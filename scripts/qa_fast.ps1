$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$FrontendRoot = Join-Path $RepoRoot "frontend"

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

Write-Host "Portfolio MRI fast QA gate" -ForegroundColor Green
Write-Host "This gate intentionally skips full pytest, live E2E, frontend build, and frontend smoke."
Write-Host "Repository: $RepoRoot"

Invoke-QaStep "Docs verification" $RepoRoot ($Python + @("scripts\verify_docs.py"))

Invoke-QaStep "Staged Run Diagnosis compatibility guard" $RepoRoot ($Python + @(
    "scripts\verify_staged_route_compatibility.py"
))

Invoke-QaStep "FastAPI/frontend contract governance" $RepoRoot ($Python + @(
    "scripts\verify_fastapi_contract_governance.py"
))

Invoke-QaStep "Backend fast offline pytest" $RepoRoot ($Python + @(
    "-m", "pytest",
    "tests\test_portfolio_review_workflow.py",
    "tests\test_mvp_pipeline_offline.py",
    "tests\test_portfolio_first_e2e_offline.py",
    "tests\test_product_bundle_paths.py",
    "tests\test_ai_commentary_context.py",
    "tests\test_light_monitoring_summary.py",
    "-q",
    "--basetemp=tmp\qa_fast_pytest"
))

Invoke-QaStep "Frontend typecheck" $FrontendRoot @("npm.cmd", "run", "typecheck")
Invoke-QaStep "Frontend API route tests" $FrontendRoot @("npm.cmd", "run", "test:api")

Write-Host ""
Write-Host "Fast QA gate passed." -ForegroundColor Green
