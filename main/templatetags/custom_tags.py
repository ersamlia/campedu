from django import template
# JANGAN import model di sini untuk menghindari error 'Apps not loaded yet'

register = template.Library()

@register.simple_tag
def get_latihan_id(subbab_urutan):
    # REVISI: Import model DI DALAM fungsi
    from main.models import LatihanSoal 
    try:
        latihan = LatihanSoal.objects.get(subbab__urutan=subbab_urutan)
        return latihan.id
    except LatihanSoal.DoesNotExist:
        return None

@register.simple_tag
def get_pengayaan_id():
    # REVISI: Import model DI DALAM fungsi
    from main.models import SoalPengayaan
    try:
        pengayaan = SoalPengayaan.objects.first()
        if pengayaan:
            return pengayaan.id
        return None
    except SoalPengayaan.DoesNotExist:
        return None