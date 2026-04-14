# PyToolkit

> Günlük geliştirici görevleri için beş pratik Python CLI aracı koleksiyonu.

[![Tests](https://github.com/Alperen520/PyToolkit/actions/workflows/tests.yml/badge.svg)](https://github.com/Alperen520/PyToolkit/actions/workflows/tests.yml)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

PyToolkit; toplu dosya yeniden adlandırma, format dönüştürme, web scraping, API testi ve metin temizleme gibi en sık karşılaşılan küçük otomasyon ihtiyaçları için hazırlanmış beş CLI aracından oluşuyor. Her araç bağımsız bir betik olup `argparse` arayüzü, hata yönetimi ve test kapsamıyla geliyor.

---

## İçindekiler

- [Araçlar](#araçlar)
- [Kurulum](#kurulum)
- [Kullanım](#kullanım)
  - [file_renamer](#1-file_renamer---toplu-dosya-yeniden-adlandırma)
  - [json_csv_converter](#2-json_csv_converter---json--csv-dönüştürücü)
  - [web_scraper](#3-web_scraper---web-scraper)
  - [api_tester](#4-api_tester---rest-api-test-aracı)
  - [text_cleaner](#5-text_cleaner---metin-temizleme)
- [Proje yapısı](#proje-yapısı)
- [Testleri çalıştırma](#testleri-çalıştırma)
- [Lisans](#lisans)

---

## Araçlar

| Araç | Amaç | Önemli parametreler |
|------|------|---------------------|
| **file_renamer** | Regex, prefix/suffix, büyük-küçük harf veya sıralı numaralandırma ile toplu yeniden adlandırma. | `--pattern`, `--replace`, `--prefix`, `--sequence`, `--dry-run` |
| **json_csv_converter** | JSON (nesne dizisi) ile CSV arasında iki yönlü dönüşüm. | `--input`, `--output`, `--direction`, `--flatten`, `--delimiter` |
| **web_scraper** | URL'den CSS seçici ile eleman çekme ve farklı formatlarda kaydetme. | `--url`, `--selector`, `--attr`, `--format` |
| **api_tester** | HTTP isteği gönderme, yanıt süresi ölçme ve sonucu kaydetme. | `--url`, `--method`, `--header`, `--json`, `--save` |
| **text_cleaner** | Metin temizleme: boşluk, noktalama, emoji, URL, HTML etiketi, rakam silme. | `--normalize-spaces`, `--remove-emoji`, `--strip-html`, `--lowercase` |

---

## Kurulum

### Yöntem A - Bağımlılıkları kurup modül olarak çalıştırma

```bash
git clone https://github.com/Alperen520/PyToolkit.git
cd PyToolkit
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Araçları modül olarak çalıştırabilirsiniz:

```bash
python -m tools.file_renamer --help
```

### Yöntem B - Paket olarak kurma (kısa CLI komutları)

```bash
pip install -e .
```

Kurulumdan sonra her araç kısa bir komutla kullanılabilir hale gelir:

```bash
file-renamer --help
json-csv     --help
web-scraper  --help
api-tester   --help
text-cleaner --help
```

### Gereksinimler

- Python 3.8 veya üstü
- `requests` >= 2.31
- `beautifulsoup4` >= 4.12
- `pytest` >= 7.4 (testler için)

---

## Kullanım

Tüm araçlar `--help` / `-h` ile tam belge çıktısı verir. Aşağıda en yaygın kullanım örnekleri yer almaktadır.

### 1. `file_renamer` - Toplu dosya yeniden adlandırma

Regex, prefix, suffix, büyük-küçük harf dönüşümü veya sıralı numaralandırma ile dosyaları yeniden adlandırır. Değişiklikleri uygulamadan önce `--dry-run` ile önizleme yapın.

```bash
# Tüm .jpg dosyalarında "IMG_" ifadesini "photo_" ile değiştir
python -m tools.file_renamer \
    --dir ./photos \
    --pattern "IMG_" --replace "photo_" \
    --ext .jpg

# Tarih prefix'i ekle, dosya adını küçük harfe çevir, önizle
python -m tools.file_renamer \
    --dir ./docs \
    --prefix "2026_" --lowercase \
    --recursive --dry-run

# Tüm PDF'leri sıralı numaralandır: scan_001.pdf, scan_002.pdf, ...
python -m tools.file_renamer \
    --dir ./scans \
    --glob "*.pdf" \
    --sequence "scan_{n:03d}"
```

Önemli parametreler:

- `--pattern` / `--replace` - Dosya adı gövdesinde regex bul/değiştir.
- `--prefix` / `--suffix` - Başa veya sona (uzantıdan önce) metin ekle.
- `--lowercase` / `--uppercase` / `--titlecase` - Büyük-küçük harf dönüşümü.
- `--sequence "scan_{n:03d}"` - Sıfır dolgulu numaralandırma ile sıralı yeniden adlandırma.
- `--recursive` - Alt klasörlere de inin.
- `--dry-run` - Dosyalara dokunmadan ne olacağını göster.

### 2. `json_csv_converter` - JSON <-> CSV dönüştürücü

Dosya uzantılarından yön otomatik algılanır.

```bash
# JSON -> CSV
python -m tools.json_csv_converter -i data.json -o data.csv

# CSV -> JSON (girintili)
python -m tools.json_csv_converter -i users.csv -o users.json --pretty

# İç içe JSON'ı düzleştirerek CSV'ye çevir ({"user": {"name": "Ada"}} -> user.name)
python -m tools.json_csv_converter -i nested.json -o flat.csv --flatten

# Noktalı virgül ayırıcılı CSV (Avrupa formatı)
python -m tools.json_csv_converter -i data.json -o data.csv --delimiter ";"
```

Farklı anahtarlara sahip satırları destekler; iç içe değerleri embedded JSON olarak saklar.

### 3. `web_scraper` - Web scraper

`requests` ile sayfayı çeker, `BeautifulSoup` ile parse eder, CSS seçici ile eleman seçer ve JSON, CSV veya düz metin olarak çıktı verir.

```bash
# Tüm H2 başlıklarını çek
python -m tools.web_scraper \
    --url https://example.com \
    --selector "h2.title"

# Linkleri JSON olarak kaydet
python -m tools.web_scraper \
    --url https://example.com \
    --selector "a" --attr href \
    --format json -o links.json

# Özel User-Agent, zaman aşımı ve sonuç limiti
python -m tools.web_scraper \
    --url https://example.com/shop \
    --selector "div.product > h3" \
    --user-agent "PyToolkit/1.0" \
    --timeout 15 --limit 20
```

> Her sitenin `robots.txt` dosyasına ve kullanım koşullarına uyun.

### 4. `api_tester` - REST API test aracı

Her HTTP metodunu destekler. Yanıt kodu, header'lar, gövde (JSON ise girintili) ve geçen süreyi gösterir.

```bash
# Basit GET
python -m tools.api_tester -u https://api.github.com/users/octocat

# JSON gövdeli POST ve özel header
python -m tools.api_tester \
    -u https://httpbin.org/post -X POST \
    --json '{"name": "Alperen"}' \
    --header "X-Api-Key: secret"

# Dosyadan gövde oku, yanıtı kaydet
python -m tools.api_tester \
    -u https://httpbin.org/put -X PUT \
    --data-file examples/api_tester/payload.json \
    --save response.json

# Sorgu parametreleri (tekrarlanabilir)
python -m tools.api_tester \
    -u https://httpbin.org/get \
    -q limit=10 -q page=2
```

Çıkış kodu 2xx yanıtlarda `0`, diğerlerinde `1`'dir - shell script'lerinde kullanışlıdır.

### 5. `text_cleaner` - Metin temizleme

Bağımsız parametreleri birleştirerek özel bir temizleme pipeline'ı oluşturun. Dosyadan veya stdin'den okur; dosyaya veya stdout'a yazar.

```bash
# Boşlukları düzenle ve küçük harfe çevir
python -m tools.text_cleaner \
    -i dirty.txt -o clean.txt \
    --normalize-spaces --lowercase

# HTML etiketi, URL ve emoji'yi tek geçişte temizle
python -m tools.text_cleaner \
    -i post.html -o post.txt \
    --strip-html --remove-urls --remove-emoji

# stdin'den oku, stdout'a yaz
echo "Merhaba   DÜNYA 😀" | python -m tools.text_cleaner \
    --normalize-spaces --remove-emoji
```

Mevcut işlemler: `--remove-emoji`, `--remove-urls`, `--strip-html`, `--remove-punct`, `--remove-digits`, `--normalize-spaces`, `--collapse-newlines`, `--normalize-unicode`, `--lowercase` / `--uppercase`, `--trim`.

---

## Proje yapısı

```
PyToolkit/
├── tools/                          # Beş CLI aracı
│   ├── __init__.py
│   ├── file_renamer.py
│   ├── json_csv_converter.py
│   ├── web_scraper.py
│   ├── api_tester.py
│   └── text_cleaner.py
├── examples/                       # Örnek giriş/çıkış dosyaları ve tarifler
│   ├── file_renamer/
│   ├── json_csv_converter/
│   ├── web_scraper/
│   ├── api_tester/
│   └── text_cleaner/
├── tests/                          # pytest test paketi
│   ├── conftest.py
│   ├── test_file_renamer.py
│   ├── test_json_csv_converter.py
│   ├── test_web_scraper.py
│   ├── test_api_tester.py
│   └── test_text_cleaner.py
├── .github/workflows/tests.yml     # CI: Python 3.8-3.12 üzerinde testler
├── requirements.txt
├── pyproject.toml                  # Paketleme ve CLI entry point'leri
├── CHANGELOG.md
├── LICENSE                         # MIT
├── .gitignore
├── README.md                       # İngilizce dokümantasyon
└── README.tr.md                    # Türkçe dokümantasyon
```

---

## Testleri çalıştırma

```bash
pip install -r requirements.txt
pytest
```

`web_scraper` ve `api_tester` testleri `requests`'i stub'lıyor - ağ bağlantısı gerekmez.

CI her push'ta Python 3.8, 3.9, 3.10, 3.11 ve 3.12 üzerinde 43 testi çalıştırır ve her CLI'nin `--help` çıktısını doğrular.

---

## Lisans

[MIT Lisansı](LICENSE) kapsamında yayınlanmıştır. © 2026 Alperen Akın.
