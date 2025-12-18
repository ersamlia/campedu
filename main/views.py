from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.db.models import Avg, Max, Min
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Q, Avg, BooleanField, Case, When
from django.db import models
from .models import (
    Profile,
    SubBab,
    LatihanSoal,
    Pertanyaan,
    PilihanJawaban,
    SoalPengayaan,
    PertanyaanPengayaan,
    PilihanPengayaan,
    SiswaProgress,
    HasilLatihan,
    JawabanSiswa,
    HasilPengayaan,
)


from django.contrib import messages

# === HALAMAN UTAMA & AUTENTIKASI ===

def halaman_utama_view(request):
    return render(request, "main/halamanUtama.html")

def register_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        role = request.POST["role"]

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username sudah digunakan!")
            return redirect("register")

        user = User.objects.create_user(
            username=username, email=email, password=password
        )
        Profile.objects.create(user=user, role=role)

        if role == "SISWA":
            SiswaProgress.objects.create(siswa=user)

        login(request, user)
        if role == "SISWA":
            return redirect("siswa_dashboard")
        else:
            return redirect("guru_dashboard")

    return render(request, "main/register.html")

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            profile = Profile.objects.get(user=user)
            if profile.role == "SISWA":
                return redirect("siswa_dashboard")
            else:
                return redirect("guru_dashboard")
        else:
            messages.error(request, "Username atau password salah!")
            return redirect("login")

    return render(request, "main/login.html")

def logout_view(request):
    logout(request)
    return redirect("halaman_utama")

def forgot_password_view(request):
    return render(request, "main/forgot-password.html")




# === ALUR SISWA ===

@login_required
def siswa_dashboard_view(request):
    if request.user.profile.role != "SISWA":
        return redirect("guru_dashboard")

    # Dapatkan progres siswa
    progress, created = SiswaProgress.objects.get_or_create(siswa=request.user)

    # Ambil ID untuk URL
    try:
        latihan_1_id = LatihanSoal.objects.get(subbab__urutan=1).id
        latihan_2_id = LatihanSoal.objects.get(subbab__urutan=2).id
        latihan_3_id = LatihanSoal.objects.get(subbab__urutan=3).id
        pengayaan_id = SoalPengayaan.objects.first().id
    except Exception as e:
        messages.error(
            request,
            f"Data materi belum diisi oleh Admin. Harap hubungi Guru. (Error: {e})",
        )
        return render(request, "main/siswa/dashboard_siswa.html", {"next_step": None})

    # REVISI: Alur Belajar Tanpa Alat Bantu
    ALUR_BELAJAR = [
        {
            "nama": "Modul 1: Karakteristik",
            "step": "modul_1",
            "url": redirect("modul", urutan_id=1).url,
            "prasyarat": True,
        },
        {
            "nama": "Latihan Soal 1",
            "step": "latihan_1",
            "url": redirect("latihan_soal", latihan_id=latihan_1_id).url,
            "prasyarat": progress.modul_1_completed,
        },
        {
            "nama": "Modul 2: Klasifikasi",
            "step": "modul_2",
            "url": redirect("modul", urutan_id=2).url,
            "prasyarat": progress.latihan_1_completed, # Syarat: Latihan 1 Selesai
        },
        {
            "nama": "Latihan Soal 2",
            "step": "latihan_2",
            "url": redirect("latihan_soal", latihan_id=latihan_2_id).url,
            "prasyarat": progress.modul_2_completed,
        },
        {
            "nama": "Modul 3: 5 Kingdom",
            "step": "modul_3",
            "url": redirect("modul", urutan_id=3).url,
            "prasyarat": progress.latihan_2_completed, # Syarat: Latihan 2 Selesai
        },
        {
            "nama": "Latihan Soal 3",
            "step": "latihan_3",
            "url": redirect("latihan_soal", latihan_id=latihan_3_id).url,
            "prasyarat": progress.modul_3_completed,
        },
        {
            "nama": "Ujian Akhir Bab",
            "step": "pengayaan",
            "url": redirect("pengayaan", pengayaan_id=pengayaan_id).url,
            "prasyarat": progress.latihan_3_completed,
        },
    ]

    total_steps = len(ALUR_BELAJAR)
    completed_steps = 0
    next_step = None
    alur_belajar_data = []

    for item in ALUR_BELAJAR:
        is_completed = getattr(progress, f"{item['step']}_completed", False)
        is_unlocked = item["prasyarat"]

        status = "terkunci"
        if is_completed:
            completed_steps += 1
            status = "selesai"
        elif is_unlocked and not next_step:
            status = "aktif"
            next_step = item

        alur_belajar_data.append(
            {
                "nama": item["nama"],
                "status": status,
                "url": item["url"] if status != "terkunci" else "#",
            }
        )

    progress_percentage = 0
    if total_steps > 0:
        progress_percentage = (completed_steps / total_steps) * 100

    skor_terakhir = "-"
    hasil_latihan_terakhir = (
        HasilLatihan.objects.filter(siswa=request.user).order_by("-id").first()
    )
    if hasil_latihan_terakhir:
        skor_terakhir = f"{hasil_latihan_terakhir.skor:.0f}%"

    context = {
        "progress": progress,
        "total_steps": total_steps,
        "completed_steps": completed_steps,
        "progress_percentage": int(progress_percentage),
        "skor_terakhir": skor_terakhir,
        "next_step": next_step,
        "alur_belajar_data": alur_belajar_data,
    }

    return render(request, "main/siswa/dashboard_siswa.html", context)


@login_required
def selesai_step_view(request, step_name):
    progress = get_object_or_404(SiswaProgress, siswa=request.user)

    valid_steps = [
        f.name
        for f in SiswaProgress._meta.get_fields()
        if isinstance(f, models.BooleanField)
    ]
    step_field_name = f"{step_name}_completed"

    if step_field_name in valid_steps:
        setattr(progress, step_field_name, True)
        progress.save()
    else:
        messages.error(request, "Langkah tidak valid.")
        return redirect("siswa_dashboard")

    # --- LOGIKA REDIRECT (ALUR BARU) ---
    try:
        latihan_1_id = LatihanSoal.objects.get(subbab__urutan=1).id
        latihan_2_id = LatihanSoal.objects.get(subbab__urutan=2).id
        latihan_3_id = LatihanSoal.objects.get(subbab__urutan=3).id
        pengayaan_id = SoalPengayaan.objects.first().id
    except Exception as e:
        messages.error(request, f"Data materi belum diisi Admin: {e}")
        return redirect("siswa_dashboard")

    if step_name == "modul_1":
        return redirect("latihan_soal", latihan_id=latihan_1_id)
    elif step_name == "latihan_1":
        # Langsung ke Modul 2 (Glosarium dihapus)
        return redirect("modul", urutan_id=2) 
    elif step_name == "modul_2":
        return redirect("latihan_soal", latihan_id=latihan_2_id)
    elif step_name == "latihan_2":
        # Langsung ke Modul 3 (Mikroskop dihapus)
        return redirect("modul", urutan_id=3) 
    elif step_name == "modul_3":
        # Langsung ke Latihan 3 (Database dihapus)
        return redirect("latihan_soal", latihan_id=latihan_3_id)
    elif step_name == "latihan_3":
        return redirect("pengayaan", pengayaan_id=pengayaan_id)
    elif step_name == "pengayaan":
        messages.success(request, "Selamat! Anda telah menyelesaikan seluruh bab!")
        return redirect("siswa_dashboard")

    return redirect("siswa_dashboard")


@login_required
def modul_view(request, urutan_id):
    subbab = get_object_or_404(SubBab, urutan=urutan_id)
    progress = get_object_or_404(SiswaProgress, siswa=request.user)

    # REVISI SYARAT PEMBUKA MODUL
    is_unlocked = False
    if urutan_id == 1:
        is_unlocked = True
    elif urutan_id == 2:
        # Syarat Modul 2: Latihan 1 Selesai
        is_unlocked = progress.latihan_1_completed 
    elif urutan_id == 3:
        # Syarat Modul 3: Latihan 2 Selesai
        is_unlocked = progress.latihan_2_completed 

    if not is_unlocked:
        messages.error(
            request, "Selesaikan langkah sebelumnya di alur belajar terlebih dahulu!"
        )
        return redirect("siswa_dashboard")

    template_name = f"main/siswa/modul_{urutan_id}.html"
    context = {"subbab": subbab}
    return render(request, template_name, context)


@login_required
def latihan_soal_view(request, latihan_id):
    latihan = get_object_or_404(LatihanSoal, id=latihan_id)
    progress = get_object_or_404(SiswaProgress, siswa=request.user)

    # --- Logika Prasyarat (Lock) ---
    is_unlocked = False
    if latihan.subbab.urutan == 1:
        is_unlocked = progress.modul_1_completed
    elif latihan.subbab.urutan == 2:
        is_unlocked = progress.modul_2_completed
    elif latihan.subbab.urutan == 3:
        is_unlocked = progress.modul_3_completed 

    if not is_unlocked:
        messages.error(
            request, "Selesaikan modul interaktif sebelumnya terlebih dahulu!"
        )
        return redirect("siswa_dashboard")

    if request.GET.get("mulai") == "true":
        pertanyaan = latihan.pertanyaan_set.all()
        context = {"latihan": latihan, "pertanyaan": pertanyaan}
        return render(request, "main/siswa/latihan_soal.html", context)
    else:
        context = {"latihan": latihan}
        return render(request, "main/siswa/latihan_petunjuk.html", context)


@login_required
def submit_latihan_view(request, latihan_id):
    if request.method == "POST":
        latihan = get_object_or_404(LatihanSoal, id=latihan_id)
        pertanyaan_list = latihan.pertanyaan_set.all()
        total_soal = pertanyaan_list.count()

        if total_soal == 0:
            messages.error(request, "Latihan ini tidak memiliki pertanyaan.")
            return redirect("siswa_dashboard")

        jawaban_benar = 0
        JawabanSiswa.objects.filter(
            siswa=request.user, pertanyaan__latihan=latihan
        ).delete()

        for pertanyaan in pertanyaan_list:
            pilihan_id = request.POST.get(f"pertanyaan_{pertanyaan.id}")
            if pilihan_id:
                pilihan_dipilih = get_object_or_404(PilihanJawaban, id=pilihan_id)
                is_benar = pilihan_dipilih.is_benar
                if is_benar:
                    jawaban_benar += 1

                JawabanSiswa.objects.create(
                    siswa=request.user,
                    pertanyaan=pertanyaan,
                    pilihan_dipilih=pilihan_dipilih,
                    is_benar=is_benar,
                )

        skor = (jawaban_benar / total_soal) * 100

        HasilLatihan.objects.update_or_create(
            siswa=request.user, latihan=latihan, defaults={"skor": skor}
        )

        progress = get_object_or_404(SiswaProgress, siswa=request.user)
        step_name = f"latihan_{latihan.subbab.urutan}_completed"
        if hasattr(progress, step_name):
            setattr(progress, step_name, True)
            progress.save()

        return redirect("hasil_latihan", latihan_id=latihan.id)

    return redirect("siswa_dashboard")


@login_required
def hasil_latihan_view(request, latihan_id):
    latihan = get_object_or_404(LatihanSoal, id=latihan_id)
    hasil = get_object_or_404(HasilLatihan, siswa=request.user, latihan=latihan)
    jawaban_siswa = JawabanSiswa.objects.filter(
        siswa=request.user, pertanyaan__latihan=latihan
    ).select_related("pertanyaan", "pilihan_dipilih")

    total_soal = jawaban_siswa.count()
    jawaban_benar = jawaban_siswa.filter(is_benar=True).count()
    jawaban_salah = total_soal - jawaban_benar

    context = {
        "latihan": latihan, 
        "hasil": hasil, 
        "jawaban_siswa": jawaban_siswa,
        "jawaban_benar": jawaban_benar,
        "jawaban_salah": jawaban_salah
    }
    return render(request, "main/siswa/hasil_latihan.html", context)


@login_required
def pengayaan_view(request, pengayaan_id):
    pengayaan = get_object_or_404(SoalPengayaan, id=pengayaan_id)
    progress = get_object_or_404(SiswaProgress, siswa=request.user)
    
    if not progress.latihan_3_completed:
        messages.error(request, "Selesaikan semua latihan sub-bab terlebih dahulu!")
        return redirect("siswa_dashboard")

    if request.GET.get("mulai") == "true":
        pertanyaan = pengayaan.pertanyaan_set.all()
        context = {"pengayaan": pengayaan, "pertanyaan": pertanyaan}
        return render(request, "main/siswa/pengayaan.html", context)
    else:
        context = {"pengayaan": pengayaan}
        return render(request, "main/siswa/pengayaan_petunjuk.html", context)

@login_required
def submit_pengayaan_view(request, pengayaan_id):
    if request.method == "POST":
        pengayaan = get_object_or_404(SoalPengayaan, id=pengayaan_id)
        pertanyaan_list = pengayaan.pertanyaan_set.all()
        total_soal = pertanyaan_list.count()

        if total_soal == 0:
            return redirect("siswa_dashboard")

        jawaban_benar = 0
        for pertanyaan in pertanyaan_list:
            jawaban_user = request.POST.get(f"pertanyaan_{pertanyaan.id}")
            if not jawaban_user: continue

            if pertanyaan.tipe == "PG":
                try:
                    pilihan_dipilih = PilihanPengayaan.objects.get(id=jawaban_user)
                    if pilihan_dipilih.is_benar: jawaban_benar += 1
                except PilihanPengayaan.DoesNotExist: pass

            elif pertanyaan.tipe == "ISIAN":
                kunci = pertanyaan.kunci_jawaban_isian.strip().lower() if pertanyaan.kunci_jawaban_isian else ""
                jawaban_siswa = jawaban_user.strip().lower()
                if jawaban_siswa == kunci: jawaban_benar += 1

        skor = (jawaban_benar / total_soal) * 100
        HasilPengayaan.objects.update_or_create(
            siswa=request.user, pengayaan=pengayaan, defaults={"skor": skor}
        )

        progress = get_object_or_404(SiswaProgress, siswa=request.user)
        progress.pengayaan_completed = True
        progress.save()

        return redirect("hasil_pengayaan", pengayaan_id=pengayaan.id)

    return redirect("siswa_dashboard")


@login_required
def hasil_pengayaan_view(request, pengayaan_id):
    pengayaan = get_object_or_404(SoalPengayaan, id=pengayaan_id)
    hasil = get_object_or_404(HasilPengayaan, siswa=request.user, pengayaan=pengayaan)
    pertanyaan_list = pengayaan.pertanyaan_set.all()
    
    total_soal = pertanyaan_list.count()
    if total_soal > 0:
        jawaban_benar = round((hasil.skor * total_soal) / 100)
        jawaban_salah = total_soal - jawaban_benar
    else:
        jawaban_benar = 0
        jawaban_salah = 0
        
    context = {
        "pengayaan": pengayaan, "hasil": hasil, "pertanyaan_list": pertanyaan_list,
        "jawaban_benar": int(jawaban_benar), "jawaban_salah": int(jawaban_salah), "total_soal": total_soal
    }
    return render(request, "main/siswa/hasil_pengayaan.html", context)


# === ALUR GURU ===

@login_required
def guru_dashboard_view(request):
    if request.user.profile.role != "GURU":
        return redirect("siswa_dashboard")

    total_siswa = User.objects.filter(profile__role="SISWA").count()
    if total_siswa == 0: total_siswa = 1

    # REVISI: Total langkah sekarang hanya 7 (Tanpa Glosarium, Mikroskop, Database)
    total_langkah = 7
    langkah_selesai_agregat = SiswaProgress.objects.filter(
        siswa__profile__role="SISWA"
    ).aggregate(
        modul_1=Count("pk", filter=Q(modul_1_completed=True)),
        latihan_1=Count("pk", filter=Q(latihan_1_completed=True)),
        # glosarium REMOVED
        modul_2=Count("pk", filter=Q(modul_2_completed=True)),
        latihan_2=Count("pk", filter=Q(latihan_2_completed=True)),
        # mikroskop REMOVED
        modul_3=Count("pk", filter=Q(modul_3_completed=True)),
        # database REMOVED
        latihan_3=Count("pk", filter=Q(latihan_3_completed=True)),
        pengayaan=Count("pk", filter=Q(pengayaan_completed=True)),
    )
    total_langkah_selesai = sum(langkah_selesai_agregat.values())
    total_langkah_seharusnya = total_siswa * total_langkah
    progres_rata_rata = (total_langkah_selesai / total_langkah_seharusnya) * 100

    skor_rata_rata_data = HasilLatihan.objects.all().aggregate(avg_skor=Avg("skor"))
    skor_rata_rata = skor_rata_rata_data["avg_skor"] or 0

    modul_sulit = (
        LatihanSoal.objects.annotate(skor_rata2=Avg("hasillatihan__skor"))
        .filter(skor_rata2__isnull=False).order_by("skor_rata2").first()
    )

    chart_data = {
        "l1_count": langkah_selesai_agregat["latihan_1"],
        "l2_count": langkah_selesai_agregat["latihan_2"],
        "l3_count": langkah_selesai_agregat["latihan_3"],
        "p_count": langkah_selesai_agregat["pengayaan"],
    }

    soal_sulit = (
        Pertanyaan.objects.annotate(
            num_salah=Count("jawabansiswa", filter=Q(jawabansiswa__is_benar=False))
        ).filter(num_salah__gt=0).order_by("-num_salah").first()
    )

    context = {
        "total_siswa": total_siswa,
        "progres_rata_rata": int(progres_rata_rata),
        "skor_rata_rata": round(skor_rata_rata, 1),
        "modul_sulit": modul_sulit,
        "chart_data": chart_data,
        "soal_sulit": soal_sulit,
    }
    return render(request, "main/guru/dashboard_guru.html", context)

@login_required
def pantau_progres_view(request):
    if request.user.profile.role != "GURU": return redirect("siswa_dashboard")
    daftar_siswa = User.objects.filter(profile__role="SISWA")
    data_progres = []
    for siswa in daftar_siswa:
        progress, created = SiswaProgress.objects.get_or_create(siswa=siswa)
        skor_1 = HasilLatihan.objects.filter(siswa=siswa, latihan__subbab__urutan=1).first()
        skor_2 = HasilLatihan.objects.filter(siswa=siswa, latihan__subbab__urutan=2).first()
        skor_3 = HasilLatihan.objects.filter(siswa=siswa, latihan__subbab__urutan=3).first()
        skor_p = HasilPengayaan.objects.filter(siswa=siswa).first()
        data_progres.append({
            "nama": siswa.username, "progress": progress,
            "skor_1": skor_1.skor if skor_1 else "-", "skor_2": skor_2.skor if skor_2 else "-",
            "skor_3": skor_3.skor if skor_3 else "-", "skor_p": skor_p.skor if skor_p else "-",
        })
    context = {"data_progres": data_progres}
    return render(request, "main/guru/pantau_progres.html", context)

@login_required
def analisis_hasil_view(request):
    # Cek apakah user adalah GURU
    if request.user.profile.role != "GURU":
        return redirect("siswa_dashboard")

    analisis_gabungan = []

    # ==========================================
    # 1. DATA LATIHAN HARIAN (Tabel LatihanSoal)
    # ==========================================
    semua_latihan = LatihanSoal.objects.all().order_by('id')
    
    for lat in semua_latihan:
        kategori = 'LATIHAN'
        
        hasil_siswa = HasilLatihan.objects.filter(latihan=lat)
        agregat = hasil_siswa.aggregate(Avg('skor'), Max('skor'), Min('skor'))
        
        daftar_nilai = []
        jumlah_lulus = 0
        
        for h in hasil_siswa:
            skor_siswa = h.skor if h.skor is not None else 0
            if skor_siswa >= 70: 
                jumlah_lulus += 1
            
            # Ambil nama & NIS aman
            nama = h.siswa.get_full_name() or h.siswa.username
            try:
                nis = h.siswa.profile.nis
            except:
                nis = "-"

            # --- SAFE DATE HANDLING ---
            # Mencoba mencari 'tanggal_dibuat', kalau tidak ada cari 'tanggal', kalau tidak ada tampilkan '-'
            tgl = getattr(h, 'tanggal_dibuat', getattr(h, 'tanggal', '-'))

            daftar_nilai.append({
                'nama': nama, 
                'nis': nis,
                'tanggal_submit': tgl, # Gunakan variabel aman ini
                'nilai': skor_siswa
            })

        analisis_gabungan.append({
            'judul': lat.judul,
            'kategori': kategori,
            'rata_rata': agregat['skor__avg'] or 0,
            'nilai_tertinggi': agregat['skor__max'] or 0,
            'nilai_terendah': agregat['skor__min'] or 0,
            'jumlah_lulus': jumlah_lulus,
            'daftar_nilai': daftar_nilai,
        })

    # ==========================================
    # 2. DATA UJIAN / PENGAYAAN (Tabel SoalPengayaan)
    # ==========================================
    semua_pengayaan = SoalPengayaan.objects.all().order_by('id')
    
    for peng in semua_pengayaan:
        kategori = 'PENGAYAAN'
        
        hasil_siswa = HasilPengayaan.objects.filter(pengayaan=peng)
        agregat = hasil_siswa.aggregate(Avg('skor'), Max('skor'), Min('skor'))
        
        daftar_nilai = []
        jumlah_lulus = 0
        
        for h in hasil_siswa:
            skor_siswa = h.skor if h.skor is not None else 0
            if skor_siswa >= 70: 
                jumlah_lulus += 1
                
            nama = h.siswa.get_full_name() or h.siswa.username
            try:
                nis = h.siswa.profile.nis
            except:
                nis = "-"

            # --- SAFE DATE HANDLING ---
            tgl = getattr(h, 'tanggal_dibuat', getattr(h, 'tanggal', '-'))

            daftar_nilai.append({
                'nama': nama, 
                'nis': nis,
                'tanggal_submit': tgl, # Gunakan variabel aman ini
                'nilai': skor_siswa
            })

        analisis_gabungan.append({
            'judul': peng.judul,
            'kategori': kategori,
            'rata_rata': agregat['skor__avg'] or 0,
            'nilai_tertinggi': agregat['skor__max'] or 0,
            'nilai_terendah': agregat['skor__min'] or 0,
            'jumlah_lulus': jumlah_lulus,
            'daftar_nilai': daftar_nilai,
        })

    context = {
        'analisis_latihan': analisis_gabungan
    }
    return render(request, 'main/guru/analisis_hasil.html', context)

@login_required
def download_progres_pdf(request):
    if request.user.profile.role != "GURU":
        return redirect("siswa_dashboard")
    
    # 1. Ambil Data (Sama persis dengan pantau_progres_view)
    daftar_siswa = User.objects.filter(profile__role="SISWA").order_by('username')
    data_progres = []
    
    for siswa in daftar_siswa:
        progress, created = SiswaProgress.objects.get_or_create(siswa=siswa)
        skor_1 = HasilLatihan.objects.filter(siswa=siswa, latihan__subbab__urutan=1).first()
        skor_2 = HasilLatihan.objects.filter(siswa=siswa, latihan__subbab__urutan=2).first()
        skor_3 = HasilLatihan.objects.filter(siswa=siswa, latihan__subbab__urutan=3).first()
        skor_p = HasilPengayaan.objects.filter(siswa=siswa).first()
        
        data_progres.append({
            "nama": siswa.username, # Atau siswa.get_full_name()
            "progress": progress,
            "skor_1": skor_1.skor if skor_1 else "-",
            "skor_2": skor_2.skor if skor_2 else "-",
            "skor_3": skor_3.skor if skor_3 else "-",
            "skor_p": skor_p.skor if skor_p else "-",
        })

    context = {"data_progres": data_progres}

    # 2. Render Template PDF
    template_path = 'main/guru/pdf_progres.html' # Kita akan buat file ini di langkah 3
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="rekap_nilai_siswa.pdf"'
    
    template = get_template(template_path)
    html = template.render(context)

    # 3. Create PDF
    pisa_status = pisa.CreatePDF(
       html, dest=response
    )

    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response

@login_required
def download_analisis_pdf(request):
    if request.user.profile.role != "GURU":
        return redirect("siswa_dashboard")

    analisis_gabungan = []

    # 1. DATA LATIHAN HARIAN
    semua_latihan = LatihanSoal.objects.all().order_by('id')
    for lat in semua_latihan:
        kategori = 'LATIHAN'
        hasil_siswa = HasilLatihan.objects.filter(latihan=lat)
        agregat = hasil_siswa.aggregate(Avg('skor'), Max('skor'), Min('skor'))
        
        daftar_nilai = []
        jumlah_lulus = 0
        for h in hasil_siswa:
            skor_siswa = h.skor if h.skor is not None else 0
            if skor_siswa >= 70: jumlah_lulus += 1
            
            nama = h.siswa.get_full_name() or h.siswa.username
            try: nis = h.siswa.profile.nis
            except: nis = "-"
            tgl = getattr(h, 'tanggal_dibuat', getattr(h, 'tanggal', '-'))

            daftar_nilai.append({
                'nama': nama, 'nis': nis, 'tanggal_submit': tgl, 'nilai': skor_siswa
            })

        analisis_gabungan.append({
            'judul': lat.judul,
            'kategori': kategori,
            'rata_rata': agregat['skor__avg'] or 0,
            'nilai_tertinggi': agregat['skor__max'] or 0,
            'nilai_terendah': agregat['skor__min'] or 0,
            'jumlah_lulus': jumlah_lulus,
            'daftar_nilai': daftar_nilai,
        })

    # 2. DATA PENGAYAAN / UJIAN
    semua_pengayaan = SoalPengayaan.objects.all().order_by('id')
    for peng in semua_pengayaan:
        kategori = 'PENGAYAAN'
        hasil_siswa = HasilPengayaan.objects.filter(pengayaan=peng)
        agregat = hasil_siswa.aggregate(Avg('skor'), Max('skor'), Min('skor'))
        
        daftar_nilai = []
        jumlah_lulus = 0
        for h in hasil_siswa:
            skor_siswa = h.skor if h.skor is not None else 0
            if skor_siswa >= 70: jumlah_lulus += 1
                
            nama = h.siswa.get_full_name() or h.siswa.username
            try: nis = h.siswa.profile.nis
            except: nis = "-"
            tgl = getattr(h, 'tanggal_dibuat', getattr(h, 'tanggal', '-'))

            daftar_nilai.append({
                'nama': nama, 'nis': nis, 'tanggal_submit': tgl, 'nilai': skor_siswa
            })

        analisis_gabungan.append({
            'judul': peng.judul,
            'kategori': kategori,
            'rata_rata': agregat['skor__avg'] or 0,
            'nilai_tertinggi': agregat['skor__max'] or 0,
            'nilai_terendah': agregat['skor__min'] or 0,
            'jumlah_lulus': jumlah_lulus,
            'daftar_nilai': daftar_nilai,
        })

    context = {'analisis_latihan': analisis_gabungan}
    
    # RENDER KE PDF
    template_path = 'main/guru/pdf_analisis.html' # Kita buat file ini di langkah 3
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="laporan_analisis_hasil.pdf"'
    
    template = get_template(template_path)
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response