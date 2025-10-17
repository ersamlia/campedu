# main/views.py

from django.shortcuts import render

def dashboard(request):
    return render(request, 'dashboard.html')

def charts(request):
    return render(request, 'materi.html')

def kuis(request):
    return render(request, 'kuis.html')

# --- UNTUK SUB-BAB 1 ---
def subbab1(request):
    # Sebaiknya gunakan subfolder untuk merapikan template
    return render(request, 'main/subbab1.html')

# TAMBAHKAN FUNGSI INI KEMBALI
def latihan1_subbab1(request):
    # Tambahkan 'main/' agar Django mencari di folder yang benar
    return render(request, 'main/latihan1_subbab1.html')

def latihan2_subbab1(request):
    return render(request, 'main/latihan2_subbab1.html')

# --- FUNGSI LAINNYA ---
def subbab2(request):
    return render(request, 'subbab2.html')

def subbab3(request):
    return render(request, 'subbab3.html')

def subbab4(request):
    return render(request, 'subbab4.html')

def subbab5(request):
    return render(request, 'subbab5.html')