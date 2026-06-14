param(
    [switch]$LocalOnly,
    [switch]$Staging,
    [switch]$SkipLive,
    [int]$ScenarioLimit = 5
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$FrontendRoot = Join-Path $RepoRoot "frontend"
$Timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$RunRoot = Join-Path $RepoRoot "output\qa_runs\$Timestamp"
$SummaryJson = Join-Path $RunRoot "qa-summary.json"
$SummaryMd = Join-Path $RunRoot "qa-summary.md"
$FindingsJson = Join-Path $RunRoot "qa-findings.json"
$FindingsMd = Join-Path $RunRoot "qa-findings.md"
$ReadinessJson = Join-Path $RunRoot "qa-release-readiness.json"
$ReadinessMd = Join-Path $RunRoot "qa-release-readiness.md"
$LogsRoot = Join-Path $RunRoot "logs"

New-Item -ItemType Directory -Force -Path $RunRoot | Out-Null
New-Item -ItemType Directory -Force -Path $LogsRoot | Out-Null

$Steps = New-Object System.Collections.Generic.List[object]
$Findings = New-Object System.Collections.Generic.List[object]
$RunStartedAt = (Get-Date).ToUniversalTime().ToString("o")

function Get-ProjectPython {
    $venvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) { return @($venvPython) }
    if (Get-Command py -ErrorAction SilentlyContinue) { return @("py", "-3") }
    throw "Python not found. Expected .\.venv\Scripts\python.exe or py -3."
}

function Get-LogSafeName {
    param([Parameter(Mandatory = $true)][string]$Name)
    $safe = $Name.ToLowerInvariant() -replace "[^a-z0-9]+", "-"
    return $safe.Trim("-")
}

function Add-QaStep {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$Status,
        [Parameter(Mandatory = $true)][string]$Classification,
        [Parameter(Mandatory = $true)][string]$Message,
        [string]$Details = "",
        [string]$Command = "",
        [string]$WorkingDirectory = "",
        [int]$ExitCode = 0,
        [string]$LogPath = ""
    )
    $Steps.Add([pscustomobject]@{
        name = $Name
        status = $Status
        classification = $Classification
        message = $Message
        details = $Details
        command = $Command
        working_directory = $WorkingDirectory
        exit_code = $ExitCode
        log_path = $LogPath
        completed_at = (Get-Date).ToUniversalTime().ToString("o")
    }) | Out-Null
}

function Add-QaFinding {
    param(
        [Parameter(Mandatory = $true)][string]$Id,
        [Parameter(Mandatory = $true)][string]$Severity,
        [Parameter(Mandatory = $true)][string]$Status,
        [Parameter(Mandatory = $true)][string]$Classification,
        [Parameter(Mandatory = $true)][string]$Subsystem,
        [Parameter(Mandatory = $true)][string]$CommandOrRoute,
        [Parameter(Mandatory = $true)][string]$Observed,
        [Parameter(Mandatory = $true)][string]$Expected,
        [string[]]$EvidencePaths = @(),
        [string]$SuspectedCause = "",
        [string]$RecommendedNextAction = "",
        [string]$OwnerArea = "",
        [string]$ReproductionCommand = "",
        [string[]]$Warnings = @(),
        [int]$RetryCount = 0
    )
    $Findings.Add([pscustomobject]@{
        id = $Id
        severity = $Severity
        status = $Status
        classification = $Classification
        subsystem = $Subsystem
        command_or_route = $CommandOrRoute
        observed = $Observed
        expected = $Expected
        evidence_paths = @($EvidencePaths)
        suspected_cause = $SuspectedCause
        recommended_next_action = $RecommendedNextAction
        owner_area = $OwnerArea
        reproduction_command = $ReproductionCommand
        warnings = @($Warnings)
        retry_count = $RetryCount
        recorded_at = (Get-Date).ToUniversalTime().ToString("o")
    }) | Out-Null
}

function Invoke-ProjectPythonCode {
    param([Parameter(Mandatory = $true)][string]$Code)
    $python = @(Get-ProjectPython)
    $exe = $python[0]
    $args = @()
    if ($python.Count -gt 1) { $args = $python[1..($python.Count - 1)] }
    $scriptPath = Join-Path $RunRoot "local_fastapi_openapi_guard.py"
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($scriptPath, $Code, $utf8NoBom)
    Push-Location $RepoRoot
    try {
        & $exe @args $scriptPath
        $exitCode = $LASTEXITCODE
    }
    finally {
        Pop-Location
        Remove-Item -LiteralPath $scriptPath -Force -ErrorAction SilentlyContinue
    }
    if ($exitCode -ne 0) { throw "Python check failed with exit code $exitCode." }
}

function Invoke-QaCommand {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$WorkingDirectory,
        [Parameter(Mandatory = $true)][string[]]$Command,
        [string]$KnownFailureReason = "",
        [string]$Subsystem = "qa",
        [string]$Severity = "P2",
        [int]$MaxAttempts = 1
    )
    Write-Host ""
    Write-Host "==> $Name" -ForegroundColor Cyan
    Write-Host "cwd: $WorkingDirectory"
    Write-Host ("cmd: " + ($Command -join " "))

    $safeName = Get-LogSafeName -Name $Name
    $logPath = Join-Path $LogsRoot "$safeName.log"
    $commandText = $Command -join " "
    $started = Get-Date
    $output = New-Object System.Collections.Generic.List[string]
    $exitCode = 0
    $attemptsUsed = 0

    $output.Add("# $Name") | Out-Null
    $output.Add("cwd: $WorkingDirectory") | Out-Null
    $output.Add("cmd: $commandText") | Out-Null
    $output.Add("started_at: $($started.ToUniversalTime().ToString("o"))") | Out-Null

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        $attemptsUsed = $attempt
        $output.Add("") | Out-Null
        $output.Add("attempt: $attempt/$MaxAttempts") | Out-Null

        Push-Location $WorkingDirectory
        try {
            $exe = $Command[0]
            $args = @()
            if ($Command.Count -gt 1) { $args = $Command[1..($Command.Count - 1)] }
            & $exe @args 2>&1 | ForEach-Object {
                $line = $_.ToString()
                $output.Add($line) | Out-Null
                Write-Host $line
            }
            $exitCode = if ($null -eq $LASTEXITCODE) { 0 } else { $LASTEXITCODE }
        }
        catch {
            $exitCode = if ($null -eq $LASTEXITCODE -or $LASTEXITCODE -eq 0) { 1 } else { $LASTEXITCODE }
            $output.Add($_.Exception.Message) | Out-Null
            Write-Host $_.Exception.Message -ForegroundColor Red
        }
        finally { Pop-Location }

        $output.Add("attempt_exit_code: $exitCode") | Out-Null
        if ($exitCode -eq 0) { break }
        if ($attempt -lt $MaxAttempts) {
            $retryMessage = "Retrying after exit code $exitCode."
            $output.Add($retryMessage) | Out-Null
            Write-Host $retryMessage -ForegroundColor Yellow
        }
    }

    $completed = Get-Date
    $duration = [Math]::Round(($completed - $started).TotalSeconds, 1)
    $output.Add("") | Out-Null
    $output.Add("completed_at: $($completed.ToUniversalTime().ToString("o"))") | Out-Null
    $output.Add("duration_seconds: $duration") | Out-Null
    $output.Add("attempts_used: $attemptsUsed") | Out-Null
    $output.Add("exit_code: $exitCode") | Out-Null
    $output | Set-Content -Path $logPath -Encoding UTF8

    if ($exitCode -eq 0) {
        Add-QaStep -Name $Name -Status "passed" -Classification "passed" -Message "Command passed." -Command $commandText -WorkingDirectory $WorkingDirectory -ExitCode $exitCode -LogPath $logPath -Details "duration_seconds=$duration; attempts_used=$attemptsUsed"
        if ($attemptsUsed -gt 1) {
            Add-QaFinding `
                -Id ("QA-" + (Get-LogSafeName -Name $Name).ToUpperInvariant() + "-RETRIED") `
                -Severity $Severity `
                -Status "passed" `
                -Classification "retried_passed" `
                -Subsystem $Subsystem `
                -CommandOrRoute $commandText `
                -Observed "Command passed after $attemptsUsed attempts." `
                -Expected "Command is stable and exits 0 on the first attempt." `
                -EvidencePaths @($logPath) `
                -RecommendedNextAction "Review the log if this retry pattern repeats in future QA runs." `
                -OwnerArea $Subsystem `
                -ReproductionCommand $commandText `
                -RetryCount $attemptsUsed
        }
        return [pscustomobject]@{
            name = $Name
            status = "passed"
            classification = "passed"
            exit_code = $exitCode
            log_path = $logPath
            command = $commandText
            duration_seconds = $duration
            attempts_used = $attemptsUsed
        }
    }

    $classification = if ([string]::IsNullOrWhiteSpace($KnownFailureReason)) { "new_failure" } else { "known_failure" }
    Add-QaStep -Name $Name -Status "failed" -Classification $classification -Message "Command failed with exit code $exitCode." -Details $KnownFailureReason -Command $commandText -WorkingDirectory $WorkingDirectory -ExitCode $exitCode -LogPath $logPath
    Add-QaFinding `
        -Id ("QA-" + (Get-LogSafeName -Name $Name).ToUpperInvariant()) `
        -Severity $Severity `
        -Status "failed" `
        -Classification $classification `
        -Subsystem $Subsystem `
        -CommandOrRoute $commandText `
        -Observed "Exit code $exitCode. See log for full output." `
        -Expected "Command exits 0 in the exhaustive local QA gate." `
        -EvidencePaths @($logPath) `
        -SuspectedCause $KnownFailureReason `
        -RecommendedNextAction "Review the command log and fix the owning subsystem before release readiness." `
        -OwnerArea $Subsystem `
        -ReproductionCommand $commandText `
        -RetryCount $attemptsUsed
    return [pscustomobject]@{
        name = $Name
        status = "failed"
        classification = $classification
        exit_code = $exitCode
        log_path = $logPath
        command = $commandText
        duration_seconds = $duration
        attempts_used = $attemptsUsed
    }
}

function Normalize-BaseUrl {
    param([Parameter(Mandatory = $true)][string]$Url)
    return $Url.TrimEnd("/")
}

function Invoke-JsonRequest {
    param(
        [Parameter(Mandatory = $true)][string]$Method,
        [Parameter(Mandatory = $true)][string]$Url,
        [object]$Body = $null
    )
    try {
        if ($null -eq $Body) { return Invoke-RestMethod -Method $Method -Uri $Url -TimeoutSec 45 }
        $json = $Body | ConvertTo-Json -Depth 20
        return Invoke-RestMethod -Method $Method -Uri $Url -ContentType "application/json" -Body $json -TimeoutSec 120
    }
    catch {
        $response = $_.Exception.Response
        $statusCode = $null
        if ($response -and $response.StatusCode) { $statusCode = [int]$response.StatusCode }
        $classification = if ($statusCode -eq 404 -or $statusCode -eq 405) { "frontend_backend_version_mismatch" } else { "new_failure" }
        throw [System.Exception]::new("HTTP request failed ($classification, status=$statusCode): $Method $Url. $($_.Exception.Message)")
    }
}

function Invoke-JsonRequestAllowFailure {
    param(
        [Parameter(Mandatory = $true)][string]$Method,
        [Parameter(Mandatory = $true)][string]$Url,
        [object]$Body = $null,
        [int]$TimeoutSec = 120
    )
    $json = $null
    $headers = @{}
    if ($null -ne $Body) {
        $json = $Body | ConvertTo-Json -Depth 20
        $headers["Content-Type"] = "application/json"
    }
    try {
        $response = if ($null -eq $Body) {
            Invoke-WebRequest -Method $Method -Uri $Url -TimeoutSec $TimeoutSec
        } else {
            Invoke-WebRequest -Method $Method -Uri $Url -Headers $headers -Body $json -TimeoutSec $TimeoutSec
        }
        $text = [string]$response.Content
        $bodyObject = if ([string]::IsNullOrWhiteSpace($text)) { $null } else { $text | ConvertFrom-Json }
        return [pscustomobject]@{ ok = ($response.StatusCode -ge 200 -and $response.StatusCode -lt 300); status = [int]$response.StatusCode; body = $bodyObject; text = $text }
    }
    catch {
        $statusCode = 0
        $text = ""
        if ($_.Exception.Response) {
            $statusCode = [int]$_.Exception.Response.StatusCode
            try {
                $stream = $_.Exception.Response.GetResponseStream()
                if ($stream) {
                    $reader = New-Object System.IO.StreamReader($stream)
                    $text = $reader.ReadToEnd()
                }
            } catch { $text = "" }
        }
        if ([string]::IsNullOrWhiteSpace($text) -and $_.ErrorDetails -and $_.ErrorDetails.Message) {
            $text = [string]$_.ErrorDetails.Message
        }
        $bodyObject = $null
        if (-not [string]::IsNullOrWhiteSpace($text)) {
            try { $bodyObject = $text | ConvertFrom-Json } catch { $bodyObject = [pscustomobject]@{ raw_text = $text } }
        }
        return [pscustomobject]@{ ok = $false; status = $statusCode; body = $bodyObject; text = $text }
    }
}

function Test-OpenApiHasStagedPost {
    param(
        [Parameter(Mandatory = $true)][object]$OpenApiSchema,
        [Parameter(Mandatory = $true)][string]$ContextLabel
    )
    $paths = $OpenApiSchema.paths
    if ($null -eq $paths) { throw "$ContextLabel OpenAPI schema has no paths object." }
    $staged = $paths."/api/v1/reviews/staged"
    if ($null -eq $staged -or $null -eq $staged.post) { throw "$ContextLabel OpenAPI schema does not expose POST /api/v1/reviews/staged." }
}

function Get-TextValue {
    param([object]$Value)
    if ($null -eq $Value) { return "" }
    $text = [string]$Value
    if ([string]::IsNullOrWhiteSpace($text)) { return "" }
    return $text.Trim()
}

function Get-LineageValue {
    param(
        [object]$Body,
        [Parameter(Mandatory = $true)][string]$Key
    )
    if ($null -eq $Body) { return "" }
    $envelope = if ($Body.fastapi_envelope) { $Body.fastapi_envelope } else { $Body }
    if ($envelope.lineage -and $envelope.lineage.$Key) { return Get-TextValue $envelope.lineage.$Key }
    if ($Body.$Key) { return Get-TextValue $Body.$Key }
    if ($envelope.$Key) { return Get-TextValue $envelope.$Key }
    return ""
}

function Test-LineageValue {
    param(
        [Parameter(Mandatory = $true)][object]$Body,
        [Parameter(Mandatory = $true)][hashtable]$Expected,
        [Parameter(Mandatory = $true)][string]$Label
    )
    foreach ($key in $Expected.Keys) {
        $expectedValue = Get-TextValue $Expected[$key]
        if ([string]::IsNullOrWhiteSpace($expectedValue)) { continue }
        $actualValue = Get-LineageValue -Body $Body -Key $key
        if (-not [string]::IsNullOrWhiteSpace($actualValue) -and $actualValue -ne $expectedValue) {
            throw "$Label lineage $key mismatch: expected $expectedValue, got $actualValue."
        }
    }
}

function Get-LaunchpadCards {
    param([object]$RecoveryBody)
    $reviewResult = if ($RecoveryBody.review_result) { $RecoveryBody.review_result } else { $RecoveryBody }
    $outputs = $reviewResult.outputs
    $cards = $null
    if ($outputs -and $outputs.candidate_launchpad -and $outputs.candidate_launchpad.cards) {
        $cards = $outputs.candidate_launchpad.cards
    }
    if ($null -eq $cards) { return @() }
    if ($cards -is [System.Array]) { return @($cards) }
    return @($cards)
}

function Select-LaunchpadCard {
    param([object[]]$Cards)
    foreach ($card in $Cards) {
        $setup = $card.candidate_setup
        if ($card.generates_portfolio -eq $true -or $card.candidate_generation_allowed -eq $true -or ($setup -and $setup.candidate_generation_allowed -eq $true) -or -not [string]::IsNullOrWhiteSpace((Get-TextValue $card.default_method))) {
            return $card
        }
    }
    if ($Cards.Count -gt 0) { return $Cards[0] }
    return $null
}

function Test-StagedDiagnosisReady {
    param(
        [Parameter(Mandatory = $true)][string]$FrontendUrl,
        [Parameter(Mandatory = $true)][string]$ReviewId
    )
    $timeoutSeconds = 900
    if ($env:PMRI_QA_STAGING_TIMEOUT_SECONDS -match "^\d+$") { $timeoutSeconds = [int]$env:PMRI_QA_STAGING_TIMEOUT_SECONDS }
    $deadline = (Get-Date).AddSeconds($timeoutSeconds)
    $latest = $null
    while ((Get-Date) -lt $deadline) {
        $status = Invoke-JsonRequest -Method "GET" -Url "$FrontendUrl/api/portfolio/review/status?reviewId=$([uri]::EscapeDataString($ReviewId))"
        $latest = $status
        if ($status.safe_error -or $status.status -eq "failed") {
            throw "Staged diagnosis failed for $ReviewId. Status payload: $(($status | ConvertTo-Json -Depth 12))"
        }
        $stages = $status.stages
        $ready = $false
        if ($stages) {
            $ready = $true
            foreach ($stageName in @("xray", "stress", "problem_classification", "launchpad_builder")) {
                $row = $stages.$stageName
                if (-not ($row -and ($row.status -eq "completed" -or $row.status -eq "partial"))) {
                    $ready = $false
                    break
                }
            }
            if (-not $ready) {
                $ready = @("diagnosis", "evidence", "problem_classification", "launchpad_builder") | ForEach-Object {
                $row = $stages.$_
                ($row -and ($row.status -eq "completed" -or $row.status -eq "partial"))
                } | Where-Object { $_ -eq $false } | Measure-Object | ForEach-Object { $_.Count -eq 0 }
            }
        }
        if ($ready) { return $status }
        Start-Sleep -Seconds 2
    }
    throw "Timed out waiting for staging diagnosis chain for $ReviewId. Last status: $(($latest | ConvertTo-Json -Depth 12))"
}

function New-StagingPortfolioPayload {
    return [ordered]@{
        investor_currency = "USD"
        mode = "demo_qa"
        client_fit = [ordered]@{
            preset_id = "balanced"
            target_return_range = [ordered]@{ min = 0.00; max = 0.25 }
            target_vol_range = [ordered]@{ min = 0.02; max = 0.30 }
            target_max_drawdown_pct = -0.60
            horizon_years = 7
            source = "questionnaire"
            source_quality = "high"
        }
        holdings = @(
            [ordered]@{ type = "instrument"; ticker = "SPY"; weight = 80 },
            [ordered]@{ type = "cash"; currency = "USD"; weight = 20 }
        )
    }
}

function Test-EnvironmentReadiness {
    Write-Host "==> Environment readiness" -ForegroundColor Cyan
    $messages = New-Object System.Collections.Generic.List[string]
    $python = @(Get-ProjectPython)
    $messages.Add("python=$($python -join ' ')") | Out-Null
    foreach ($commandName in @("git", "npm.cmd", "node")) {
        $cmd = Get-Command $commandName -ErrorAction SilentlyContinue
        if (-not $cmd) { throw "Required command is not available on PATH: $commandName" }
        $messages.Add("$commandName=$($cmd.Source)") | Out-Null
    }
    foreach ($path in @("scripts\qa_fast.ps1", "scripts\qa_contracts.ps1", "scripts\verify_fastapi_contract_governance.py", "frontend\package.json")) {
        if (-not (Test-Path (Join-Path $RepoRoot $path))) { throw "Required path is missing: $path" }
    }
    Add-QaStep -Name "Environment readiness" -Status "passed" -Classification "passed" -Message "Required local commands and QA entrypoints are available." -Details ($messages -join "; ")
}

function Test-LocalFastApiOpenApi {
    Write-Host "==> Local FastAPI staged OpenAPI guard" -ForegroundColor Cyan
    $code = @(
        "from pathlib import Path",
        "import sys",
        "",
        "repo_root = Path(__file__).resolve().parents[3]",
        "sys.path.insert(0, str(repo_root))",
        "",
        "from src.api.app import app",
        "schema = app.openapi()",
        "staged = schema.get('paths', {}).get('/api/v1/reviews/staged', {})",
        "if 'post' not in staged:",
        "    raise SystemExit('POST /api/v1/reviews/staged is missing from local FastAPI OpenAPI.')",
        "print('local FastAPI OpenAPI includes POST /api/v1/reviews/staged')"
    ) -join [Environment]::NewLine
    Invoke-ProjectPythonCode -Code $code
    Add-QaStep `
        -Name "Local FastAPI staged OpenAPI guard" `
        -Status "passed" `
        -Classification "passed" `
        -Message "Local FastAPI OpenAPI exposes POST /api/v1/reviews/staged."
    Add-QaFinding `
        -Id "QA-RUN-DIAGNOSIS-STAGED-OPENAPI" `
        -Severity "P0" `
        -Status "passed" `
        -Classification "passed" `
        -Subsystem "FastAPI" `
        -CommandOrRoute "POST /api/v1/reviews/staged" `
        -Observed "Local FastAPI OpenAPI contains POST /api/v1/reviews/staged." `
        -Expected "Run Diagnosis compatibility route is present." `
        -RecommendedNextAction "Keep this guard green before release."
}

function Test-StagingRunDiagnosis {
    Write-Host "==> Staging Run Diagnosis compatibility guard" -ForegroundColor Cyan
    if ($env:PMRI_QA_ALLOW_STAGING -ne "1") {
        Add-QaStep -Name "Staging Run Diagnosis compatibility guard" -Status "skipped" -Classification "skipped_not_configured" -Message "Set PMRI_QA_ALLOW_STAGING=1 with PMRI_QA_FRONTEND_URL and PMRI_QA_FASTAPI_URL to enable staging checks."
        Add-QaFinding -Id "QA-STAGING-RUN-DIAGNOSIS-SKIPPED" -Severity "P0" -Status "skipped" -Classification "skipped_not_configured" -Subsystem "staging" -CommandOrRoute "POST /api/portfolio/diagnose" -Observed "Staging guard was not run because PMRI_QA_ALLOW_STAGING was not 1." -Expected "Release readiness runs configure staging URLs and opt in explicitly." -RecommendedNextAction "Set PMRI_QA_ALLOW_STAGING=1, PMRI_QA_FRONTEND_URL, and PMRI_QA_FASTAPI_URL before staging release readiness." -OwnerArea "staging"
        return
    }
    if ([string]::IsNullOrWhiteSpace($env:PMRI_QA_FRONTEND_URL) -or [string]::IsNullOrWhiteSpace($env:PMRI_QA_FASTAPI_URL)) {
        Add-QaStep -Name "Staging Run Diagnosis compatibility guard" -Status "skipped" -Classification "skipped_not_configured" -Message "PMRI_QA_FRONTEND_URL and PMRI_QA_FASTAPI_URL are required for staging checks."
        Add-QaFinding -Id "QA-STAGING-RUN-DIAGNOSIS-SKIPPED" -Severity "P0" -Status "skipped" -Classification "skipped_not_configured" -Subsystem "staging" -CommandOrRoute "POST /api/portfolio/diagnose" -Observed "Staging guard was not run because one or more staging URLs are missing." -Expected "Release readiness runs configure both frontend and FastAPI staging URLs." -RecommendedNextAction "Set PMRI_QA_FRONTEND_URL and PMRI_QA_FASTAPI_URL." -OwnerArea "staging"
        return
    }
    $frontendUrl = Normalize-BaseUrl -Url $env:PMRI_QA_FRONTEND_URL
    $fastApiUrl = Normalize-BaseUrl -Url $env:PMRI_QA_FASTAPI_URL
    $details = "frontend_url=$frontendUrl; fastapi_url=$fastApiUrl"
    try {
        [void](Invoke-JsonRequest -Method "GET" -Url "$fastApiUrl/api/v1/health")
        $openApi = Invoke-JsonRequest -Method "GET" -Url "$fastApiUrl/openapi.json"
        Test-OpenApiHasStagedPost -OpenApiSchema $openApi -ContextLabel "Staging FastAPI"
        $payload = New-StagingPortfolioPayload
        $diagnosis = Invoke-JsonRequest -Method "POST" -Url "$frontendUrl/api/portfolio/diagnose" -Body $payload
        if ([string]::IsNullOrWhiteSpace($diagnosis.review_id)) { throw "Frontend diagnosis response did not include review_id." }
        if ($diagnosis.status -eq "failed") { throw "Frontend diagnosis returned status=failed for a safe staging smoke payload." }
        Add-QaStep -Name "Staging Run Diagnosis compatibility guard" -Status "passed" -Classification "passed" -Message "Staging frontend and FastAPI are compatible for staged Run Diagnosis." -Details "$details; review_id=$($diagnosis.review_id); status=$($diagnosis.status)"
        Add-QaFinding `
            -Id "QA-STAGING-RUN-DIAGNOSIS" `
            -Severity "P0" `
            -Status "passed" `
            -Classification "passed" `
            -Subsystem "staging" `
            -CommandOrRoute "POST /api/portfolio/diagnose and POST /api/v1/reviews/staged" `
            -Observed "Staging diagnosis returned review_id=$($diagnosis.review_id), status=$($diagnosis.status)." `
            -Expected "Staging frontend returns a review_id and uses a FastAPI backend that supports the staged endpoint." `
            -RecommendedNextAction "Keep frontend and FastAPI deployments version-aligned." `
            -OwnerArea "staging"
    }
    catch {
        $message = $_.Exception.Message
        $classification = if ($message -match "frontend_backend_version_mismatch|405|404|/api/v1/reviews/staged") { "frontend_backend_version_mismatch" } else { "new_failure" }
        Add-QaStep -Name "Staging Run Diagnosis compatibility guard" -Status "failed" -Classification $classification -Message $message -Details $details
        Add-QaFinding `
            -Id "QA-STAGING-RUN-DIAGNOSIS" `
            -Severity "P0" `
            -Status "failed" `
            -Classification $classification `
            -Subsystem "staging" `
            -CommandOrRoute "POST /api/portfolio/diagnose and POST /api/v1/reviews/staged" `
            -Observed $message `
            -Expected "Staging frontend returns a review_id and uses a FastAPI backend that supports the staged endpoint." `
            -RecommendedNextAction "Deploy matching frontend and FastAPI versions or update the configured backend URL."
    }
}

function Test-StagingJourneyReadiness {
    Write-Host "==> Staging route-chain journey guard" -ForegroundColor Cyan
    if ($env:PMRI_QA_ALLOW_STAGING -ne "1") {
        Add-QaStep -Name "Staging route-chain journey guard" -Status "skipped" -Classification "skipped_not_configured" -Message "Set PMRI_QA_ALLOW_STAGING=1 with staging URLs to enable the route-chain check."
        Add-QaFinding -Id "QA-STAGING-JOURNEY-SKIPPED" -Severity "P0" -Status "skipped" -Classification "skipped_not_configured" -Subsystem "staging" -CommandOrRoute "diagnose -> recover -> builder -> candidate -> comparison -> verdict -> report" -Observed "Staging route-chain check was skipped because staging was not explicitly enabled." -Expected "Release readiness runs the staging route chain against configured frontend and FastAPI deployments." -RecommendedNextAction "Run .\scripts\qa_exhaustive.cmd -Staging with PMRI_QA_ALLOW_STAGING=1 and staging URLs." -OwnerArea "staging"
        return
    }
    if ([string]::IsNullOrWhiteSpace($env:PMRI_QA_FRONTEND_URL) -or [string]::IsNullOrWhiteSpace($env:PMRI_QA_FASTAPI_URL)) {
        Add-QaStep -Name "Staging route-chain journey guard" -Status "skipped" -Classification "skipped_not_configured" -Message "PMRI_QA_FRONTEND_URL and PMRI_QA_FASTAPI_URL are required for staging route-chain checks."
        Add-QaFinding -Id "QA-STAGING-JOURNEY-SKIPPED" -Severity "P0" -Status "skipped" -Classification "skipped_not_configured" -Subsystem "staging" -CommandOrRoute "diagnose -> recover -> builder -> candidate -> comparison -> verdict -> report" -Observed "Staging route-chain check was skipped because one or more staging URLs are missing." -Expected "Release readiness runs the staging route chain against configured frontend and FastAPI deployments." -RecommendedNextAction "Set PMRI_QA_FRONTEND_URL and PMRI_QA_FASTAPI_URL." -OwnerArea "staging"
        return
    }

    $frontendUrl = Normalize-BaseUrl -Url $env:PMRI_QA_FRONTEND_URL
    $fastApiUrl = Normalize-BaseUrl -Url $env:PMRI_QA_FASTAPI_URL
    $details = "frontend_url=$frontendUrl; fastapi_url=$fastApiUrl"
    $evidencePath = Join-Path $RunRoot "staging-journey.json"
    $routeEvidence = [ordered]@{
        frontend_url = $frontendUrl
        fastapi_url = $fastApiUrl
        started_at = (Get-Date).ToUniversalTime().ToString("o")
        stages = [ordered]@{}
    }

    try {
        [void](Invoke-JsonRequest -Method "GET" -Url "$fastApiUrl/api/v1/health")
        $openApi = Invoke-JsonRequest -Method "GET" -Url "$fastApiUrl/openapi.json"
        Test-OpenApiHasStagedPost -OpenApiSchema $openApi -ContextLabel "Staging FastAPI"
        $routeEvidence.stages.fastapi_openapi = [ordered]@{ status = "passed"; route = "POST /api/v1/reviews/staged" }

        $diagnosis = Invoke-JsonRequest -Method "POST" -Url "$frontendUrl/api/portfolio/diagnose" -Body (New-StagingPortfolioPayload)
        $reviewId = Get-TextValue $diagnosis.review_id
        if ([string]::IsNullOrWhiteSpace($reviewId)) { $reviewId = Get-LineageValue -Body $diagnosis -Key "review_id" }
        if ([string]::IsNullOrWhiteSpace($reviewId)) { throw "Staging diagnosis response did not include review_id." }
        if ($diagnosis.status -eq "failed") { throw "Staging diagnosis returned status=failed." }
        $routeEvidence.review_id = $reviewId
        $routeEvidence.stages.diagnosis_start = [ordered]@{ status = "passed"; review_id = $reviewId; response_status = $diagnosis.status }

        [void](Test-StagedDiagnosisReady -FrontendUrl $frontendUrl -ReviewId $reviewId)
        $routeEvidence.stages.diagnosis_poll = [ordered]@{ status = "passed"; review_id = $reviewId }

        $recovery = Invoke-JsonRequest -Method "POST" -Url "$frontendUrl/api/portfolio/review/recover" -Body ([ordered]@{ review_id = $reviewId })
        if ($recovery.status -ne "completed") { throw "Staging recovery did not return status=completed." }
        $routeEvidence.stages.recovery = [ordered]@{ status = "passed"; review_id = $reviewId }

        $cards = @(Get-LaunchpadCards -RecoveryBody $recovery)
        if ($cards.Count -eq 0) { throw "Staging recovered review has no Launchpad cards." }
        $selectedCard = Select-LaunchpadCard -Cards $cards
        $selectedCardId = Get-TextValue $selectedCard.card_id
        if ([string]::IsNullOrWhiteSpace($selectedCardId)) { $selectedCardId = Get-TextValue $selectedCard.id }
        if ([string]::IsNullOrWhiteSpace($selectedCardId)) { throw "Selected staging Launchpad card has no card_id." }
        $routeEvidence.selected_card_id = $selectedCardId

        $builder = Invoke-JsonRequest -Method "POST" -Url "$frontendUrl/api/portfolio/builder/prepare" -Body ([ordered]@{ review_id = $reviewId; selected_card_id = $selectedCardId })
        Test-LineageValue -Body $builder -Expected @{ review_id = $reviewId; selected_card_id = $selectedCardId } -Label "staging builder"
        $routeEvidence.stages.builder = [ordered]@{ status = "passed"; selected_card_id = $selectedCardId; can_generate_candidate = $builder.can_generate_candidate }

        $candidate = Invoke-JsonRequest -Method "POST" -Url "$frontendUrl/api/portfolio/candidate/generate" -Body ([ordered]@{ review_id = $reviewId; selected_card_id = $selectedCardId })
        $candidateId = Get-TextValue $candidate.candidate_id
        if ([string]::IsNullOrWhiteSpace($candidateId)) { $candidateId = Get-LineageValue -Body $candidate -Key "candidate_id" }
        if ([string]::IsNullOrWhiteSpace($candidateId)) { throw "Staging candidate generation did not return candidate_id." }
        Test-LineageValue -Body $candidate -Expected @{ review_id = $reviewId; selected_card_id = $selectedCardId; candidate_id = $candidateId } -Label "staging candidate"
        $routeEvidence.candidate_id = $candidateId
        $routeEvidence.stages.candidate = [ordered]@{ status = "passed"; candidate_id = $candidateId; generation_status = $candidate.generation_status }

        $comparison = Invoke-JsonRequest -Method "POST" -Url "$frontendUrl/api/portfolio/comparison/generate" -Body ([ordered]@{ review_id = $reviewId; selected_card_id = $selectedCardId })
        $comparisonId = Get-LineageValue -Body $comparison -Key "comparison_id"
        if ([string]::IsNullOrWhiteSpace($comparisonId)) { $comparisonId = "current_vs_candidate:$candidateId" }
        Test-LineageValue -Body $comparison -Expected @{ review_id = $reviewId; selected_card_id = $selectedCardId; candidate_id = $candidateId; comparison_id = $comparisonId } -Label "staging comparison"
        $routeEvidence.comparison_id = $comparisonId
        $routeEvidence.stages.comparison = [ordered]@{ status = "passed"; comparison_id = $comparisonId }

        $verdict = Invoke-JsonRequest -Method "POST" -Url "$frontendUrl/api/portfolio/verdict/generate" -Body ([ordered]@{ review_id = $reviewId; selected_card_id = $selectedCardId })
        $verdictId = Get-TextValue $verdict.verdict_id
        if ([string]::IsNullOrWhiteSpace($verdictId)) { $verdictId = Get-LineageValue -Body $verdict -Key "verdict_id" }
        if ([string]::IsNullOrWhiteSpace($verdictId)) { throw "Staging verdict did not return verdict_id." }
        Test-LineageValue -Body $verdict -Expected @{ review_id = $reviewId; selected_card_id = $selectedCardId; candidate_id = $candidateId; comparison_id = $comparisonId; verdict_id = $verdictId } -Label "staging verdict"
        $routeEvidence.verdict_id = $verdictId
        $routeEvidence.stages.verdict = [ordered]@{ status = "passed"; verdict_id = $verdictId }

        $report = Invoke-JsonRequest -Method "POST" -Url "$frontendUrl/api/portfolio/report/generate" -Body ([ordered]@{ review_id = $reviewId; selected_card_id = $selectedCardId })
        Test-LineageValue -Body $report -Expected @{ review_id = $reviewId; selected_card_id = $selectedCardId; candidate_id = $candidateId; verdict_id = $verdictId } -Label "staging report"
        $routeEvidence.stages.report = [ordered]@{ status = "passed"; report_status = $report.status }

        $stale = Invoke-JsonRequestAllowFailure -Method "POST" -Url "$frontendUrl/api/portfolio/candidate/generate" -Body ([ordered]@{ review_id = $reviewId; selected_card_id = "${selectedCardId}_stale_probe" })
        if ($stale.ok -or $stale.status -ne 409) { throw "Staging stale selected-card probe expected HTTP 409, got HTTP $($stale.status)." }
        $routeEvidence.stages.stale_selected_card_probe = [ordered]@{ status = "passed"; http_status = $stale.status }

        $routeEvidence.finished_at = (Get-Date).ToUniversalTime().ToString("o")
        $routeEvidence | ConvertTo-Json -Depth 20 | Set-Content -Path $evidencePath -Encoding UTF8

        Add-QaStep -Name "Staging route-chain journey guard" -Status "passed" -Classification "passed" -Message "Staging frontend route chain completed through Report with same-run lineage and stale-card 409 proof." -Details "$details; review_id=$reviewId; selected_card_id=$selectedCardId; candidate_id=$candidateId; comparison_id=$comparisonId; verdict_id=$verdictId" -LogPath $evidencePath
        Add-QaFinding `
            -Id "QA-STAGING-JOURNEY-LINEAGE" `
            -Severity "P0" `
            -Status "passed" `
            -Classification "passed" `
            -Subsystem "staging route chain" `
            -CommandOrRoute "diagnose -> recover -> builder -> candidate -> comparison -> verdict -> report -> stale selected-card probe" `
            -Observed "Staging route chain completed for review_id=$reviewId, selected_card_id=$selectedCardId, candidate_id=$candidateId, comparison_id=$comparisonId, verdict_id=$verdictId; stale selected-card probe returned 409." `
            -Expected "Every downstream stage belongs to the same review/card/candidate lineage and stale selected-card requests are rejected." `
            -EvidencePaths @($evidencePath) `
            -RecommendedNextAction "Keep this check green before production release." `
            -OwnerArea "staging"
    }
    catch {
        $message = $_.Exception.Message
        $classification = if ($message -match "frontend_backend_version_mismatch|405|404|/api/v1/reviews/staged") { "frontend_backend_version_mismatch" } elseif ($message -match "timed out|timeout|market|provider|unavailable|503|504") { "blocked_external" } else { "new_failure" }
        $routeEvidence.error = $message
        $routeEvidence.finished_at = (Get-Date).ToUniversalTime().ToString("o")
        $routeEvidence | ConvertTo-Json -Depth 20 | Set-Content -Path $evidencePath -Encoding UTF8
        Add-QaStep -Name "Staging route-chain journey guard" -Status "failed" -Classification $classification -Message $message -Details $details -LogPath $evidencePath
        Add-QaFinding `
            -Id "QA-STAGING-JOURNEY-LINEAGE" `
            -Severity "P0" `
            -Status "failed" `
            -Classification $classification `
            -Subsystem "staging route chain" `
            -CommandOrRoute "diagnose -> recover -> builder -> candidate -> comparison -> verdict -> report -> stale selected-card probe" `
            -Observed $message `
            -Expected "Staging route chain completes through Report with same-run lineage and stale selected-card HTTP 409 proof." `
            -EvidencePaths @($evidencePath) `
            -RecommendedNextAction "Fix the staging frontend/backend route chain or document the external blocker before release readiness." `
            -OwnerArea "staging"
    }
}

function Find-LatestBrowserVerticalReport {
    param([datetime]$NotBefore)
    $playwrightRoot = Join-Path $RepoRoot "output\playwright"
    if (-not (Test-Path $playwrightRoot)) { return $null }
    $reports = Get-ChildItem -Path $playwrightRoot -Recurse -Filter "qa-report.json" -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -match "vertical-qa-" -and $_.LastWriteTime -ge $NotBefore.AddSeconds(-5) } |
        Sort-Object LastWriteTime -Descending
    if ($reports.Count -eq 0) { return $null }
    return $reports[0].FullName
}

function Add-BrowserVerticalEvidence {
    param(
        [string]$ReportPath,
        [Parameter(Mandatory = $true)][object]$CommandResult
    )
    if ([string]::IsNullOrWhiteSpace($ReportPath) -or -not (Test-Path $ReportPath)) {
        Add-QaFinding `
            -Id "QA-BROWSER-VERTICAL-REPORT-MISSING" `
            -Severity "P0" `
            -Status "failed" `
            -Classification "new_failure" `
            -Subsystem "frontend vertical" `
            -CommandOrRoute $CommandResult.command `
            -Observed "Browser vertical command did not leave a discoverable qa-report.json under output/playwright." `
            -Expected "Browser vertical QA writes output/playwright/vertical-qa-*/qa-report.json with screenshots or DOM fallbacks." `
            -EvidencePaths @($CommandResult.log_path) `
            -RecommendedNextAction "Inspect the command log and repair the vertical QA reporter." `
            -OwnerArea "frontend vertical" `
            -ReproductionCommand $CommandResult.command
        return
    }

    $report = Get-Content -Raw -LiteralPath $ReportPath | ConvertFrom-Json
    $outputDir = Split-Path -Parent $ReportPath
    $evidencePaths = New-Object System.Collections.Generic.List[string]
    $evidencePaths.Add($ReportPath) | Out-Null
    foreach ($name in @("next.log", "fastapi.log")) {
        $path = Join-Path $outputDir $name
        if (Test-Path $path) { $evidencePaths.Add($path) | Out-Null }
    }
    $visualArtifacts = Get-ChildItem -LiteralPath $outputDir -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -in @(".png", ".html", ".txt") } |
        Select-Object -First 30
    foreach ($artifact in $visualArtifacts) { $evidencePaths.Add($artifact.FullName) | Out-Null }

    $scenarioRows = @($report.scenarios)
    $reviewIds = @($scenarioRows | ForEach-Object { Get-TextValue $_.review_id } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    $lineageRows = @($scenarioRows | ForEach-Object {
        "scenario=$($_.scenario_id); review_id=$($_.review_id); selected_card_id=$($_.selected_card_id); candidate_id=$($_.candidate_id); comparison_id=$($_.comparison_id); verdict_id=$($_.verdict_id); stale_probe_status=$($_.stale_probe_status)"
    })
    $screenshotsCount = @(Get-ChildItem -LiteralPath $outputDir -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -eq ".png" }).Count
    $fallbackCount = @(Get-ChildItem -LiteralPath $outputDir -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -in @(".html", ".txt") }).Count
    $observed = "status=$($report.status); frontend_url=$($report.frontend_url); fastapi_url=$($report.fastapi_url); scenarios=$($scenarioRows.Count); screenshots=$screenshotsCount; dom_fallback_files=$fallbackCount; lineage=[$($lineageRows -join ' | ')]"
    $status = if ($report.status -eq "passed" -and $CommandResult.status -eq "passed") { "passed" } else { "failed" }
    $classification = if ($status -eq "passed") { "passed" } elseif (($report.failures -join " ") -match "market|provider|timeout|timed out|unavailable") { "blocked_external" } else { $CommandResult.classification }
    if ([string]::IsNullOrWhiteSpace($classification)) { $classification = "new_failure" }

    Add-QaFinding `
        -Id "QA-BROWSER-VERTICAL-LINEAGE" `
        -Severity "P0" `
        -Status $status `
        -Classification $classification `
        -Subsystem "frontend vertical" `
        -CommandOrRoute $CommandResult.command `
        -Observed $observed `
        -Expected "Fresh FastAPI and Next.js servers complete the vertical route chain, preserve same-run lineage, capture screenshots or DOM fallbacks, and reject stale selected-card requests with HTTP 409." `
        -EvidencePaths @($evidencePaths.ToArray()) `
        -SuspectedCause (($report.failures -join " ") -replace "\s+", " ").Trim() `
        -RecommendedNextAction "If failed, inspect qa-report.json, next.log, fastapi.log, and visual artifacts before release readiness." `
        -OwnerArea "frontend vertical" `
        -ReproductionCommand $CommandResult.command `
        -RetryCount $CommandResult.attempts_used
}

function Invoke-BrowserVerticalQa {
    if ($SkipLive) {
        Add-QaStep -Name "Browser vertical QA" -Status "skipped" -Classification "skipped_not_configured" -Message "Skipped because -SkipLive was supplied."
        Add-QaFinding -Id "QA-BROWSER-VERTICAL-SKIPPED" -Severity "P0" -Status "skipped" -Classification "skipped_not_configured" -Subsystem "frontend vertical" -CommandOrRoute "npm.cmd run qa:vertical -- --scenario-limit $ScenarioLimit" -Observed "Browser vertical QA was skipped by operator flag." -Expected "Release readiness runs browser vertical QA unless explicitly scoped to local static checks." -RecommendedNextAction "Run .\scripts\qa_exhaustive.cmd -LocalOnly or .\scripts\qa_exhaustive.cmd -Staging without -SkipLive for release readiness." -OwnerArea "frontend vertical" -ReproductionCommand "cd frontend; npm.cmd run qa:vertical -- --scenario-limit $ScenarioLimit"
        return
    }

    $startedAt = Get-Date
    $result = Invoke-QaCommand "Browser vertical QA" $FrontendRoot @("npm.cmd", "run", "qa:vertical", "--", "--scenario-limit", [string]$ScenarioLimit) -Subsystem "frontend vertical" -Severity "P0"
    $reportPath = Find-LatestBrowserVerticalReport -NotBefore $startedAt
    Add-BrowserVerticalEvidence -ReportPath $reportPath -CommandResult $result
}

function Invoke-Session02LocalGate {
    $python = @(Get-ProjectPython)
    Test-EnvironmentReadiness
    Test-LocalFastApiOpenApi
    $null = Invoke-QaCommand "Fast daily QA" $RepoRoot @("powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "scripts\qa_fast.ps1") -KnownFailureReason "Known Session 01 baseline: qa_fast includes frontend API route tests, and npm.cmd run test:api reported 14 passed and 6 failed." -Subsystem "cross-cutting" -Severity "P1"
    $null = Invoke-QaCommand "Contract QA" $RepoRoot @("powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "scripts\qa_contracts.ps1") -Subsystem "backend contracts" -Severity "P1"
    $null = Invoke-QaCommand "FastAPI governance verification" $RepoRoot ($python + @("scripts\verify_fastapi_contract_governance.py")) -Subsystem "FastAPI" -Severity "P1"
    $null = Invoke-QaCommand "Focused FastAPI public contract pytest" $RepoRoot ($python + @("-m", "pytest", "tests\test_fastapi_app.py", "tests\test_fastapi_contract_governance.py", "-q", "--basetemp=tmp\qa_exhaustive_fastapi_contract")) -Subsystem "FastAPI" -Severity "P1"
    $null = Invoke-QaCommand "Full backend pytest" $RepoRoot ($python + @("-m", "pytest")) -KnownFailureReason "Known full-suite baseline tracked in KNOWN_ISSUES.md: Session 02 exhaustive QA reported 34 failed, 1887 passed, 3 skipped on 2026-06-14." -Subsystem "backend" -Severity "P1"
    $null = Invoke-QaCommand "Frontend typecheck" $FrontendRoot @("npm.cmd", "run", "typecheck") -Subsystem "frontend" -Severity "P1"
    $null = Invoke-QaCommand "Frontend production build" $FrontendRoot @("npm.cmd", "run", "build") -KnownFailureReason "Known Session 02 runner baseline tracked as KI-2026-06-14-001: npm.cmd run build can return -1 inside the long exhaustive gate after full pytest, while the same build command passes when run standalone." -Subsystem "frontend" -Severity "P1" -MaxAttempts 2
    $null = Invoke-QaCommand "Frontend API route tests" $FrontendRoot @("npm.cmd", "run", "test:api") -KnownFailureReason "Known Session 01 baseline: npm.cmd run test:api reported 14 passed and 6 failed; diagnosis staged-route tests passed." -Subsystem "frontend API" -Severity "P1"
    $null = Invoke-QaCommand "Frontend smoke tests" $FrontendRoot @("npm.cmd", "run", "test:smoke") -Subsystem "frontend" -Severity "P1"
    $null = Invoke-QaCommand "Docs verification" $RepoRoot ($python + @("scripts\verify_docs.py")) -Subsystem "docs" -Severity "P2"
    $null = Invoke-QaCommand "Docs link pytest" $RepoRoot ($python + @("-m", "pytest", "tests\test_docs_links.py", "-q", "--basetemp=tmp\qa_exhaustive_docs_links")) -Subsystem "docs" -Severity "P2"
    $null = Invoke-QaCommand "Supabase compact Client Fit pytest" $RepoRoot ($python + @("-m", "pytest", "tests\test_supabase_client_fit_compact_storage.py", "-q", "--basetemp=tmp\qa_exhaustive_supabase_compact")) -Subsystem "Supabase" -Severity "P2"
    $null = Invoke-QaCommand "Supabase compact/privacy frontend API rows" $FrontendRoot @("node", "--test", "--test-name-pattern=Supabase", "tests/api-route-tests.cjs") -KnownFailureReason "Known Session 01 frontend API baseline: the Supabase staged persistence row is part of the recorded non-green npm.cmd run test:api suite." -Subsystem "Supabase" -Severity "P2"
}

function Write-QaSummary {
    $newFailures = @($Steps | Where-Object { $_.classification -eq "new_failure" -or $_.classification -eq "frontend_backend_version_mismatch" })
    $knownFailures = @($Steps | Where-Object { $_.classification -eq "known_failure" })
    $externalBlockers = @($Steps | Where-Object { $_.classification -eq "blocked_external" })
    $blockingFindings = @($Findings | Where-Object { $_.status -eq "failed" -and $_.severity -in @("P0", "P1", "P2") })
    $p0Blockers = @($blockingFindings | Where-Object { $_.severity -eq "P0" })
    $p1Blockers = @($blockingFindings | Where-Object { $_.severity -eq "P1" })
    $p2Blockers = @($blockingFindings | Where-Object { $_.severity -eq "P2" })
    $releaseStatus = if ($p0Blockers.Count -gt 0 -or $p1Blockers.Count -gt 0 -or $p2Blockers.Count -gt 0) { "not_ready" } elseif ($knownFailures.Count -gt 0) { "ready_with_known_failures" } else { "ready" }
    $runStatus = if ($newFailures.Count -gt 0) { "failed" } elseif ($externalBlockers.Count -gt 0) { "blocked_external" } elseif ($knownFailures.Count -gt 0) { "passed_with_known_failures" } else { "passed" }
    $completedAt = (Get-Date).ToUniversalTime().ToString("o")
    $releaseReadiness = [pscustomobject]@{
        schema_version = "qa_release_readiness_session03_v1"
        status = $releaseStatus
        generated_at = $completedAt
        blocker_counts = [pscustomobject]@{
            P0 = $p0Blockers.Count
            P1 = $p1Blockers.Count
            P2 = $p2Blockers.Count
        }
        blockers = @($blockingFindings | ForEach-Object {
            [pscustomobject]@{
                id = $_.id
                severity = $_.severity
                classification = $_.classification
                subsystem = $_.subsystem
                observed = $_.observed
                evidence_paths = $_.evidence_paths
                recommended_next_action = $_.recommended_next_action
            }
        })
    }
    $summary = [pscustomobject]@{
        schema_version = "qa_exhaustive_session03_v1"
        run_status = $runStatus
        started_at = $RunStartedAt
        completed_at = $completedAt
        repo_root = $RepoRoot
        mode = [pscustomobject]@{ local_only = [bool]$LocalOnly; staging = [bool]$Staging; skip_live = [bool]$SkipLive; scenario_limit = $ScenarioLimit }
        output_dir = $RunRoot
        logs_dir = $LogsRoot
        counts = [pscustomobject]@{
            total = $Steps.Count
            passed = @($Steps | Where-Object { $_.status -eq "passed" }).Count
            failed = @($Steps | Where-Object { $_.status -eq "failed" }).Count
            known_failure = $knownFailures.Count
            new_failure = $newFailures.Count
            blocked_external = $externalBlockers.Count
            skipped_not_configured = @($Steps | Where-Object { $_.classification -eq "skipped_not_configured" }).Count
        }
        release_readiness = $releaseReadiness
        steps = @($Steps.ToArray())
        findings_file = $FindingsJson
        release_readiness_file = $ReadinessJson
    }
    $summary | ConvertTo-Json -Depth 20 | Set-Content -Path $SummaryJson -Encoding UTF8
    [pscustomobject]@{
        schema_version = "qa_findings_session03_v1"
        run_status = $runStatus
        generated_at = $completedAt
        output_dir = $RunRoot
        release_readiness_file = $ReadinessJson
        findings = @($Findings.ToArray())
    } | ConvertTo-Json -Depth 20 | Set-Content -Path $FindingsJson -Encoding UTF8
    $releaseReadiness | ConvertTo-Json -Depth 20 | Set-Content -Path $ReadinessJson -Encoding UTF8

    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add("# Portfolio MRI Exhaustive QA Summary") | Out-Null
    $lines.Add("") | Out-Null
    $lines.Add("- Schema: qa_exhaustive_session03_v1") | Out-Null
    $lines.Add("- Status: $runStatus") | Out-Null
    $lines.Add("- Release readiness: $releaseStatus") | Out-Null
    $lines.Add("- Started: $RunStartedAt") | Out-Null
    $lines.Add("- Completed: $completedAt") | Out-Null
    $lines.Add("- Output: $RunRoot") | Out-Null
    $lines.Add("- Logs: $LogsRoot") | Out-Null
    $lines.Add("- Findings: $FindingsJson") | Out-Null
    $lines.Add("- Release readiness file: $ReadinessJson") | Out-Null
    $lines.Add("- P0/P1/P2 blockers: $($p0Blockers.Count)/$($p1Blockers.Count)/$($p2Blockers.Count)") | Out-Null
    $lines.Add("") | Out-Null
    $lines.Add("## Steps") | Out-Null
    foreach ($step in $Steps) {
        $lines.Add("") | Out-Null
        $lines.Add("### $($step.name)") | Out-Null
        $lines.Add("- Status: $($step.status)") | Out-Null
        $lines.Add("- Classification: $($step.classification)") | Out-Null
        $lines.Add("- Message: $($step.message)") | Out-Null
        if (-not [string]::IsNullOrWhiteSpace($step.command)) { $lines.Add("- Command: $($step.command)") | Out-Null }
        if (-not [string]::IsNullOrWhiteSpace($step.log_path)) { $lines.Add("- Log: $($step.log_path)") | Out-Null }
        if (-not [string]::IsNullOrWhiteSpace($step.details)) { $lines.Add("- Details: $($step.details)") | Out-Null }
    }
    $lines | Set-Content -Path $SummaryMd -Encoding UTF8

    $findingLines = New-Object System.Collections.Generic.List[string]
    $findingLines.Add("# Portfolio MRI Exhaustive QA Findings") | Out-Null
    $findingLines.Add("") | Out-Null
    $findingLines.Add("- Schema: qa_findings_session03_v1") | Out-Null
    $findingLines.Add("- Status: $runStatus") | Out-Null
    $findingLines.Add("- Release readiness: $releaseStatus") | Out-Null
    $findingLines.Add("- Output: $RunRoot") | Out-Null
    foreach ($finding in $Findings) {
        $findingLines.Add("") | Out-Null
        $findingLines.Add("## $($finding.id)") | Out-Null
        $findingLines.Add("- Severity: $($finding.severity)") | Out-Null
        $findingLines.Add("- Status: $($finding.status)") | Out-Null
        $findingLines.Add("- Classification: $($finding.classification)") | Out-Null
        $findingLines.Add("- Subsystem: $($finding.subsystem)") | Out-Null
        $findingLines.Add("- Command or route: $($finding.command_or_route)") | Out-Null
        $findingLines.Add("- Observed: $($finding.observed)") | Out-Null
        $findingLines.Add("- Expected: $($finding.expected)") | Out-Null
        if ($finding.evidence_paths.Count -gt 0) { $findingLines.Add("- Evidence: $($finding.evidence_paths -join '; ')") | Out-Null }
        if (-not [string]::IsNullOrWhiteSpace($finding.suspected_cause)) { $findingLines.Add("- Suspected cause: $($finding.suspected_cause)") | Out-Null }
        if (-not [string]::IsNullOrWhiteSpace($finding.recommended_next_action)) { $findingLines.Add("- Recommended next action: $($finding.recommended_next_action)") | Out-Null }
        if (-not [string]::IsNullOrWhiteSpace($finding.owner_area)) { $findingLines.Add("- Owner area: $($finding.owner_area)") | Out-Null }
        if (-not [string]::IsNullOrWhiteSpace($finding.reproduction_command)) { $findingLines.Add("- Reproduction command: $($finding.reproduction_command)") | Out-Null }
        if ($finding.retry_count -gt 0) { $findingLines.Add("- Retry count: $($finding.retry_count)") | Out-Null }
        if ($finding.warnings.Count -gt 0) { $findingLines.Add("- Warnings: $($finding.warnings -join '; ')") | Out-Null }
    }
    $findingLines | Set-Content -Path $FindingsMd -Encoding UTF8

    $readinessLines = New-Object System.Collections.Generic.List[string]
    $readinessLines.Add("# Portfolio MRI Release Readiness") | Out-Null
    $readinessLines.Add("") | Out-Null
    $readinessLines.Add("- Schema: qa_release_readiness_session03_v1") | Out-Null
    $readinessLines.Add("- Status: $releaseStatus") | Out-Null
    $readinessLines.Add("- Generated: $completedAt") | Out-Null
    $readinessLines.Add("- P0 blockers: $($p0Blockers.Count)") | Out-Null
    $readinessLines.Add("- P1 blockers: $($p1Blockers.Count)") | Out-Null
    $readinessLines.Add("- P2 blockers: $($p2Blockers.Count)") | Out-Null
    foreach ($blocker in $blockingFindings) {
        $readinessLines.Add("") | Out-Null
        $readinessLines.Add("## $($blocker.id)") | Out-Null
        $readinessLines.Add("- Severity: $($blocker.severity)") | Out-Null
        $readinessLines.Add("- Classification: $($blocker.classification)") | Out-Null
        $readinessLines.Add("- Subsystem: $($blocker.subsystem)") | Out-Null
        $readinessLines.Add("- Observed: $($blocker.observed)") | Out-Null
        $readinessLines.Add("- Recommended next action: $($blocker.recommended_next_action)") | Out-Null
        if ($blocker.evidence_paths.Count -gt 0) { $readinessLines.Add("- Evidence: $($blocker.evidence_paths -join '; ')") | Out-Null }
    }
    $readinessLines | Set-Content -Path $ReadinessMd -Encoding UTF8

    Write-Host ""
    Write-Host "QA summary written:" -ForegroundColor Green
    Write-Host $SummaryJson
    Write-Host $SummaryMd
    Write-Host $FindingsJson
    Write-Host $FindingsMd
    Write-Host $ReadinessJson
    Write-Host $ReadinessMd
    if ($runStatus -eq "failed") { throw "One or more exhaustive QA Session 03 steps produced new failures. See $SummaryMd." }
}

Write-Host "Portfolio MRI exhaustive QA gate (Session 03)" -ForegroundColor Green
Write-Host "Repository: $RepoRoot"
Write-Host "Output: $RunRoot"
Write-Host "Browser scenario limit: $ScenarioLimit"
if ($SkipLive) { Write-Host "Live/browser checks are skipped by -SkipLive." -ForegroundColor Yellow }

try {
    Invoke-Session02LocalGate
    Invoke-BrowserVerticalQa
    if ($Staging -and -not $LocalOnly) {
        Test-StagingRunDiagnosis
        Test-StagingJourneyReadiness
    } elseif ($Staging -and $LocalOnly) {
        Add-QaStep -Name "Staging Run Diagnosis compatibility guard" -Status "skipped" -Classification "skipped_not_configured" -Message "Skipped because -LocalOnly was supplied."
        Add-QaFinding -Id "QA-STAGING-RUN-DIAGNOSIS-SKIPPED" -Severity "P0" -Status "skipped" -Classification "skipped_not_configured" -Subsystem "staging" -CommandOrRoute "POST /api/portfolio/diagnose" -Observed "Staging guard was skipped because -LocalOnly was supplied." -Expected "Staging release readiness runs without -LocalOnly and with staging URLs configured." -RecommendedNextAction "Run .\scripts\qa_exhaustive.cmd -Staging without -LocalOnly when staging release readiness is required." -OwnerArea "staging"
        Add-QaStep -Name "Staging route-chain journey guard" -Status "skipped" -Classification "skipped_not_configured" -Message "Skipped because -LocalOnly was supplied."
        Add-QaFinding -Id "QA-STAGING-JOURNEY-SKIPPED" -Severity "P0" -Status "skipped" -Classification "skipped_not_configured" -Subsystem "staging" -CommandOrRoute "diagnose -> recover -> builder -> candidate -> comparison -> verdict -> report" -Observed "Staging route-chain check was skipped because -LocalOnly was supplied." -Expected "Staging release readiness runs without -LocalOnly and with staging URLs configured." -RecommendedNextAction "Run .\scripts\qa_exhaustive.cmd -Staging without -LocalOnly when staging release readiness is required." -OwnerArea "staging"
    }
}
catch {
    Add-QaStep -Name "Session 02 orchestration" -Status "failed" -Classification "new_failure" -Message $_.Exception.Message
}
finally { Write-QaSummary }
