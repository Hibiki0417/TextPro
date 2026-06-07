from django.urls import path

from . import views


app_name = "ocr"

urlpatterns = [
    path("", views.index, name="index"),
    path("api/transcribe/", views.transcribe, name="transcribe"),
]
