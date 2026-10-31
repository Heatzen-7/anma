"""Menjalankan semua query di sebuah file .sql dan mencetak hasilnya.
Contoh:  python jalankan_sql.py latihan.sql
"""
import re
import sqlite3
import sys

import pandas as pd

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)
pd.set_option("display.max_rows", 60)
pd.set_option("display.max_colwidth", 45)

berkas = sys.argv[1] if len(sys.argv) > 1 else "latihan.sql"
teks = open(berkas, encoding="utf-8").read()
con = sqlite3.connect("anma.db")
for blok in teks.split(";"):
    baris = blok.splitlines()
    sql = "\n".join(b for b in baris if not b.strip().startswith("--")).strip()
    if not sql:
        continue
    judul = next((b.strip()[2:].strip() for b in baris if re.match(r"--\s*\d+\.", b.strip())), "(tanpa judul)")
    print("\n" + "=" * 72)
    print(judul)
    try:
        print(pd.read_sql_query(sql, con).to_string(index=False))
    except Exception as e:
        print("ERROR SQL:", e)
con.close()
