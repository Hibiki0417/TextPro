$ErrorActionPreference = "Stop"

function Resolve-Python {
    $candidates = @("python", "py", "python3")
    foreach ($candidate in $candidates) {
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($command) {
            return $candidate
        }
    }
    throw "Python 3.10 or newer was not found. Install Python and run this script again."
}

$python = Resolve-Python

if (-not (Test-Path ".\.venv")) {
    & $python -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt

if (-not (Test-Path ".\.env")) {
    Copy-Item ".\.env.example" ".\.env"
}

Write-Host "Setup complete. Set OPENAI_API_KEY in .env."
