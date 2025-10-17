# main/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('charts/', views.charts, name='charts'),
    path('tables/', views.tables, name='tables'),
    path('subbab1/', views.subbab1, name='subbab1'),
    path('subbab1/latihan1_subbab1/', views.latihan1_subbab1, name='latihan1_subbab1'),
    # URL BARU UNTUK LATIHAN 2
    path('subbab1/latihan2_subbab1/', views.latihan2_subbab1, name='latihan2_subbab1'),
    # URL sub-bab lainnya
    path('subbab2/', views.subbab2, name='subbab2'),
    path('subbab3/', views.subbab3, name='subbab3'),
    path('subbab4/', views.subbab4, name='subbab4'),
    path('subbab5/', views.subbab5, name='subbab5'),
]