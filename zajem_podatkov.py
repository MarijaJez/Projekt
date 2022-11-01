import requests
import os
import re
import csv

juhe_zacetna_stran_url = 'https://www.kulinarika.net/recepti/seznam/juhe-in-zakuhe/'
direktorij = 'html_nizi'
juhe_glavna_stran = 'juhe.html'
ime_csv_datoteke = 'podatki.csv'

def vsebina_url_kot_niz(url):
    """Funkcija kot argument sprejme niz in poskusi vrniti vsebino te spletne
    strani kot niz. V primeru, da med izvajanje pride do napake vrne None.
    """
    try:
        # del kode, ki morda sproži napako
        vsebina = requests.get(url)
    except Exception as e:
        print(f'Napaka pri prenosu: {url} ::', e)
        return None
        # koda, ki se izvede pri napaki
        # dovolj je če izpišemo opozorilo in prekinemo izvajanje funkcije
    # nadaljujemo s kodo če ni prišlo do napake
    return vsebina.text

def shrani_niz_v_datoteko(niz, direktorij, ime_datoteke):
    """Funkcija zapiše vrednost parametra "text" v novo ustvarjeno datoteko
    locirano v "directory"/"filename", ali povozi obstoječo. V primeru, da je
    niz "directory" prazen datoteko ustvari v trenutni mapi.
    """
    os.makedirs(direktorij, exist_ok=True)
    path = os.path.join(direktorij, ime_datoteke)
    with open(path, 'w', encoding='utf-8') as file_out:
        file_out.write(niz)
    return None

def shrani_zacetno_stran(url, direktorij, ime_datoteke):
    """Funkcija shrani vsebino spletne strani na naslovu "page" v datoteko
    "directory"/"filename"."""
    shrani_niz_v_datoteko(vsebina_url_kot_niz(url), direktorij, ime_datoteke)


def preberi_dat_kot_niz(direktorij, ime_datoteke):
    """Funkcija vrne celotno vsebino datoteke "directory"/"filename" kot niz."""
    with open(os.path.join(direktorij, ime_datoteke), 'r', encoding='utf-8') as datoteka:
        return datoteka.read()

def seznam_receptov_na_strani(vsebina_strani):
    """Funkcija poišče posamezne recepte, ki se nahajajo v spletni strani in
    vrne seznam receptov."""
    vzorec = re.compile(r"""<article class='en_recept clearfix'>(.*?)</article>""",
                    flags=re.DOTALL)
    recepti = re.findall(vzorec, vsebina_strani)
    return recepti

def slovar_iz_recepta_gl_str(block):
    """Funkcija iz niza za posamezen recept izlušči podatke o imenu jedi, avtorju, oceni, času priprave in 
    povezavi do strani recepta ter vrne slovar, ki vsebuje ustrezne podatke."""
    objekt = re.compile(r"""<a href=(?P<povezava>.*?)>(?P<ime>.*?)</a></h3>.*<a class='username'.*?>(?P<avtor>.*?)</a>.*<span class='cas'>(?P<cas_priprave>.*?)</span>""",
                        re.DOTALL)
    slovar = re.search(objekt, block).groupdict()
    vzorec_ocena = r'<img alt="Povprečna ocena recepta: (?P<ocena>.*?)".*<p class="cas">'
    ocene = re.search(vzorec_ocena, block)
    if ocene is not None:
        slovar['povprečna_ocena'] = ocene.group('ocena')
    else:
        slovar['povprečna_ocena'] = 'Unknown'
    return slovar

def podatki_o_receptu_iz_datoteke(ime_datoteke, direktorij):
    """Funkcija prebere podatke v datoteki "direktorij"/"ime_datoteke" in jih
    pretvori (razčleni) v pripadajoč seznam slovarjev za vsak recept posebej."""
    seznam = []
    for recept in seznam_receptov_na_strani(preberi_dat_kot_niz(ime_datoteke, direktorij)):
        seznam.append(slovar_iz_recepta_gl_str(recept))
    return seznam


def izdelaj_csv(kljuci, recepti, ime_datoteke):
    """
    Funkcija v csv datoteko podano s parametroma "directory"/"filename" zapiše
    vrednosti v parametru "rows" pripadajoče ključem podanim v "fieldnames"
    """
    with open(ime_datoteke, 'w', encoding='utf-8') as d:
        writer = csv.DictWriter(d, fieldnames=kljuci)
        writer.writeheader()
        for recept in recepti:
            writer.writerow(recept)
    return

def zapisi_recepte_v_csv(recepti, ime_datoteke):
    """Funkcija vse podatke iz parametra "ads" zapiše v csv datoteko podano s
    parametroma "directory"/"filename". Funkcija predpostavi, da so ključi vseh
    slovarjev parametra ads enaki in je seznam ads neprazen."""
    assert recepti and (all(j.keys() == recepti[0].keys() for j in recepti))
    izdelaj_csv(recepti[0].keys(), recepti, ime_datoteke)


def main(redownload=True, reparse=True):
    """Funkcija izvede celoten del pridobivanja podatkov:
    1. Recepte prenese iz Kulinarike
    2. Lokalno html datoteko pretvori v lepšo predstavitev podatkov
    3. Podatke shrani v csv datoteko
    """
    # Najprej v lokalno datoteko shranimo glavno stran
    shrani_zacetno_stran(juhe_zacetna_stran_url, direktorij, juhe_glavna_stran)

    # Iz lokalne (html) datoteke preberemo podatke
    recepti = seznam_receptov_na_strani(preberi_dat_kot_niz(direktorij, juhe_glavna_stran))

    # Podatke preberemo v lepšo obliko (seznam slovarjev)
    recepti_sez = [slovar_iz_recepta_gl_str(recept) for recept in recepti]
    
    # Podatke shranimo v csv datoteko
    zapisi_recepte_v_csv(recepti_sez, ime_csv_datoteke)
    # Dodatno: S pomočjo parametrov funkcije main omogoči nadzor, ali se
    # celotna spletna stran ob vsakem zagon prenese (četudi že obstaja)
    # in enako za pretvorbo


if __name__ == '__main__':
    main()

