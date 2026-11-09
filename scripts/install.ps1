# Installs the `tf` command (the factory launcher) on Windows. `tf install` then installs the factory in a project.
#
#   irm <url of this file> | iex
#   powershell -ExecutionPolicy Bypass -File scripts\install.ps1      # from a clone of the repository
#
# Variables (optional): TF_REPO (default https://github.com/dbqm45/tf.git), TF_BIN (default ~\.local\bin),
# TF_PYTHON (default py, python3, python), TF_GIT (default git), TF_NO_PATH (do not ask about PATH). See docs/setup.md.
# The script installs only tf and tf.cmd in TF_BIN; it changes PATH only after you confirm.
# ASCII only: Windows PowerShell 5.1 does not read `irm | iex` as UTF-8, so other characters would be garbled.
$ErrorActionPreference = 'Stop'

$Repo = if ($env:TF_REPO) { $env:TF_REPO } else { 'https://github.com/dbqm45/tf.git' }
$Bin = if ($env:TF_BIN) { $env:TF_BIN } else { Join-Path $HOME '.local\bin' }
$Git = if ($env:TF_GIT) { $env:TF_GIT } else { 'git' }

# throw, not exit: with `irm | iex` exit would close the PowerShell window
function Fail($msg) { throw "ERROR: $msg" }

# Python 3.9+ (the Microsoft Store alias does not run Python and fails the version check)
$Py = $null
$cands = if ($env:TF_PYTHON) { @($env:TF_PYTHON) } else { @('py', 'python3', 'python') }
foreach ($c in $cands) {
    if (Get-Command $c -ErrorAction SilentlyContinue) {
        & $c -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) { $Py = $c; break }
    }
}
if (-not $Py) { Fail "Python 3.9+ not found (tried: $($cands -join ', ')). Install it: winget install Python.Python.3.12 or https://www.python.org/downloads/" }

if (-not (Get-Command $Git -ErrorAction SilentlyContinue)) { Fail "git not found ($Git). Install it: winget install Git.Git or https://git-scm.com/downloads" }

$Tmp = Join-Path ([IO.Path]::GetTempPath()) ("tf-install." + [Guid]::NewGuid().ToString('N'))
try {
    Write-Host "> Downloading the factory from $Repo"
    & $Git clone -q --depth 1 $Repo (Join-Path $Tmp 'tf')
    if ($LASTEXITCODE -ne 0) { Fail "Could not download $Repo. A private repository needs git access (gh auth login or Git Credential Manager)." }
    & $Py (Join-Path $Tmp 'tf\core\factory\tf.py') --install-launcher --repo $Repo --bin $Bin
    if ($LASTEXITCODE -ne 0) { Fail 'Installing the launcher failed.' }
} finally {
    if (Test-Path $Tmp) { Remove-Item -Recurse -Force $Tmp }
}

$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
if (-not (($userPath -split ';') -contains $Bin) -and -not $env:TF_NO_PATH -and [Environment]::UserInteractive) {
    $ans = Read-Host "Add $Bin to your user PATH? [y/N]"
    if ($ans -match '^[yY]') {
        [Environment]::SetEnvironmentVariable('Path', "$userPath;$Bin", 'User')
        Write-Host 'Added to PATH. Open a new terminal window.'
    } else {
        Write-Host "Note: add $Bin to PATH to run tf from any directory."
    }
}
Write-Host 'Done. In your project directory run: tf install'
