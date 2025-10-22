from django import forms


class ImageUploadForm(forms.Form):
    image = forms.ImageField(
        label="Dodaj zdjęcie z podręcznika",
        help_text="Wybierz zdjęcie lub zrzut ekranu z siglami biblijnymi.",
    )
