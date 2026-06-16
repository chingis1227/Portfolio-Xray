$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Get-ProjectPython {
    $venvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        return @($venvPython)
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @("py", "-3")
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @("python")
    }
    throw "Python not found. Checked .\.venv\Scripts\python.exe, py -3, and python."
}

function Invoke-QaStep {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$WorkingDirectory,
        [Parameter(Mandatory = $true)][string[]]$Command
    )

    Write-Host ""
    Write-Host "==> $Name" -ForegroundColor Cyan
    Write-Host "cwd: $WorkingDirectory"
    Write-Host ("cmd: " + ($Command -join " "))

    Push-Location $WorkingDirectory
    try {
        $exe = $Command[0]
        $args = @()
        if ($Command.Count -gt 1) {
            $args = $Command[1..($Command.Count - 1)]
        }
        & $exe @args
        if ($LASTEXITCODE -ne 0) {
            throw "Step failed with exit code $LASTEXITCODE`: $Name"
        }
    }
    finally {
        Pop-Location
    }
}

$Python = @(Get-ProjectPython)

Write-Host "Portfolio MRI contract QA gate" -ForegroundColor Green
Write-Host "This gate intentionally skips networked/live checks and full pytest."
Write-Host "Repository: $RepoRoot"

Invoke-QaStep "Candidate factory/comparison contract pytest" $RepoRoot ($Python + @(
    "-m", "pytest",
    "tests\test_candidate_factory_contract.py",
    "tests\test_candidate_comparison_contract.py",
    "tests\test_candidate_factory.py",
    "tests\test_candidate_comparison.py",
    "-k",
    "not test_current_unavailable_in_optimize_mode",
    "-q",
    "--basetemp=tmp\qa_contracts_pytest"
))

Write-Host ""
Write-Host "Contract QA gate passed." -ForegroundColor Green
