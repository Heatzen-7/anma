"""Anma, Checkpoint 2: muat CSV ke database SQLite (anma.db).
Jalankan di folder anma:  python muat_sqlite.py
"""
import sqlite3

import pandas as pd

saya = pd.read_csv("data/list_saya.csv")
kat = pd.read_csv("data/katalog_populer.csv")
rel = pd.read_csv("data/relasi.csv")

ATRIBUT = ["id", "judul", "tipe", "status_tayang", "episode", "durasi_eps_menit", "skor_komunitas",
           "peringkat_skor", "peringkat_populer", "jumlah_pengguna_list", "sumber", "tahun", "musim",
           "tanggal_mulai", "rating_usia", "franchise_id", "franchise_nama"]

anime = pd.concat([saya[ATRIBUT], kat[ATRIBUT]]).drop_duplicates("id")
list_saya = saya[["id", "status_list", "episode_ditonton", "diubah_pada"]]
kandidat = kat[["id"]].drop_duplicates()


def pecah(kolom):
    """Satu baris per genre (atau studio) per judul."""
    s = pd.concat([saya[["id", kolom]], kat[["id", kolom]]]).drop_duplicates("id")
    s[kolom] = s[kolom].fillna("").str.split("|")
    s = s.explode(kolom)
    return s[s[kolom] != ""]


tabel = {"anime": anime, "list_saya": list_saya, "kandidat": kandidat,
         "genre_anime": pecah("genre"), "studio_anime": pecah("studio"), "relasi": rel}
con = sqlite3.connect("anma.db")
for nama, df in tabel.items():
    df.to_sql(nama, con, if_exists="replace", index=False)
    print(f"{nama}: {len(df)} baris")
con.close()
print("\nSelesai: anma.db dibuat.")
