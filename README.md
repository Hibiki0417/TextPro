# TextPro

手書き文字の写真をアップロードすると、OpenAI API で読み取り、コピーしやすいテキストとして返す Django アプリです。

## セットアップ

Python 3.10 以上が必要です。

```powershell
cd C:\textpro
.\setup.ps1
```

`.env` の `OPENAI_API_KEY` を自分の API キーに置き換えてください。

## 起動

```powershell
.\run.ps1
```

ブラウザで http://127.0.0.1:8000/ を開きます。

## メモ

- アップロード画像はサーバーに保存せず、OpenAI API 呼び出しのためにメモリ上で Base64 data URL に変換します。
- 対応画像は JPEG、PNG、WebP、GIF です。
- 既定のモデルは `.env` の `OPENAI_MODEL` で変更できます。
- 画像サイズ上限は `IMAGE_UPLOAD_MAX_BYTES` で変更できます。

## デプロイ

Render などの Python 対応ホスティングにそのまま載せられる設定を含めています。

必要な環境変数:

- `OPENAI_API_KEY`
- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG=False`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`

Render では `render.yaml` を使って Blueprint として作成できます。
