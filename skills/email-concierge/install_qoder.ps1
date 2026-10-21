param(
    [switch]$NoSetup,
    [switch]$FirstInstall
)

$ErrorActionPreference = "Stop"
$sourceDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$skillsDir = Join-Path $env:USERPROFILE ".qoder\skills"
$targetDir = Join-Path $skillsDir "email-concierge"
$markerFile = Join-Path $targetDir "state\.setup_completed.json"

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) { $pythonCommand = Get-Command py -ErrorAction SilentlyContinue }
if (-not $pythonCommand) { throw "Python 3.10+ was not found. Install Python from https://www.python.org/downloads/windows/ and rerun this script." }
$python = $pythonCommand.Source
$setupFlag = if ($NoSetup) { "--no-setup" } else { "--setup" }

# Auto-detect first install unless the caller explicitly passed -FirstInstall.
$isFirstInstall = $FirstInstall -or (-not (Test-Path $markerFile))

$installArgs = @("--target", "qoder", "--destination", $skillsDir, $setupFlag, "--json")
if ($isFirstInstall) { $installArgs += "--first-install" }

$result = & $python (Join-Path $sourceDir "install_skill.py") @installArgs
$exitCode = $LASTEXITCODE
if ($result) { $result | Write-Output }
if ($exitCode -ne 0) { exit $exitCode }

Write-Host "Installed Qoder skill to $targetDir"
if ($NoSetup) {
    Write-Host "Installed without dependencies. Run setup later: $python `"$targetDir\setup_auto.py`" --project-dir `"$targetDir`""
}
