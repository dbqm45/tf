# Instaluje komendę `tf` (launcher fabryki) na Windows. Fabrykę w projekcie instaluje potem `tf install`.
#
#   irm <adres tego pliku> | iex
#   powershell -ExecutionPolicy Bypass -File scripts\install.ps1      # z klonu repozytorium
#
# Zmienne (opcjonalne): TF_REPO (domyślnie https://github.com/dbqm45/tf.git), TF_BIN (domyślnie ~\.local\bin),
# TF_PYTHON (domyślnie py, python3, python), TF_GIT (domyślnie git). Opis: docs/setup.md.
# Skrypt niczego nie instaluje poza tf i tf.cmd w TF_BIN; PATH zmienia tylko po potwierdzeniu (TF_NO_PATH=1 — bez pytania).
$ErrorActionPreference = 'Stop'

$Repo = if ($env:TF_REPO) { $env:TF_REPO } else { 'https://github.com/dbqm45/tf.git' }
$Bin = if ($env:TF_BIN) { $env:TF_BIN } else { Join-Path $HOME '.local\bin' }
$Git = if ($env:TF_GIT) { $env:TF_GIT } else { 'git' }

# throw, nie exit: przy `irm … | iex` exit zamknąłby okno PowerShella
function Fail($msg) { throw "✗ $msg" }

# Python 3.9+ (alias ze Sklepu Microsoft nie uruchamia Pythona — odpada w sprawdzeniu wersji)
$Py = $null
$cands = if ($env:TF_PYTHON) { @($env:TF_PYTHON) } else { @('py', 'python3', 'python') }
foreach ($c in $cands) {
    if (Get-Command $c -ErrorAction SilentlyContinue) {
        & $c -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) { $Py = $c; break }
    }
}
if (-not $Py) { Fail "Brak Pythona 3.9+ (sprawdzono: $($cands -join ', ')). Zainstaluj go: winget install Python.Python.3.12 albo https://www.python.org/downloads/" }

if (-not (Get-Command $Git -ErrorAction SilentlyContinue)) { Fail "Brak gita ($Git). Zainstaluj go: winget install Git.Git albo https://git-scm.com/downloads" }

$Tmp = Join-Path ([IO.Path]::GetTempPath()) ("tf-install." + [Guid]::NewGuid().ToString('N'))
try {
    Write-Host "→ Pobieram fabrykę z $Repo"
    & $Git clone -q --depth 1 $Repo (Join-Path $Tmp 'tf')
    if ($LASTEXITCODE -ne 0) { Fail "Nie udało się pobrać $Repo. Prywatne repozytorium wymaga dostępu w gicie (gh auth login albo Git Credential Manager)." }
    & $Py (Join-Path $Tmp 'tf\core\factory\tf.py') --install-launcher --repo $Repo --bin $Bin
    if ($LASTEXITCODE -ne 0) { Fail 'Instalacja launchera nie powiodła się.' }
} finally {
    if (Test-Path $Tmp) { Remove-Item -Recurse -Force $Tmp }
}

$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
if (-not (($userPath -split ';') -contains $Bin) -and -not $env:TF_NO_PATH -and [Environment]::UserInteractive) {
    $ans = Read-Host "Dodać $Bin do PATH użytkownika? [t/N]"
    if ($ans -match '^[tTyY]') {
        [Environment]::SetEnvironmentVariable('Path', "$userPath;$Bin", 'User')
        Write-Host "✓ Dodano do PATH — otwórz nowe okno terminala."
    } else {
        Write-Host "ℹ Dodaj $Bin do PATH, żeby wywoływać tf z dowolnego katalogu."
    }
}
Write-Host '✓ Gotowe. W katalogu projektu: tf install'
