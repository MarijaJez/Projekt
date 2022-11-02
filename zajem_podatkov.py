import requests
import os
import re
import csv
from csv import writer
from csv import reader
import pandas as pd

juhe_zacetna_stran_url = 'https://www.kulinarika.net/recepti/seznam/juhe-in-zakuhe/?offset=0'
direktorij_glavne_strani = 'html_nizi'
juhe_glavna_stran = 'juhe.html'
ime_csv_datoteke = 'podatki.csv'
direktorij_podstrani_juhe = 'html_nizi\\juhe_podstrani'
csv_sestavine = 'sestavine.csv'
csv_postopki = 'postopki.csv'

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

def shrani_stran(url, direktorij, ime_datoteke):
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
    Funkcija v csv datoteko podano s parametrom "ime_datoteke" zapiše
    vrednosti v parametru "recepti" pripadajoče ključem podanim v "kljuci"
    """
    with open(ime_datoteke, 'w', encoding='utf-8') as d:
        writer = csv.DictWriter(d, fieldnames=kljuci)
        writer.writeheader()
        for recept in recepti:
            writer.writerow(recept)
    return

def izdelaj_csv_sestavine(indeks_recepta, sestavine, ime_datoteke):
    """
    Funkcija v csv datoteko podano s parametrom "ime_datoteke" zapiše
    vrednosti v parametru "recepti" pripadajoče ključem podanim v "kljuci"
    """
    with open(ime_datoteke, 'a', encoding='utf-8') as d:
        writer = csv.DictWriter(d, fieldnames=['indeks', 'količina', 'sestavina'])
        for sestavina in sestavine:
            sestavina_slovar = {'indeks': indeks_recepta, 'količina': sestavina[0], 'sestavina': sestavina[1]}
            writer.writerow(sestavina_slovar)
    return

def izdelaj_csv_postopki(indeks_recepta, postopek, ime_datoteke):
    """
    Funkcija v csv datoteko podano s parametrom "ime_datoteke" zapiše
    vrednosti v parametru "recepti" pripadajoče ključem podanim v "kljuci"
    """
    with open(ime_datoteke, 'a', encoding='utf-8') as d:
        writer = csv.DictWriter(d, fieldnames=['indeks', 'korak', 'navodila'])
        for korak in postopek:
            sestavina_slovar = {'indeks': indeks_recepta, 'korak': korak[0], 'navodila': korak[1]}
            writer.writerow(sestavina_slovar)
    return

def zapisi_recepte_v_csv(recepti, ime_datoteke):
    """Funkcija vse podatke iz parametra "ads" zapiše v csv datoteko podano s
    parametroma "directory"/"filename". Funkcija predpostavi, da so ključi vseh
    slovarjev parametra ads enaki in je seznam ads neprazen."""
    assert recepti and (all(j.keys() == recepti[0].keys() for j in recepti))
    izdelaj_csv(recepti[0].keys(), recepti, ime_datoteke)


def dodaj_indekse(ime_datoteke):
    """Funkcija podatkom v csv datoteki doda še en stolpec indeksov."""
    data_new = pd.read_csv(ime_datoteke)
    # data_new['indeks'] = range(len(data_new))
    data_new.to_csv('podatki_z_indeksi.csv')
    # with open(ime_datoteke, 'r') as read_obj:
    #         with open('output_1.csv', 'w', newline='') as write_obj:
    #             csv_reader = reader(read_obj)
    #             csv_writer = writer(write_obj)
    #             i = 0
    #             for row in csv_reader:
    #                 row.append(i)
    #                 csv_writer.writerow(row)
    #                 i += 1


def main(redownload=True, reparse=True):
    """Funkcija izvede celoten del pridobivanja podatkov:
    1. Recepte prenese iz Kulinarike
    2. Lokalno html datoteko pretvori v lepšo predstavitev podatkov
    3. Podatke shrani v csv datoteko
    """
    # Najprej v lokalno datoteko shranimo glavno stran
    shrani_stran(juhe_zacetna_stran_url, direktorij_glavne_strani, juhe_glavna_stran)

    # Iz lokalne (html) datoteke preberemo podatke
    recepti = seznam_receptov_na_strani(preberi_dat_kot_niz(direktorij_glavne_strani, juhe_glavna_stran))

    # Podatke preberemo v lepšo obliko (seznam slovarjev)
    recepti_sez = [slovar_iz_recepta_gl_str(recept) for recept in recepti]
    
    # Podatke shranimo v csv datoteko
    zapisi_recepte_v_csv(recepti_sez, ime_csv_datoteke)
    dodaj_indekse(ime_csv_datoteke)
    # Dodatno: S pomočjo parametrov funkcije main omogoči nadzor, ali se
    # celotna spletna stran ob vsakem zagon prenese (četudi že obstaja)
    # in enako za pretvorbo


def shrani_podstrani(podatki, direktorij):
    """Funkcija shrani v datoteko direktorij/ime_datoteke html vseh podstrani glavne strani, 
    katerih url-ji so v datoteki s podatki."""
    recepti = pd.read_csv(podatki)
    for i, url in enumerate(recepti['povezava']):
        shrani_stran("https://www.kulinarika.net/" + url[1:-1], direktorij, str(i) + ".html")

def podatki_o_receptu_iz_podstrani(direktorij, podstran):
    """Funkcija iz html-ja podstrani izlušči podatke o sestavinah, potrebnih za pripravo jedi in 
    postopku priprave ter jih shrani v ločene csv datoteke."""
    indeks = podstran.split('.')[0]
    podstran = preberi_dat_kot_niz(direktorij, podstran)
    sestavina = re.compile(r"""<p class="cf" itemprop="recipeIngredient"><span class="label">(?P<kolicina>.*?)</span><span class="label-value">(?P<sestavina>.*?)</span></p>""",
                        re.DOTALL)
    sestavine = re.findall(sestavina, podstran)
    korak = re.compile(r"""<p class="cf en_korak_postopek" itemprop="recipeInstructions"><span class="label">(?P<korak>.*?) </span><span class="data">(?P<postopek>.*?)</span></p>""",
                        re.DOTALL)
    postopek = re.findall(korak, podstran)
    
    return indeks, sestavine, postopek

def shrani_podatke_iz_podstrani(direktorij, podstran, ime_datoteke_sestavine, ime_datoteke_postopki):
    """Funkcija shrani podatke o sestavinah iz strani na 'direktorij'/'podstran' v datoteko 
    'ime_datoteke_sestavine' in podatke o postopkih iz strani na 'direktorij'/'podstran' v 
    datoteko 'ime_datoteke_postopki'."""
    indeks, sestavine, postopek = podatki_o_receptu_iz_podstrani(direktorij, podstran)
    izdelaj_csv_sestavine(indeks, sestavine, ime_datoteke_sestavine)
    izdelaj_csv_postopki(indeks, postopek, ime_datoteke_postopki)


def main2():
    """Funkcija shrani htmlje vseh podstrani na povezavah v datoteki juhe.html in iz njih zajame
    podatke o sestavinah in postopkih, ki jh skrani v svoji 2 csv datoteki."""
    shrani_podstrani(ime_csv_datoteke, direktorij_podstrani_juhe)

    dirs = os.listdir(direktorij_podstrani_juhe)
    for datoteka in dirs:
        shrani_podatke_iz_podstrani(direktorij_podstrani_juhe, datoteka, csv_sestavine, csv_postopki)


if __name__ == '__main__':
    main()
    main2()

