# main/urls.py (SUDAH DIPERBAIKI)

from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='halamanUtama'),
    
    # ==========================
    # URL KHUSUS SISWA
    # ==========================
    path('siswa/dashboard/', views.dashboard, name='dashboard'),
    path('siswa/materi/', views.charts, name='materi'),
    path('siswa/kuis/', views.kuis, name='kuis'),
    
    # PERBAIKAN: Tambahkan 'siswa/' di depan
    path('siswa/subbab1/', views.subbab1, name='subbab1'),
    
    # PERBAIKAN: Tambahkan 'siswa/' di depan
    path('siswa/subbab1/latihan1_subbab1/', views.latihan1_subbab1, name='latihan1_subbab1'),
    
    # PERBAIKAN: Tambahkan 'siswa/' di depan
    path('siswa/subbab1/latihan2_subbab1/', views.latihan2_subbab1, name='latihan2_subbab1'),
    
    # PERBAIKAN: Tambahkan 'siswa/' di depan
    path('siswa/subbab2/', views.subbab2, name='subbab2'),
    path('siswa/subbab3/', views.subbab3, name='subbab3'),
    path('siswa/subbab4/', views.subbab4, name='subbab4'),
    path('siswa/subbab5/', views.subbab5, name='subbab5'),

    # ==========================
    # URL KHUSUS GURU (Ini sudah benar)
    # ==========================
    path('guru/dashboard/', views.guru_dashboard, name='guru_dashboard'),
    path('guru/kelas/', views.guru_kelas, name='guru_kelas'),
    path('guru/progres/', views.guru_progres, name='guru_progres'),
]