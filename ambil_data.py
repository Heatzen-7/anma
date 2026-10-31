"""Anma, Checkpoint 1: ambil data dari MyAnimeList.

Hasil:
  data/list_saya.csv        list Anda + atribut judul + franchise_id
  data/katalog_populer.csv  judul terpopuler + atribut + franchise_id
  data/relasi.csv           hubungan antar judul (sequel, prequel, dst.)

Cara pakai (di jendela cmd yang sudah (.venv) dan MAL_CLIENT_ID-nya di-set):
  python ambil_data.py              -> 2000 judul terpopuler
  python ambil_data.py --top 500    -> lebih cepat

Aman dihentikan dengan Ctrl+C lalu dijalankan lagi: hasil unduhan tersimpan di folder cache/.
"""
import argparse
import json
import os
import sys
import time

import pandas as pd
import requests

# ===== PENGATURAN =====
USER = "Heatzen"
JEDA = 0.6  # detik antar permintaan, supaya tidak membebani API MAL
# Hubungan yang dianggap "satu franchise". spin_off, character, dan other sengaja tidak ikut
# karena sering menyambungkan franchise yang sebenarnya berbeda.
HUBUNGAN_FRANCHISE = {"sequel", "prequel", "side_story", "parent_story", "full_story", "summary", "alternative_version"}
# ===== selesai =====

BASE = "https://api.myanimelist.net/v2"
FIELDS = ("id,title,media_type,status,num_episodes,mean,rank,popularity,num_list_users,genres,studios,"
          "source,start_season,start_date,average_episode_duration,rating,related_anime")
S = requests.Session()
S.headers["X-MAL-CLIENT-ID"] = os.environ.get("MAL_CLIENT_ID", "")


def get(url, params=None, coba=6):
    for i in range(coba):
        try:
            r = S.get(url, params=params, timeout=30)
        except requests.RequestException as e:
            tunggu = 2 ** i
            print(f"  koneksi gagal ({e.__class__.__name__}), menunggu {tunggu} detik")
            time.sleep(tunggu)
            continue
        if r.status_code == 200:
            time.sleep(JEDA)
            return r.json()
        if r.status_code in (429, 500, 502, 503, 504):
            tunggu = 5 * 2 ** i
            print(f"  HTTP {r.status_code}, menunggu {tunggu} detik")
            time.sleep(tunggu)
            continue
        if r.status_code == 404:
            return None
        sys.exit(f"HTTP {r.status_code}: {r.text[:200]}")
    sys.exit("Gagal berulang kali. Coba lagi nanti. Data yang sudah terunduh tersimpan di folder cache/.")


def ambil_list():
    url, params, hasil = f"{BASE}/users/{USER}/animelist", {"fields": "list_status", "limit": 1000}, []
    while url:
        d = get(url, params)
        params = None
        for it in d["data"]:
            ls = it["list_status"]
            hasil.append({"id": it["node"]["id"], "status": ls.get("status"),
                          "ditonton": ls.get("num_episodes_watched"), "diubah": ls.get("updated_at")})
        url = d.get("paging", {}).get("next")
    return hasil


def ambil_populer(n):
    ids, offset = [], 0
    while len(ids) < n:
        d = get(f"{BASE}/anime/ranking", {"ranking_type": "bypopularity", "limit": min(500, n - len(ids)), "offset": offset})
        batch = [x["node"]["id"] for x in d["data"]]
        if not batch:
            break
        ids += batch
        offset += len(batch)
    return ids


def detail(i):
    p = f"cache/{i}.json"
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    d = get(f"{BASE}/anime/{i}", {"fields": FIELDS})
    if d is not None:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False)
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=2000, help="jumlah judul terpopuler (0 = hanya list Anda)")
    a = ap.parse_args()
    if not S.headers["X-MAL-CLIENT-ID"]:
        sys.exit("MAL_CLIENT_ID belum diatur. Jalankan: set MAL_CLIENT_ID=ID_ANDA")
    os.makedirs("cache", exist_ok=True)
    os.makedirs("data", exist_ok=True)

    print("1/4 Mengambil list Anda...")
    saya = ambil_list()
    print(f"    {len(saya)} entri")
    print(f"2/4 Mengambil daftar {a.top} judul terpopuler...")
    populer = ambil_populer(a.top) if a.top > 0 else []
    semua = list(dict.fromkeys([x["id"] for x in saya] + populer))
    print(f"3/4 Mengambil detail {len(semua)} judul. Boleh dihentikan (Ctrl+C) dan dilanjutkan nanti.")
    det = {}
    for n, i in enumerate(semua, 1):
        d = detail(i)
        if d:
            det[i] = d
        if n % 25 == 0 or n == len(semua):
            print(f"    {n}/{len(semua)}")

    print("4/4 Mengelompokkan franchise dan menyimpan CSV...")
    induk, nama, relasi = {}, {}, []

    def cari(x):
        induk.setdefault(x, x)
        while induk[x] != x:
            induk[x] = induk[induk[x]]
            x = induk[x]
        return x

    def gabung(x, y):
        rx, ry = cari(x), cari(y)
        if rx != ry:
            induk[max(rx, ry)] = min(rx, ry)

    for i, d in det.items():
        cari(i)
        nama[i] = d.get("title")
        for r in d.get("related_anime", []):
            j, tipe = r["node"]["id"], r.get("relation_type")
            nama.setdefault(j, r["node"].get("title"))
            relasi.append({"id_a": i, "id_b": j, "relasi": tipe})
            if tipe in HUBUNGAN_FRANCHISE:
                gabung(i, j)

    def baris(d):
        ms = d.get("start_season") or {}
        dur = d.get("average_episode_duration")
        f = cari(d["id"])
        return {
            "id": d["id"], "judul": d["title"], "tipe": d.get("media_type"), "status_tayang": d.get("status"),
            "episode": d.get("num_episodes"), "durasi_eps_menit": round(dur / 60, 1) if dur else None,
            "skor_komunitas": d.get("mean"), "peringkat_skor": d.get("rank"), "peringkat_populer": d.get("popularity"),
            "jumlah_pengguna_list": d.get("num_list_users"),
            "genre": "|".join(g["name"] for g in d.get("genres", [])),
            "studio": "|".join(s["name"] for s in d.get("studios", [])),
            "sumber": d.get("source"), "tahun": ms.get("year"), "musim": ms.get("season"),
            "tanggal_mulai": d.get("start_date"), "rating_usia": d.get("rating"),
            "franchise_id": f, "franchise_nama": nama.get(f),
        }

    katalog = pd.DataFrame([baris(det[i]) for i in populer if i in det])
    saya_df = pd.DataFrame([{**baris(det[x["id"]]), "status_list": x["status"],
                             "episode_ditonton": x["ditonton"], "diubah_pada": x["diubah"]}
                            for x in saya if x["id"] in det])
    katalog.to_csv("data/katalog_populer.csv", index=False, encoding="utf-8-sig")
    saya_df.to_csv("data/list_saya.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(relasi).to_csv("data/relasi.csv", index=False, encoding="utf-8-sig")

    print("\n===== RINGKASAN (kirim bagian ini ke saya) =====")
    print("Entri di list Anda:", len(saya_df), "dari", len(saya), "(judul dewasa tidak ikut, sesuai bawaan MAL)")
    print("Franchise unik di list Anda:", saya_df["franchise_id"].nunique())
    print("Status di list Anda:", saya_df["status_list"].value_counts().to_dict())
    print("Tipe di list Anda:", saya_df["tipe"].value_counts().to_dict())
    print("Judul list Anda di luar kandidat populer:", int((~saya_df["id"].isin(populer)).sum()))
    print("Kandidat populer terambil:", len(katalog), "| franchise unik:", katalog["franchise_id"].nunique() if len(katalog) else 0)
    print("Franchise terbesar di list Anda:", saya_df["franchise_nama"].value_counts().head(3).to_dict())


if __name__ == "__main__":
    main()
