from django.urls import path

from . import views

app_name = "sigla"

urlpatterns = [
    path("", views.UploadView.as_view(), name="upload"),
]
