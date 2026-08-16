$ErrorActionPreference = 'Stop'

$Repo = 'https://github.com/badrpk/xerus.git'
$Dest = if ($env:XERUS_INSTALL_HOME) { $env:XERUS_INSTALL_HOME } else { Join-Path $HOME '.local\share\xerus' }
$Venv = Join-Path $Dest '.venv'
$BinDir = if ($env:XERUS_BIN_DIR) { $env:XERUS_BIN_DIR } else { Join-Path $HOME '.local\bin' }

if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'git is required' }
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw 'python is required' }

if (Test-Path (Join-Path $Dest '.git')) {
    $dirty = git -C $Dest status --porcelain
    if ($dirty) { throw "Refusing update: $Dest has local changes" }
    git -C $Dest fetch origin --tags --prune
    git -C $Dest checkout main
    git -C $Dest pull --ff-only origin main
} elseif (Test-Path $Dest) {
    throw "Refusing overwrite: $Dest exists and is not a Git repository"
} else {
    git clone --branch main $Repo $Dest
}

python -m venv $Venv
$Py = Join-Path $Venv 'Scripts\python.exe'
& $Py -m pip install --upgrade pip
& $Py -m pip install $Dest

New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
$Cmd = Join-Path $BinDir 'xerus.cmd'
$XerusExe = Join-Path $Venv 'Scripts\xerus.exe'
"@echo off`r`n`"$XerusExe`" %*`r`n" | Set-Content -Encoding ASCII $Cmd

Write-Host "Xerus installed at $Dest"
Write-Host "CLI: $Cmd"
Write-Host 'Try: xerus status'
