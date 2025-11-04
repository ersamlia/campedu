from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Q, Avg
from .models import (
    Profile, SubBab, LatihanSoal, Pertanyaan, PilihanJawaban,
    SoalPengayaan, PertanyaanPengayaan, PilihanPengayaan,
    ProgressSiswa, HasilLatihan, JawabanSiswa, HasilPengayaan
)
from django.contrib import messages

# === HALAMAN UTAMA & AUTENTIKASI ===

def halaman_utama_view(request):
    # 'halamanUtama.html' dari struktur file Anda
    return render(request, 'main/halamanUtama.html')

def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        role = request.POST['role'] # 'SISWA' or 'GURU'

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username sudah digunakan!')
            return redirect('register')

        user = User.objects.create_user(username=username, email=email, password=password)
        Profile.objects.create(user=user, role=role)
        
        login(request, user)
        if role == 'SISWA':
            return redirect('siswa_dashboard')
        else:
            return redirect('guru_dashboard')
            
    # 'register.html' dari struktur file Anda
    return render(request, 'main/register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            profile = Profile.objects.get(user=user)
            if profile.role == 'SISWA':
                return redirect('siswa_dashboard')
            else:
                return redirect('guru_dashboard')
        else:
            messages.error(request, 'Username atau password salah!')
            return redirect('login')
            
    # 'login.html' dari struktur file Anda
    return render(request, 'main/login.html')

def logout_view(request):
    logout(request)
    return redirect('halaman_utama')

def forgot_password_view(request):
    # Logika untuk lupa password bisa ditambahkan nanti
    # 'forgot-password.html' dari struktur file Anda
    return render(request, 'main/forgot-password.html')


# === ALUR SISWA ===

@login_required
def siswa_dashboard_view(request):
    if request.user.profile.role != 'SISWA':
        return redirect('guru_dashboard') # Keamanan jika guru akses

    subbabs = SubBab.objects.all().order_by('urutan')
    progress_siswa = ProgressSiswa.objects.filter(siswa=request.user)
    
    # Buat dictionary untuk status progres
    progress_status = {prog.subbab.id: prog for prog in progress_siswa}
    
    # Logika untuk membuka kunci
    status_bab = []
    unlocked = True # Bab pertama selalu terbuka
    for bab in subbabs:
        prog = progress_status.get(bab.id)
        status = {
            'subbab': bab,
            'unlocked': unlocked,
            'modul_completed': prog.modul_completed if prog else False,
            'latihan_completed': prog.latihan_completed if prog else False,
        }
        status_bab.append(status)
        
        # Kunci untuk bab berikutnya: modul DAN latihan harus selesai
        if not (status['modul_completed'] and status['latihan_completed']):
            unlocked = False 
            
    # Cek apakah semua latihan selesai untuk membuka pengayaan
    semua_latihan_selesai = all(s['latihan_completed'] for s in status_bab)
    try:
        pengayaan = SoalPengayaan.objects.first() # Asumsi hanya ada 1
        pengayaan_selesai = HasilPengayaan.objects.filter(siswa=request.user, pengayaan=pengayaan).exists()
    except:
        pengayaan = None
        pengayaan_selesai = False

    context = {
        'status_bab': status_bab,
        'pengayaan': pengayaan,
        'semua_latihan_selesai': semua_latihan_selesai,
        'pengayaan_selesai': pengayaan_selesai
    }
    return render(request, 'main/siswa/dashboard_siswa.html', context)

@login_required
def modul_view(request, urutan_id):
    subbab = get_object_or_404(SubBab, urutan=urutan_id)
    template_name = f'main/siswa/modul_{urutan_id}.html'
    
    # Buat progress jika belum ada
    ProgressSiswa.objects.get_or_create(siswa=request.user, subbab=subbab)
    
    context = {'subbab': subbab}
    return render(request, template_name, context)

@login_required
def modul_selesai_view(request, subbab_id):
    # Ini adalah view 'dummy' yang dipanggil saat siswa menekan tombol 'Selesai Modul'
    subbab = get_object_or_404(SubBab, id=subbab_id)
    progress = get_object_or_404(ProgressSiswa, siswa=request.user, subbab=subbab)
    progress.modul_completed = True
    progress.save()
    return redirect('siswa_dashboard')


@login_required
def latihan_soal_view(request, latihan_id):
    latihan = get_object_or_404(LatihanSoal, id=latihan_id)
    # Cek apakah modul sebelumnya sudah selesai
    progress = ProgressSiswa.objects.get(siswa=request.user, subbab=latihan.subbab)
    if not progress.modul_completed:
        messages.error(request, 'Harap selesaikan modul interaktif terlebih dahulu!')
        return redirect('siswa_dashboard')
        
    pertanyaan = latihan.pertanyaan_set.all()
    context = {'latihan': latihan, 'pertanyaan': pertanyaan}
    return render(request, 'main/siswa/latihan_soal.html', context)

@login_required
def submit_latihan_view(request, latihan_id):
    if request.method == 'POST':
        latihan = get_object_or_404(LatihanSoal, id=latihan_id)
        pertanyaan_list = latihan.pertanyaan_set.all()
        
        total_soal = pertanyaan_list.count()
        jawaban_benar = 0
        
        # Hapus jawaban lama (jika ada)
        JawabanSiswa.objects.filter(siswa=request.user, pertanyaan__latihan=latihan).delete()

        for pertanyaan in pertanyaan_list:
            pilihan_id = request.POST.get(f'pertanyaan_{pertanyaan.id}')
            if pilihan_id:
                pilihan_dipilih = get_object_or_404(PilihanJawaban, id=pilihan_id)
                
                is_benar = pilihan_dipilih.is_benar
                if is_benar:
                    jawaban_benar += 1
                
                # Simpan jawaban siswa untuk analisis guru
                JawabanSiswa.objects.create(
                    siswa=request.user,
                    pertanyaan=pertanyaan,
                    pilihan_dipilih=pilihan_dipilih,
                    is_benar=is_benar
                )
        
        skor = (jawaban_benar / total_soal) * 100
        
        # Simpan hasil skor
        HasilLatihan.objects.update_or_create(
            siswa=request.user, latihan=latihan,
            defaults={'skor': skor}
        )
        
        # Update progress
        progress = get_object_or_404(ProgressSiswa, siswa=request.user, subbab=latihan.subbab)
        progress.latihan_completed = True
        progress.save()
        
        return redirect('hasil_latihan', latihan_id=latihan.id)
    return redirect('siswa_dashboard')

@login_required
def hasil_latihan_view(request, latihan_id):
    latihan = get_object_or_404(LatihanSoal, id=latihan_id)
    hasil = get_object_or_404(HasilLatihan, siswa=request.user, latihan=latihan)
    context = {'latihan': latihan, 'hasil': hasil}
    return render(request, 'main/siswa/hasil_latihan.html', context)

# --- View untuk Soal Pengayaan ---
@login_required
def pengayaan_view(request, pengayaan_id):
    pengayaan = get_object_or_404(SoalPengayaan, id=pengayaan_id)
    pertanyaan = pengayaan.pertanyaan_set.all()
    context = {'pengayaan': pengayaan, 'pertanyaan': pertanyaan}
    return render(request, 'main/siswa/pengayaan.html', context)

@login_required
def submit_pengayaan_view(request, pengayaan_id):
    if request.method == 'POST':
        pengayaan = get_object_or_404(SoalPengayaan, id=pengayaan_id)
        pertanyaan_list = pengayaan.pertanyaan_set.all()
        
        total_soal = pertanyaan_list.count()
        jawaban_benar = 0
        
        for pertanyaan in pertanyaan_list:
            pilihan_id = request.POST.get(f'pertanyaan_{pertanyaan.id}')
            if pilihan_id:
                pilihan_dipilih = get_object_or_404(PilihanPengayaan, id=pilihan_id)
                if pilihan_dipilih.is_benar:
                    jawaban_benar += 1
        
        skor = (jawaban_benar / total_soal) * 100
        
        HasilPengayaan.objects.update_or_create(
            siswa=request.user, pengayaan=pengayaan,
            defaults={'skor': skor}
        )
        return redirect('hasil_pengayaan', pengayaan_id=pengayaan.id)
    return redirect('siswa_dashboard')

@login_required
def hasil_pengayaan_view(request, pengayaan_id):
    pengayaan = get_object_or_404(SoalPengayaan, id=pengayaan_id)
    hasil = get_object_or_404(HasilPengayaan, siswa=request.user, pengayaan=pengayaan)
    context = {'pengayaan': pengayaan, 'hasil': hasil}
    return render(request, 'main/siswa/hasil_pengayaan.html', context)


# === ALUR GURU ===

@login_required
def guru_dashboard_view(request):
    if request.user.profile.role != 'GURU':
        return redirect('siswa_dashboard') # Keamanan
    return render(request, 'main/guru/dashboard_guru.html')

@login_required
def pantau_progres_view(request):
    if request.user.profile.role != 'GURU':
        return redirect('siswa_dashboard')

    daftar_siswa = User.objects.filter(profile__role='SISWA')
    subbabs = SubBab.objects.all().order_by('urutan')
    
    # Siapkan data untuk tabel
    data_progres = []
    for siswa in daftar_siswa:
        progres_siswa = {
            'nama': siswa.username,
            'bab': []
        }
        for bab in subbabs:
            # Dapatkan progres modul
            prog = ProgressSiswa.objects.filter(siswa=siswa, subbab=bab).first()
            # Dapatkan hasil latihan
            hasil = HasilLatihan.objects.filter(siswa=siswa, latihan__subbab=bab).first()
            
            progres_siswa['bab'].append({
                'modul_selesai': prog.modul_completed if prog else False,
                'latihan_selesai': prog.latihan_completed if prog else False,
                'skor': hasil.skor if hasil else '-'
            })
        
        # Tambahkan data pengayaan
        pengayaan = SoalPengayaan.objects.first()
        hasil_pengayaan = HasilPengayaan.objects.filter(siswa=siswa, pengayaan=pengayaan).first()
        progres_siswa['pengayaan'] = {
            'selesai': True if hasil_pengayaan else False,
            'skor': hasil_pengayaan.skor if hasil_pengayaan else '-'
        }
        
        data_progres.append(progres_siswa)

    context = {
        'subbabs': subbabs,
        'data_progres': data_progres
    }
    return render(request, 'main/guru/pantau_progres.html', context)

@login_required
def analisis_hasil_view(request):
    if request.user.profile.role != 'GURU':
        return redirect('siswa_dashboard')

    # Ini adalah logika "wow" untuk dosen Anda
    # Menganalisis semua pertanyaan di semua latihan soal
    
    analisis_latihan = []
    for latihan in LatihanSoal.objects.all().order_by('subbab__urutan'):
        data_latihan = {
            'judul': latihan.judul,
            'pertanyaan': []
        }
        for pertanyaan in latihan.pertanyaan_set.all():
            total_menjawab = JawabanSiswa.objects.filter(pertanyaan=pertanyaan).count()
            total_salah = JawabanSiswa.objects.filter(pertanyaan=pertanyaan, is_benar=False).count()
            
            persen_salah = 0
            if total_menjawab > 0:
                persen_salah = (total_salah / total_menjawab) * 100
            
            data_latihan['pertanyaan'].append({
                'teks': pertanyaan.teks_pertanyaan,
                'total_menjawab': total_menjawab,
                'total_salah': total_salah,
                'persen_salah': round(persen_salah, 1)
            })
        analisis_latihan.append(data_latihan)
        
    context = {
        'analisis_latihan': analisis_latihan
    }
    return render(request, 'main/guru/analisis_hasil.html', context)