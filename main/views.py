from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Q, Avg, BooleanField, Case, When
from django.db import models  # <-- INI ADALAH PERBAIKAN UNTUK NAMEERROR
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
        role = request.POST["role"]  # 'SISWA' or 'GURU'

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
        # Ini terjadi jika database masih kosong
        messages.error(
            request,
            f"Data materi belum diisi oleh Admin. Harap hubungi Guru. (Error: {e})",
        )
        return render(request, "main/siswa/dashboard_siswa.html")

    # REVISI: Definisikan seluruh alur belajar di satu tempat
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
            "nama": "Alat: Glosarium",
            "step": "glosarium",
            "url": redirect("glosarium").url,
            "prasyarat": progress.latihan_1_completed,
        },
        {
            "nama": "Modul 2: Klasifikasi",
            "step": "modul_2",
            "url": redirect("modul", urutan_id=2).url,
            "prasyarat": progress.glosarium_completed,
        },
        {
            "nama": "Latihan Soal 2",
            "step": "latihan_2",
            "url": redirect("latihan_soal", latihan_id=latihan_2_id).url,
            "prasyarat": progress.modul_2_completed,
        },
        {
            "nama": "Alat: Lab Mikroskop",
            "step": "mikroskop",
            "url": redirect("lab_mikroskop").url,
            "prasyarat": progress.latihan_2_completed,
        },
        {
            "nama": "Modul 3: 5 Kingdom",
            "step": "modul_3",
            "url": redirect("modul", urutan_id=3).url,
            "prasyarat": progress.mikroskop_completed,
        },
        {
            "nama": "Alat: Database Spesies",
            "step": "database",
            "url": redirect("database_spesies").url,
            "prasyarat": progress.modul_3_completed,
        },
        {
            "nama": "Latihan Soal 3",
            "step": "latihan_3",
            "url": redirect("latihan_soal", latihan_id=latihan_3_id).url,
            "prasyarat": progress.database_completed,
        },
        {
            "nama": "Ujian Akhir Bab",
            "step": "pengayaan",
            "url": redirect("pengayaan", pengayaan_id=pengayaan_id).url,
            "prasyarat": progress.latihan_3_completed,
        },
    ]

    # Hitung metrik untuk "Cards"
    total_steps = len(ALUR_BELAJAR)
    completed_steps = 0
    next_step = None

    # Data untuk progress bar di dashboard
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
            next_step = item  # Temukan langkah berikutnya

        alur_belajar_data.append(
            {
                "nama": item["nama"],
                "status": status,
                "url": item["url"] if status != "terkunci" else "#",
            }
        )

    # Data untuk Card "Progress"
    progress_percentage = (completed_steps / total_steps) * 100

    # Data untuk Card "Skor Terakhir"
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
        messages.success(request, f"Langkah '{step_name}' Selesai!")
    else:
        messages.error(request, "Langkah tidak valid.")

    return redirect("siswa_dashboard")


@login_required
def modul_view(request, urutan_id):
    subbab = get_object_or_404(SubBab, urutan=urutan_id)
    progress = get_object_or_404(SiswaProgress, siswa=request.user)

    is_unlocked = False
    if urutan_id == 1:  # Modul 1
        is_unlocked = True
    elif urutan_id == 2:  # Modul 2
        is_unlocked = progress.latihan_1_completed
    elif urutan_id == 3:  # Modul 3
        is_unlocked = progress.latihan_2_completed

    if not is_unlocked:
        messages.error(
            request, "Selesaikan langkah sebelumnya di sidebar terlebih dahulu!"
        )
        return redirect("siswa_dashboard")

    template_name = f"main/siswa/modul_{urutan_id}.html"
    context = {"subbab": subbab}
    return render(request, template_name, context)


@login_required
def latihan_soal_view(request, latihan_id):
    latihan = get_object_or_404(LatihanSoal, id=latihan_id)
    progress = get_object_or_404(SiswaProgress, siswa=request.user)

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

    pertanyaan = latihan.pertanyaan_set.all()
    context = {"latihan": latihan, "pertanyaan": pertanyaan}
    return render(request, "main/siswa/latihan_soal.html", context)


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
        step_name = (
            f"latihan_{latihan.subbab.urutan}_completed"  # cth: "latihan_1_completed"
        )
        if hasattr(progress, step_name):
            setattr(progress, step_name, True)
            progress.save()

        messages.success(
            request, f"Latihan {latihan.subbab.urutan} Selesai! Skor Anda: {skor:.0f}%"
        )
        return redirect("siswa_dashboard")

    return redirect("siswa_dashboard")


# --- View untuk Soal Pengayaan ---
@login_required
def pengayaan_view(request, pengayaan_id):
    pengayaan = get_object_or_404(SoalPengayaan, id=pengayaan_id)
    progress = get_object_or_404(SiswaProgress, siswa=request.user)

    if not progress.latihan_3_completed:
        messages.error(request, "Selesaikan semua latihan sub-bab terlebih dahulu!")
        return redirect("siswa_dashboard")

    pertanyaan = pengayaan.pertanyaan_set.all()
    context = {"pengayaan": pengayaan, "pertanyaan": pertanyaan}
    return render(request, "main/siswa/pengayaan.html", context)


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
            pilihan_id = request.POST.get(f"pertanyaan_{pertanyaan.id}")
            if pilihan_id:
                pilihan_dipilih = get_object_or_404(PilihanPengayaan, id=pilihan_id)
                if pilihan_dipilih.is_benar:
                    jawaban_benar += 1

        skor = (jawaban_benar / total_soal) * 100

        HasilPengayaan.objects.update_or_create(
            siswa=request.user, pengayaan=pengayaan, defaults={"skor": skor}
        )

        progress = get_object_or_404(SiswaProgress, siswa=request.user)
        progress.pengayaan_completed = True
        progress.save()

        messages.success(request, f"Ujian Akhir Bab Selesai! Skor Anda: {skor:.0f}%")
        return redirect("siswa_dashboard")

    return redirect("siswa_dashboard")


# === ALAT BANTU BELAJAR SISWA (VIEWS BARU) ===
# (Ditambahkan logika 'Tidak Bisa di-Skip')


@login_required
def glosarium_view(request):
    if request.user.profile.role != "SISWA":
        return redirect("guru_dashboard")
    progress = get_object_or_404(SiswaProgress, siswa=request.user)

    # Prasyarat: Selesai Modul 1
    if not progress.latihan_1_completed:
        messages.error(request, "Selesaikan Latihan 1 terlebih dahulu!")
        return redirect("siswa_dashboard")

    context = {"progress": progress}
    return render(request, "main/siswa/glosarium.html", context)


@login_required
def lab_mikroskop_view(request):
    if request.user.profile.role != "SISWA":
        return redirect("guru_dashboard")
    progress = get_object_or_404(SiswaProgress, siswa=request.user)

    # Prasyarat: Selesai Modul 2
    if not progress.latihan_2_completed:
        messages.error(request, "Selesaikan Latihan 2 terlebih dahulu!")
        return redirect("siswa_dashboard")

    context = {"progress": progress}
    return render(request, "main/siswa/lab_mikroskop.html", context)


@login_required
def database_spesies_view(request):
    if request.user.profile.role != "SISWA":
        return redirect("guru_dashboard")
    progress = get_object_or_404(SiswaProgress, siswa=request.user)

    # Prasyarat: Selesai Modul 3
    if not progress.modul_3_completed:
        messages.error(request, "Selesaikan Modul 3 terlebih dahulu!")
        return redirect("siswa_dashboard")

    context = {"progress": progress}
    return render(request, "main/siswa/database_spesies.html", context)


# === ALUR GURU ===
# (REVISI BESAR PADA PANTAU PROGRES)


@login_required
def guru_dashboard_view(request):
    if request.user.profile.role != "GURU":
        return redirect("siswa_dashboard")

    # === Ambil Data untuk Kartu Metrik ===

    # 1. Total Siswa
    total_siswa = User.objects.filter(profile__role="SISWA").count()
    if total_siswa == 0:
        total_siswa = 1  # Hindari pembagian dengan nol

    # 2. Progres Rata-Rata Kelas
    # Kita hitung progres berdasarkan 10 langkah di model SiswaProgress
    total_langkah = 10
    langkah_selesai_agregat = SiswaProgress.objects.filter(
        siswa__profile__role="SISWA"
    ).aggregate(
        modul_1=Count("pk", filter=Q(modul_1_completed=True)),
        latihan_1=Count("pk", filter=Q(latihan_1_completed=True)),
        glosarium=Count("pk", filter=Q(glosarium_completed=True)),
        modul_2=Count("pk", filter=Q(modul_2_completed=True)),
        latihan_2=Count("pk", filter=Q(latihan_2_completed=True)),
        mikroskop=Count("pk", filter=Q(mikroskop_completed=True)),
        modul_3=Count("pk", filter=Q(modul_3_completed=True)),
        database=Count("pk", filter=Q(database_completed=True)),
        latihan_3=Count("pk", filter=Q(latihan_3_completed=True)),
        pengayaan=Count("pk", filter=Q(pengayaan_completed=True)),
    )
    total_langkah_selesai = sum(langkah_selesai_agregat.values())
    total_langkah_seharusnya = total_siswa * total_langkah
    progres_rata_rata = (total_langkah_selesai / total_langkah_seharusnya) * 100

    # 3. Skor Rata-Rata (dari semua latihan yang sudah dikerjakan)
    skor_rata_rata_data = HasilLatihan.objects.all().aggregate(avg_skor=Avg("skor"))
    skor_rata_rata = skor_rata_rata_data["avg_skor"] or 0

    # 4. Modul Paling Sulit (Latihan dengan skor rata-rata terendah)
    modul_sulit = (
        LatihanSoal.objects.annotate(skor_rata2=Avg("hasillatihan__skor"))
        .filter(skor_rata2__isnull=False)
        .order_by("skor_rata2")
        .first()
    )  # .first() mengambil yg terendah

    # === Ambil Data untuk Bar Chart ===
    chart_data = {
        "l1_count": langkah_selesai_agregat["latihan_1"],
        "l2_count": langkah_selesai_agregat["latihan_2"],
        "l3_count": langkah_selesai_agregat["latihan_3"],
        "p_count": langkah_selesai_agregat["pengayaan"],
    }

    # === Ambil Data untuk "Soal Paling Sulit" ===
    soal_sulit = (
        Pertanyaan.objects.annotate(
            num_salah=Count("jawabansiswa", filter=Q(jawabansiswa__is_benar=False))
        )
        .filter(num_salah__gt=0)
        .order_by("-num_salah")
        .first()
    )  # -num_salah mengambil yg tertinggi

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
    if request.user.profile.role != "GURU":
        return redirect("siswa_dashboard")

    daftar_siswa = User.objects.filter(profile__role="SISWA")

    data_progres = []
    for siswa in daftar_siswa:
        progress, created = SiswaProgress.objects.get_or_create(siswa=siswa)

        skor_1 = HasilLatihan.objects.filter(
            siswa=siswa, latihan__subbab__urutan=1
        ).first()
        skor_2 = HasilLatihan.objects.filter(
            siswa=siswa, latihan__subbab__urutan=2
        ).first()
        skor_3 = HasilLatihan.objects.filter(
            siswa=siswa, latihan__subbab__urutan=3
        ).first()
        skor_p = HasilPengayaan.objects.filter(siswa=siswa).first()

        data_progres.append(
            {
                "nama": siswa.username,
                "progress": progress,
                "skor_1": skor_1.skor if skor_1 else "-",
                "skor_2": skor_2.skor if skor_2 else "-",
                "skor_3": skor_3.skor if skor_3 else "-",
                "skor_p": skor_p.skor if skor_p else "-",
            }
        )

    context = {"data_progres": data_progres}
    return render(request, "main/guru/pantau_progres.html", context)


@login_required
def analisis_hasil_view(request):
    if request.user.profile.role != "GURU":
        return redirect("siswa_dashboard")

    analisis_latihan = []
    for latihan in LatihanSoal.objects.all().order_by("subbab__urutan"):
        data_latihan = {"judul": latihan.judul, "pertanyaan": []}
        for pertanyaan in latihan.pertanyaan_set.all():
            total_menjawab = JawabanSiswa.objects.filter(pertanyaan=pertanyaan).count()
            total_salah = JawabanSiswa.objects.filter(
                pertanyaan=pertanyaan, is_benar=False
            ).count()

            persen_salah = 0
            if total_menjawab > 0:
                persen_salah = (total_salah / total_menjawab) * 100

            data_latihan["pertanyaan"].append(
                {
                    "teks": pertanyaan.teks_pertanyaan,
                    "total_menjawab": total_menjawab,
                    "total_salah": total_salah,
                    "persen_salah": round(persen_salah, 1),
                }
            )
        analisis_latihan.append(data_latihan)

    context = {"analisis_latihan": analisis_latihan}
    return render(request, "main/guru/analisis_hasil.html", context)
