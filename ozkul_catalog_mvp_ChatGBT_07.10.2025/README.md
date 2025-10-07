# ÖZKUL Katalog — MVP

## Hızlı Başlangıç (Render)
1. Bu klasörü bir Git deposu yap: `git init && git add . && git commit -m "init"`
2. GitHub'a gönder.
3. Render'da "New > Web Service > Build from Git repo" de.
4. `render.yaml` otomatik algılanır. `SECRET_PASSWORD` için tek bir şifre belirle.
5. Açılan linkten giriş: kullanıcı adı **ozkul** (sabit), şifre `SECRET_PASSWORD`.

## Lokal Çalıştırma
```
pip install -r requirements.txt
uvicorn app.main:app --reload
# http://localhost:8000
```

## Excel İçe/Dışa Aktarma
- `/import/excel` ile xlsx yükle (gömülü resimler desteklenir).
- `/export/excel` ile mevcut veriyi xlsx indir.

## PDF Katalog
- `/catalog/pdf` menüsünden "klasik / modern / minimal", ayrıca Logo ✔/❌, Şirket adı ✔/❌ seç.
