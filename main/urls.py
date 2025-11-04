# main/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Halaman Utama & Auth
    path('', views.halaman_utama_view, name='halaman_utama'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    # Lupa password dari file Anda
    path('forgot-password/', views.forgot_password_view, name='forgot_password'), 

    # === ALUR SISWA ===
    path('siswa/dashboard/', views.siswa_dashboard_view, name='siswa_dashboard'),
    
    # Modul Interaktif
    path('modul/<int:urutan_id>/', views.modul_view, name='modul'),
    path('modul/selesai/<int:subbab_id>/', views.modul_selesai_view, name='modul_selesai'),

    # Latihan Soal per Sub-Bab
    path('latihan/<int:latihan_id>/', views.latihan_soal_view, name='latihan_soal'),
    path('latihan/submit/<int:latihan_id>/', views.submit_latihan_view, name='submit_latihan'),
    path('latihan/hasil/<int:latihan_id>/', views.hasil_latihan_view, name='hasil_latihan'),

    # Soal Pengayaan
    path('pengayaan/<int:pengayaan_id>/', views.pengayaan_view, name='pengayaan'),
    path('pengayaan/submit/<int:pengayaan_id>/', views.submit_pengayaan_view, name='submit_pengayaan'),
    path('pengayaan/hasil/<int:pengayaan_id>/', views.hasil_pengayaan_view, name='hasil_pengayaan'),

    # === ALUR GURU ===
    path('guru/dashboard/', views.guru_dashboard_view, name='guru_dashboard'),
    path('guru/progres/', views.pantau_progres_view, name='pantau_progres'),
    path('guru/analisis/', views.analisis_hasil_view, name='analisis_hasil'),
]