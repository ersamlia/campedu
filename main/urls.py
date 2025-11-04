from django.urls import path
from . import views

urlpatterns = [
    # Halaman Utama & Auth
    path('', views.halaman_utama_view, name='halaman_utama'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'), 

    # === ALUR SISWA ===
    path('siswa/dashboard/', views.siswa_dashboard_view, name='siswa_dashboard'),
    
    # Modul Interaktif
    path('modul/<int:urutan_id>/', views.modul_view, name='modul'),
    
    # Latihan Soal per Sub-Bab
    path('latihan/<int:latihan_id>/', views.latihan_soal_view, name='latihan_soal'),
    path('latihan/submit/<int:latihan_id>/', views.submit_latihan_view, name='submit_latihan'),

    # Soal Pengayaan
    path('pengayaan/<int:pengayaan_id>/', views.pengayaan_view, name='pengayaan'),
    path('pengayaan/submit/<int:pengayaan_id>/', views.submit_pengayaan_view, name='submit_pengayaan'),

    # --- ALAT BANTU BELAJAR (DARI SIDEBAR) ---
    path('siswa/glosarium/', views.glosarium_view, name='glosarium'),
    path('siswa/lab-mikroskop/', views.lab_mikroskop_view, name='lab_mikroskop'),
    path('siswa/database-spesies/', views.database_spesies_view, name='database_spesies'),
    
    # --- URL BARU UNTUK MENANDAI SELESAI ---
    # REVISI: Mengganti 'modul_selesai_view'
    path('selesai/<str:step_name>/', views.selesai_step_view, name='selesai_step'),

    # === ALUR GURU ===
    path('guru/dashboard/', views.guru_dashboard_view, name='guru_dashboard'),
    path('guru/progres/', views.pantau_progres_view, name='pantau_progres'),
    path('guru/analisis/', views.analisis_hasil_view, name='analisis_hasil'),
]