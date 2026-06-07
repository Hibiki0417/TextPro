from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .services import ImageValidationError, TranscriptionError, transcribe_handwriting, validate_image


def index(request):
    return render(request, "ocr/index.html")


@require_POST
def transcribe(request):
    uploaded_file = request.FILES.get("image")
    if not uploaded_file:
        return JsonResponse({"error": "画像を選択してください。"}, status=400)

    try:
        image = validate_image(uploaded_file)
        text = transcribe_handwriting(image)
    except ImageValidationError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except TranscriptionError as exc:
        return JsonResponse({"error": str(exc)}, status=502)

    return JsonResponse({"text": text})
