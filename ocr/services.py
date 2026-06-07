import base64
from dataclasses import dataclass

from django.conf import settings
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    OpenAI,
    OpenAIError,
    PermissionDeniedError,
    RateLimitError,
)


ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}


@dataclass(frozen=True)
class UploadedImage:
    content: bytes
    content_type: str
    name: str


class ImageValidationError(ValueError):
    pass


class TranscriptionError(RuntimeError):
    pass


def validate_image(uploaded_file) -> UploadedImage:
    content_type = uploaded_file.content_type or ""
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ImageValidationError("JPEG、PNG、WebP、GIF の画像を選択してください。")

    max_bytes = settings.IMAGE_UPLOAD_MAX_BYTES
    if uploaded_file.size > max_bytes:
        max_mb = max_bytes / 1024 / 1024
        raise ImageValidationError(f"画像は {max_mb:.0f}MB 以下にしてください。")

    content = uploaded_file.read()
    if not content:
        raise ImageValidationError("画像ファイルが空です。別の画像を選択してください。")

    return UploadedImage(
        content=content,
        content_type=content_type,
        name=uploaded_file.name,
    )


def transcribe_handwriting(image: UploadedImage) -> str:
    if not settings.OPENAI_API_KEY:
        raise TranscriptionError("OPENAI_API_KEY が設定されていません。")

    encoded = base64.b64encode(image.content).decode("ascii")
    data_url = f"data:{image.content_type};base64,{encoded}"

    client = OpenAI(
        api_key=settings.OPENAI_API_KEY,
        max_retries=2,
        timeout=60.0,
    )

    try:
        response = client.responses.create(
            model=settings.OPENAI_MODEL,
            store=False,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "You are an OCR transcription engine for handwritten notes. "
                                "Transcribe only the visible handwriting in the image. "
                                "Preserve line breaks and reading order. "
                                "Return plain copy-pasteable text with no explanation. "
                                "If a character or word is unclear, mark it as [不明]."
                            ),
                        },
                        {
                            "type": "input_image",
                            "image_url": data_url,
                            "detail": "high",
                        },
                    ],
                }
            ],
        )
    except AuthenticationError as exc:
        raise TranscriptionError(
            "OpenAI APIキーが無効です。Render の環境変数 OPENAI_API_KEY を確認してください。"
        ) from exc
    except PermissionDeniedError as exc:
        raise TranscriptionError(
            f"このOpenAI APIキーではモデル {settings.OPENAI_MODEL} を使えません。OPENAI_MODEL を確認してください。"
        ) from exc
    except RateLimitError as exc:
        raise TranscriptionError(
            f"OpenAI API の利用上限に達しています。OpenAI の課金・利用上限・レート制限を確認してください。詳細: {safe_openai_message(exc)}"
        ) from exc
    except BadRequestError as exc:
        raise TranscriptionError(
            f"OpenAI API に送った画像リクエストが不正です。画像形式・サイズ・モデル設定を確認してください。詳細: {safe_openai_message(exc)}"
        ) from exc
    except (APIConnectionError, APITimeoutError) as exc:
        raise TranscriptionError(
            "OpenAI API への接続がタイムアウトしました。時間を置いてもう一度試してください。"
        ) from exc
    except APIStatusError as exc:
        raise TranscriptionError(
            f"OpenAI API がエラーを返しました。status={exc.status_code} 詳細: {safe_openai_message(exc)}"
        ) from exc
    except OpenAIError as exc:
        raise TranscriptionError(
            f"OpenAI API の呼び出しに失敗しました。詳細: {safe_openai_message(exc)}"
        ) from exc

    text = extract_response_text(response).strip()
    if not text:
        raise TranscriptionError("文字を読み取れませんでした。別の写真で試してください。")
    return text


def safe_openai_message(exc: Exception) -> str:
    message = str(exc)
    if settings.OPENAI_API_KEY:
        message = message.replace(settings.OPENAI_API_KEY, "[hidden]")
    return message[:500]


def extract_response_text(response) -> str:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return output_text

    fragments = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            text = getattr(content, "text", None)
            if text:
                fragments.append(text)
    return "\n".join(fragments)
