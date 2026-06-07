from types import SimpleNamespace

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings

from .services import ImageValidationError, extract_response_text, safe_openai_message, validate_image


class ImageValidationTests(SimpleTestCase):
    @override_settings(IMAGE_UPLOAD_MAX_BYTES=1024)
    def test_validate_image_accepts_supported_image(self):
        uploaded = SimpleUploadedFile(
            "note.png",
            b"fake-image",
            content_type="image/png",
        )

        image = validate_image(uploaded)

        self.assertEqual(image.content_type, "image/png")
        self.assertEqual(image.content, b"fake-image")

    @override_settings(IMAGE_UPLOAD_MAX_BYTES=4)
    def test_validate_image_rejects_large_image(self):
        uploaded = SimpleUploadedFile(
            "note.png",
            b"too-large",
            content_type="image/png",
        )

        with self.assertRaises(ImageValidationError):
            validate_image(uploaded)

    def test_validate_image_rejects_unsupported_type(self):
        uploaded = SimpleUploadedFile(
            "note.txt",
            b"hello",
            content_type="text/plain",
        )

        with self.assertRaises(ImageValidationError):
            validate_image(uploaded)

    @override_settings(IMAGE_UPLOAD_MAX_BYTES=1024)
    def test_validate_image_rejects_empty_file(self):
        uploaded = SimpleUploadedFile(
            "note.png",
            b"",
            content_type="image/png",
        )

        with self.assertRaises(ImageValidationError):
            validate_image(uploaded)


class ResponseTextTests(SimpleTestCase):
    def test_extract_response_text_prefers_output_text(self):
        response = SimpleNamespace(output_text="hello")

        self.assertEqual(extract_response_text(response), "hello")

    def test_extract_response_text_reads_output_fragments(self):
        response = SimpleNamespace(
            output=[
                SimpleNamespace(
                    content=[
                        SimpleNamespace(text="line 1"),
                        SimpleNamespace(text="line 2"),
                    ]
                )
            ]
        )

        self.assertEqual(extract_response_text(response), "line 1\nline 2")


class OpenAIErrorMessageTests(SimpleTestCase):
    @override_settings(OPENAI_API_KEY="sk-secret")
    def test_safe_openai_message_hides_api_key(self):
        error = RuntimeError("bad key sk-secret")

        self.assertEqual(safe_openai_message(error), "bad key [hidden]")
