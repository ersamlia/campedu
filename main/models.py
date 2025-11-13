from django.db import models
from django.contrib.auth.models import User

# 1. MODEL UNTUK AUTENTIKASI DAN PERAN (ROLES)
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ROLE_CHOICES = (
        ('SISWA', 'Siswa'),
        ('GURU', 'Guru'),
    )
    role = models.CharField(max_length=5, choices=ROLE_CHOICES)

    def __str__(self):
        return f'{self.user.username} - {self.role}'

# 2. MODEL UNTUK KONTEN PEMBELAJARAN
class SubBab(models.Model):
    judul = models.CharField(max_length=200)
    urutan = models.IntegerField(unique=True, help_text="Urutan bab, e.g., 1, 2, 3")
    
    def __str__(self):
        return f'{self.urutan}. {self.judul}'

class LatihanSoal(models.Model):
    subbab = models.OneToOneField(SubBab, on_delete=models.CASCADE)
    judul = models.CharField(max_length=200)

    def __str__(self):
        return self.judul

class Pertanyaan(models.Model):
    latihan = models.ForeignKey(LatihanSoal, on_delete=models.CASCADE, related_name='pertanyaan_set')
    teks_pertanyaan = models.TextField()
    
    # <-- TAMBAHKAN BARIS DI BAWAH INI -->
    explanation = models.TextField(blank=True, null=True, help_text="Penjelasan/Feedback untuk jawaban yang benar")

    def __str__(self):
        return self.teks_pertanyaan

class PilihanJawaban(models.Model):
    pertanyaan = models.ForeignKey(Pertanyaan, on_delete=models.CASCADE, related_name='pilihan_set')
    teks_pilihan = models.CharField(max_length=200)
    is_benar = models.BooleanField(default=False)

    def __str__(self):
        return self.teks_pilihan

# 3. MODEL UNTUK UJIAN AKHIR BAB (PENGAYAAN)
class SoalPengayaan(models.Model):
    judul = models.CharField(max_length=200, default="Ujian Akhir Bab")

    def __str__(self):
        return self.judul

class PertanyaanPengayaan(models.Model):
    pengayaan = models.ForeignKey(SoalPengayaan, on_delete=models.CASCADE, related_name='pertanyaan_set')
    teks_pertanyaan = models.TextField()

    # <-- TAMBAHKAN BARIS DI BAWAH INI -->
    explanation = models.TextField(blank=True, null=True, help_text="Penjelasan/Feedback untuk jawaban yang benar")

    def __str__(self):
        return self.teks_pertanyaan

class PilihanPengayaan(models.Model):
    pertanyaan = models.ForeignKey(PertanyaanPengayaan, on_delete=models.CASCADE, related_name='pilihan_set')
    teks_pilihan = models.CharField(max_length=200)
    is_benar = models.BooleanField(default=False)

    def __str__(self):
        return self.teks_pilihan

# 4. MODEL BARU UNTUK MELACAK PROGRES SISWA (LINEAR)
class SiswaProgress(models.Model):
    siswa = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Kunci Progres (Default=False)
    # Sub-Bab 1
    modul_1_completed = models.BooleanField(default=False)
    latihan_1_completed = models.BooleanField(default=False)
    
    # Sub-Bab 2 (Alur baru menyisipkan alat bantu)
    glosarium_completed = models.BooleanField(default=False)
    modul_2_completed = models.BooleanField(default=False)
    latihan_2_completed = models.BooleanField(default=False)
    
    # Sub-Bab 3 (Alur baru menyisipkan alat bantu)
    mikroskop_completed = models.BooleanField(default=False)
    modul_3_completed = models.BooleanField(default=False)
    database_completed = models.BooleanField(default=False)
    latihan_3_completed = models.BooleanField(default=False)
    
    # Ujian Akhir
    pengayaan_completed = models.BooleanField(default=False)

    def __str__(self):
        return f'Progres untuk {self.siswa.username}'

# 5. MODEL UNTUK MELACAK SKOR DAN JAWABAN
class HasilLatihan(models.Model):
    siswa = models.ForeignKey(User, on_delete=models.CASCADE)
    latihan = models.ForeignKey(LatihanSoal, on_delete=models.CASCADE)
    skor = models.DecimalField(max_digits=5, decimal_places=2) # Skor 0-100

class JawabanSiswa(models.Model):
    # Model ini PENTING untuk fitur analisis guru
    siswa = models.ForeignKey(User, on_delete=models.CASCADE)
    pertanyaan = models.ForeignKey(Pertanyaan, on_delete=models.CASCADE)
    pilihan_dipilih = models.ForeignKey(PilihanJawaban, on_delete=models.CASCADE)
    is_benar = models.BooleanField()

class HasilPengayaan(models.Model):
    siswa = models.ForeignKey(User, on_delete=models.CASCADE)
    pengayaan = models.ForeignKey(SoalPengayaan, on_delete=models.CASCADE)
    skor = models.DecimalField(max_digits=5, decimal_places=2)