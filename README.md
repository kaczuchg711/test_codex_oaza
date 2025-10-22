# Rozpoznawanie sigli biblijnych

Aplikacja Django umożliwiająca przesłanie zdjęcia z podręcznika i automatyczne
wyszukanie sigli biblijnych z wykorzystaniem OCR (Tesseract) oraz biblioteki
[pythonbible](https://github.com/avendesora/pythonbible).

## Wymagania

- Python 3.11+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) (z pakietami językowymi `pol` i `eng`)

## Instalacja

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Migracje i uruchomienie

```bash
cd bible_sigla
python manage.py migrate
python manage.py runserver
```

Następnie otwórz przeglądarkę pod adresem <http://127.0.0.1:8000/> i wgraj
obraz. Aplikacja wyświetli znalezione sigla oraz pobrane fragmenty Biblii w
języku angielskim (King James Version).

## Testy

```bash
cd bible_sigla
python manage.py test
```
