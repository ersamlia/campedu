# main/admin.py

from django.contrib import admin
from .models import (
    Profile, SubBab, LatihanSoal, Pertanyaan, PilihanJawaban,
    SoalPengayaan, PertanyaanPengayaan, PilihanPengayaan,
    SiswaProgress, 
    HasilLatihan, JawabanSiswa, HasilPengayaan
)

# Struktur ini membantu melihat relasi di admin
class PilihanJawabanInline(admin.TabularInline):
    model = PilihanJawaban
    extra = 4 # Tampilkan 4 slot pilihan kosong

class PertanyaanAdmin(admin.ModelAdmin):
    inlines = [PilihanJawabanInline]
    list_display = ('teks_pertanyaan', 'latihan')
    
    # ==========================================================
    # PERBARUI/TAMBAHKAN BLOK 'fieldsets' INI
    # ==========================================================
    # Ini akan mengatur tampilan form admin saat Anda menambah/mengedit pertanyaan
    fieldsets = (
        (None, {
            # Tampilkan field ini di bagian atas
            'fields': ('latihan', 'teks_pertanyaan', 'explanation') 
        }),
    )
    # ==========================================================
    

class PilihanPengayaanInline(admin.TabularInline):
    model = PilihanPengayaan
    extra = 4

class PertanyaanPengayaanAdmin(admin.ModelAdmin):
    inlines = [PilihanPengayaanInline]
    list_display = ('teks_pertanyaan', 'pengayaan')

    # ==========================================================
    # PERBARUI/TAMBAHKAN BLOK 'fieldsets' INI JUGA
    # ==========================================================
    fieldsets = (
        (None, {
            'fields': ('pengayaan', 'teks_pertanyaan', 'explanation')
        }),
    )
    # ==========================================================


# --- Daftarkan Model Anda ---
admin.site.register(Profile)
admin.site.register(SubBab)
admin.site.register(LatihanSoal)
admin.site.register(SoalPengayaan)

# Gunakan admin kustom untuk Pertanyaan
admin.site.register(Pertanyaan, PertanyaanAdmin)
admin.site.register(PertanyaanPengayaan, PertanyaanPengayaanAdmin)

# Model untuk melacak progres
admin.site.register(SiswaProgress) 
admin.site.register(HasilLatihan)
admin.site.register(JawabanSiswa)
admin.site.register(HasilPengayaan)