# Najprej iz Kulinarike zajamemo vse podatke iz glavnih strani (tj. strani, na katerih je po 20 receptov).
# To izvedemo za vsako kategorijo posebej, zato moramo vsakič posebej ustrezno spremeniti spremenljivke
# "kategorija", "st_strani" in "url" v funkciji "shrani_strani".

# Ko se program izvede, imamo csv datoteko "podatki_z_indeksi.csv", v kateri so podatki o indeksu recepta, 
# povezavi, imenu jedi, avtorju, času priprave jedi, povprečni oceni in kategoriji jedi.


import requests
import os
import re
import csv
import pandas as pd

kategorija = "sladice"
direktorij_glavne_strani = f'html_nizi\\{kategorija}_glavne_strani'
ime_csv_datoteke = 'podatki.csv'
direktorij_podstrani = f'html_nizi\\{kategorija}_podstrani'
st_strani = 401

def vsebina_url_kot_niz(url):
    """Funkcija kot argument sprejme niz in poskusi vrniti vsebino te spletne
    strani kot niz. V primeru, da med izvajanje pride do napake, vrne None.
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
    """Funkcija zapiše vrednost parametra "text" v novo ustvarjeno datoteko,
    locirano v "direktorij"/"ime_datoteke", ali povozi obstoječo. V primeru, da je
    niz "direktorij" prazen, datoteko ustvari v trenutni mapi.
    """
    os.makedirs(direktorij, exist_ok=True)
    path = os.path.join(direktorij, ime_datoteke)
    with open(path, 'w', encoding='utf-8') as file_out:
        file_out.write(niz)
    return None

def shrani_stran(url, direktorij, ime_datoteke):
    """Funkcija shrani vsebino spletne strani na naslovu "page" v datoteko
    "direktorij"/"ime_datoteke"."""
    shrani_niz_v_datoteko(vsebina_url_kot_niz(url), direktorij, ime_datoteke)

def shrani_strani(direktorij, st_strani):
    """Funkcija shrani vse strani določene kategorije od 1. do "st_strani" v thml datoteke z imenom '"kategorija"-"st_strani".html'."""
    url = f'https://www.kulinarika.net/recepti/seznam/sladice/?offset={(st_strani - 1) * 20 + 1}'
    ime_datoteke = '{}-{}.html'.format(kategorija, st_strani)
    shrani_stran(url, direktorij, ime_datoteke)

def preberi_dat_kot_niz(direktorij, ime_datoteke):
    """Funkcija vrne celotno vsebino datoteke "direktorij"/"ime_datoteke" kot niz."""
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
    objekt = re.compile(r"""<a href=(?P<povezava>.*?)>(?P<ime>.*?)</a></h3>.*""",
                        re.DOTALL)
    slovar = re.search(objekt, block).groupdict()
    vzorec_avtor = r"<a class='username'.*?>(?P<avtor>.*?)</a>"
    avtor = re.search(vzorec_avtor, block)
    if avtor is not None:
        slovar['avtor'] = avtor.group('avtor')
    else:
        slovar['avtor'] = 'Unknown'
    vzorec_cas = r"<span class='cas'>(?P<cas_priprave>.*?)</span>"
    cas = re.search(vzorec_cas, block)
    if cas is not None:
        slovar['cas_priprave'] = cas.group('cas_priprave')
    else:
        slovar['cas_priprave'] = 'Unknown'
    vzorec_ocena = r'<img alt="Povprečna ocena recepta: (?P<ocena>.*?)".*<p class="cas">'
    ocene = re.search(vzorec_ocena, block)
    if ocene is not None:
        slovar['povprečna_ocena'] = ocene.group('ocena')
    else:
        slovar['povprečna_ocena'] = 'Unknown'
    slovar['kategorija'] = kategorija
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
    Funkcija v csv datoteko podano s parametrom "ime_datoteke" zapiše
    vrednosti v parametru "recepti" pripadajoče ključem podanim v "kljuci"
    """
    with open(ime_datoteke, 'a', encoding='utf-8') as d:
        writer = csv.DictWriter(d, fieldnames=kljuci)
        for recept in recepti:
            writer.writerow(recept)
    return

def zapisi_recepte_v_csv(recepti, ime_datoteke):
    """Funkcija vse podatke iz parametra "recepti" zapiše v csv datoteko "ime_datoteke". 
    Funkcija predpostavi, da so ključi vseh slovarjev parametra recepti enaki 
    in je seznam recepti neprazen."""
    assert recepti and (all(j.keys() == recepti[0].keys() for j in recepti))
    izdelaj_csv(recepti[0].keys(), recepti, ime_datoteke)


def main(redownload=True, reparse=True):
    """Funkcija izvede celoten del pridobivanja podatkov:
    1. Recepte prenese iz Kulinarike
    2. Lokalno html datoteko pretvori v lepšo predstavitev podatkov
    3. Podatke shrani v csv datoteko
    """
    # Najprej v lokalno datoteko shranimo glavno stran
    recepti = []
    for i in range(st_strani):
        shrani_strani(direktorij_glavne_strani, i)

    # Iz lokalne (html) datoteke preberemo podatke
        recepti_str = seznam_receptov_na_strani(preberi_dat_kot_niz(direktorij_glavne_strani, f'{kategorija}-{i}.html'))
        recepti += recepti_str

    # Podatke preberemo v lepšo obliko (seznam slovarjev)
    recepti_sez = [slovar_iz_recepta_gl_str(recept) for recept in recepti]
    
    # Podatke shranimo v csv datoteko
    zapisi_recepte_v_csv(recepti_sez, ime_csv_datoteke)

    # Dodatno: S pomočjo parametrov funkcije main omogoči nadzor, ali se
    # celotna spletna stran ob vsakem zagon prenese (četudi že obstaja)
    # in enako za pretvorbo


if __name__ == '__main__':
    main()


# Na koncu še počistimo podvojene recepte in dodamo stolpec indeksov:
df = pd.read_csv('podatki.csv')
df = df.drop_duplicates(subset=['povezava'])
df = df.reset_index(drop=True)
df.to_csv('podatki_z_indeksi.csv')