from django.contrib import admin
from .models import (
    Profile, SubBab, LatihanSoal, Pertanyaan, PilihanJawaban,
    SoalPengayaan, PertanyaanPengayaan, PilihanPengayaan,
    SiswaProgress, 
    HasilLatihan, JawabanSiswa, HasilPengayaan
)

# --- 1. Admin untuk Latihan Soal (Sub-bab) ---
class PilihanJawabanInline(admin.TabularInline):
    model = PilihanJawaban
    extra = 4 

class PertanyaanAdmin(admin.ModelAdmin):
    inlines = [PilihanJawabanInline]
    list_display = ('teks_pertanyaan', 'latihan')
    list_filter = ('latihan',)  # Memudahkan filter per Latihan
    
    fieldsets = (
        (None, {
            'fields': ('latihan', 'teks_pertanyaan', 'explanation') 
        }),
    )

# --- 2. Admin untuk Soal Pengayaan (Ujian Akhir) ---
class PilihanPengayaanInline(admin.TabularInline):
    model = PilihanPengayaan
    extra = 4

class PertanyaanPengayaanAdmin(admin.ModelAdmin):
    inlines = [PilihanPengayaanInline]
    # Menampilkan kolom Tipe di daftar soal
    list_display = ('teks_pertanyaan', 'tipe', 'pengayaan')
    # Menambahkan filter di samping kanan agar mudah mencari soal PG/Isian
    list_filter = ('pengayaan', 'tipe')
    search_fields = ('teks_pertanyaan',)

    # Mengatur tampilan form agar lebih rapi
    fieldsets = (
        ('Detail Soal', {
            'fields': ('pengayaan', 'tipe', 'teks_pertanyaan', 'explanation')
        }),
        ('Kunci Jawaban (Khusus Isian)', {
            'classes': ('collapse',), # Membuat bagian ini bisa ditutup/buka
            'fields': ('kunci_jawaban_isian',),
            'description': 'Isi kolom ini <b>HANYA</b> jika Tipe Soal adalah "Isian Singkat". Biarkan kosong jika Pilihan Ganda.'
        }),
    )

# --- Daftarkan Model ---
admin.site.register(Profile)
admin.site.register(SubBab)
admin.site.register(LatihanSoal)
admin.site.register(SoalPengayaan)

# Gunakan admin kustom untuk Pertanyaan
admin.site.register(Pertanyaan, PertanyaanAdmin)
admin.site.register(PertanyaanPengayaan, PertanyaanPengayaanAdmin)

# Model untuk melacak progres & hasil
admin.site.register(SiswaProgress) 
admin.site.register(HasilLatihan)
admin.site.register(JawabanSiswa)
admin.site.register(HasilPengayaan)
# admin.site.register(PilihanJawaban) # Opsional: Biasanya tidak perlu didaftarkan terpisah karena sudah ada di Inline
# admin.site.register(PilihanPengayaan) # Opsional