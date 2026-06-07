const form = document.querySelector("#ocr-form");
const imageInput = document.querySelector("#image-input");
const fileName = document.querySelector("#file-name");
const previewWrap = document.querySelector(".preview-wrap");
const imagePreview = document.querySelector("#image-preview");
const submitButton = document.querySelector("#submit-button");
const copyButton = document.querySelector("#copy-button");
const resultText = document.querySelector("#result-text");
const resultMeta = document.querySelector("#result-meta");
const message = document.querySelector("#message");

function setBusy(isBusy) {
  submitButton.disabled = isBusy;
  submitButton.querySelector("span").textContent = isBusy ? "読み取り中..." : "テキスト化する";
}

function showMessage(text, isError = false) {
  message.textContent = text;
  message.classList.toggle("is-error", isError);
}

function friendlyBrowserError(error) {
  const rawMessage = error?.message || "";

  if (rawMessage.includes("did not match the expected pattern")) {
    return "入力値の形式が正しくありません。Render の OPENAI_API_KEY は sk-... のキー本体だけを設定してください。";
  }

  if (rawMessage.includes("Failed to fetch")) {
    return "サーバーに接続できませんでした。デプロイURLや通信状態を確認してください。";
  }

  return rawMessage || "処理に失敗しました。";
}

async function parseJsonResponse(response) {
  const contentType = response.headers.get("content-type") || "";

  if (contentType.includes("application/json")) {
    return response.json();
  }

  const text = await response.text();
  return {
    error: text ? text.slice(0, 300) : "サーバーからJSON以外の応答が返りました。",
  };
}

imageInput.addEventListener("change", () => {
  const file = imageInput.files[0];
  showMessage("");

  if (!file) {
    fileName.textContent = "JPEG / PNG / WebP / GIF";
    previewWrap.hidden = true;
    imagePreview.removeAttribute("src");
    return;
  }

  fileName.textContent = file.name;
  const objectUrl = URL.createObjectURL(file);
  imagePreview.src = objectUrl;
  imagePreview.onload = () => URL.revokeObjectURL(objectUrl);
  previewWrap.hidden = false;
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(form);
  setBusy(true);
  showMessage("");
  resultMeta.textContent = "OpenAI で画像を解析しています。";

  try {
    const response = await fetch(form.action, {
      method: "POST",
      body: formData,
      headers: {
        "X-CSRFToken": formData.get("csrfmiddlewaretoken"),
      },
    });
    const payload = await parseJsonResponse(response);

    if (!response.ok) {
      throw new Error(payload.error || "読み取りに失敗しました。");
    }

    resultText.value = payload.text;
    copyButton.disabled = payload.text.length === 0;
    resultMeta.textContent = `${payload.text.length} 文字`;
    showMessage("読み取りが完了しました。");
  } catch (error) {
    showMessage(friendlyBrowserError(error), true);
    resultMeta.textContent = "結果はここに表示されます。";
  } finally {
    setBusy(false);
  }
});

copyButton.addEventListener("click", async () => {
  if (!resultText.value) {
    return;
  }

  try {
    await navigator.clipboard.writeText(resultText.value);
    showMessage("コピーしました。");
  } catch {
    resultText.select();
    document.execCommand("copy");
    showMessage("コピーしました。");
  }
});
