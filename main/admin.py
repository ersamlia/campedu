from django.contrib import admin
from .models import (
    Profile, SubBab, LatihanSoal, Pertanyaan, PilihanJawaban,
    SoalPengayaan, PertanyaanPengayaan, PilihanPengayaan,
    ProgressSiswa, HasilLatihan, JawabanSiswa, HasilPengayaan
)

# Struktur ini membantu melihat relasi di admin
class PilihanJawabanInline(admin.TabularInline):
    model = PilihanJawaban
    extra = 4

class PertanyaanAdmin(admin.ModelAdmin):
    inlines = [PilihanJawabanInline]

class PilihanPengayaanInline(admin.TabularInline):
    model = PilihanPengayaan
    extra = 4

class PertanyaanPengayaanAdmin(admin.ModelAdmin):
    inlines = [PilihanPengayaanInline]

admin.site.register(Profile)
admin.site.register(SubBab)
admin.site.register(LatihanSoal)
admin.site.register(Pertanyaan, PertanyaanAdmin)
admin.site.register(SoalPengayaan)
admin.site.register(PertanyaanPengayaan, PertanyaanPengayaanAdmin)

# Model untuk melacak progres (opsional di admin, tapi bagus untuk dicek)
admin.site.register(ProgressSiswa)
admin.site.register(HasilLatihan)
admin.site.register(JawabanSiswa)
admin.site.register(HasilPengayaan)