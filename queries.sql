-- 1. Jumlah judul per status di list saya
SELECT status_list, COUNT(*) AS jumlah
FROM list_saya
GROUP BY status_list
ORDER BY jumlah DESC;

-- 2. 10 judul di list saya dengan skor komunitas tertinggi
SELECT a.judul, a.skor_komunitas, l.status_list
FROM list_saya AS l
JOIN anime AS a ON a.id = l.id
WHERE a.skor_komunitas IS NOT NULL
ORDER BY a.skor_komunitas DESC
LIMIT 10;

-- 3. 10 genre yang paling sering saya selesaikan
SELECT g.genre, COUNT(*) AS jumlah
FROM list_saya AS l
JOIN genre_anime AS g ON g.id = l.id
WHERE l.status_list = 'completed'
GROUP BY g.genre
ORDER BY jumlah DESC
LIMIT 10;

-- 4. Per genre: berapa yang selesai dan berapa yang ditunda atau dihentikan
SELECT g.genre,
       COUNT(*) AS total,
       SUM(CASE WHEN l.status_list = 'completed' THEN 1 ELSE 0 END) AS selesai,
       SUM(CASE WHEN l.status_list IN ('on_hold', 'dropped') THEN 1 ELSE 0 END) AS ditunda_dihentikan
FROM list_saya AS l
JOIN genre_anime AS g ON g.id = l.id
GROUP BY g.genre
HAVING total >= 5
ORDER BY ditunda_dihentikan DESC, total DESC;

-- 5. Per genre: berapa persen judul populer yang sudah saya selesaikan (10 genre paling jarang)
SELECT g.genre,
       COUNT(*) AS populer,
       SUM(CASE WHEN l.status_list = 'completed' THEN 1 ELSE 0 END) AS selesai_saya,
       ROUND(100.0 * SUM(CASE WHEN l.status_list = 'completed' THEN 1 ELSE 0 END) / COUNT(*), 1) AS persen
FROM kandidat AS k
JOIN genre_anime AS g ON g.id = k.id
LEFT JOIN list_saya AS l ON l.id = k.id
GROUP BY g.genre
HAVING populer >= 30
ORDER BY persen ASC
LIMIT 10;

-- 6. 10 franchise terbesar di list saya
SELECT a.franchise_nama, COUNT(*) AS jumlah_entri
FROM list_saya AS l
JOIN anime AS a ON a.id = l.id
GROUP BY a.franchise_id
ORDER BY jumlah_entri DESC
LIMIT 10;

-- 7. 15 franchise populer yang belum saya tonton sama sekali
WITH populer AS (
    SELECT a.franchise_id, a.franchise_nama, MIN(a.peringkat_populer) AS peringkat_terbaik
    FROM kandidat AS k
    JOIN anime AS a ON a.id = k.id
    GROUP BY a.franchise_id
),
sudah AS (
    SELECT DISTINCT a.franchise_id
    FROM list_saya AS l
    JOIN anime AS a ON a.id = l.id
    WHERE l.status_list <> 'plan_to_watch'
)
SELECT p.franchise_nama, p.peringkat_terbaik
FROM populer AS p
LEFT JOIN sudah AS s ON s.franchise_id = p.franchise_id
WHERE s.franchise_id IS NULL
ORDER BY p.peringkat_terbaik
LIMIT 15;
