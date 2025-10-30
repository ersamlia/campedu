# main/views.py

from django.shortcuts import render

# Halaman Utama (Tetap)
def index(request):
    return render(request, 'main/halamanUtama.html')

# ==========================
#  VIEW KHUSUS SISWA
# ==========================
def dashboard(request):
    # Arahkan ke folder 'siswa/'
    return render(request, 'main/siswa/dashboard.html')

def charts(request):
    # Arahkan ke folder 'siswa/'
    return render(request, 'main/siswa/materi.html')

def kuis(request):
    return render(request, 'main/siswa/kuis.html')

# --- UNTUK SUB-BAB 1 ---
def subbab1(request):
    # Sebaiknya gunakan subfolder untuk merapikan template
    return render(request, 'main/siswa/subbab1.html')

# TAMBAHKAN FUNGSI INI KEMBALI
def latihan1_subbab1(request):
    # Tambahkan 'main/' agar Django mencari di folder yang benar
    return render(request, 'main/siswa/latihan1_subbab1.html')

def latihan2_subbab1(request):
    return render(request, 'main/siswa/latihan2_subbab1.html')

# --- FUNGSI LAINNYA ---
def subbab2(request):
    return render(request, 'main/siswa/subbab2.html')

def subbab3(request):
    return render(request, 'main/siswa/subbab3.html')

def subbab4(request):
    return render(request, 'main/siswa/subbab4.html')

def subbab5(request):
    return render(request, 'main/siswa/subbab5.html')


# ==========================
#  VIEW KHUSUS GURU
# ==========================
def guru_dashboard(request):
    # Arahkan ke folder 'guru/'
    return render(request, 'main/guru/guru-dashboard.html')

def guru_kelas(request):
    # Arahkan ke folder 'guru/'
    return render(request, 'main/guru/buat_kelas.html')

def guru_progres(request):
    return render(request, 'main/guru/progres_siswa.html')

