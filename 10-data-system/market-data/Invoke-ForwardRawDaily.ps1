[CmdletBinding()]
param(
    [ValidateSet('Run', 'TaskPlan')]
    [string]$Mode = 'Run',
    [string]$DailyAt,
    [string]$PowerShellExecutablePath,
    [string]$RunnerScriptPath
)

$ErrorActionPreference = 'Stop'
$script:ForwardRawDailyRoot = 'D:\AQ_DATA\FORWARD_RAW_ONLY'
$script:ForwardRawDailyMutexName = 'Global\AQ.ForwardRawOnly.Daily'
$script:ForwardRawDailyAnchorDate = '2026-10-19'
$script:ForwardRawDailyCloseBufferMinutes = 15
$script:ForwardRawDailyMaxMissingSessions = 5
$script:ForwardRawDailyMaxFetchSessionsPerRun = 3
$script:ForwardRawDailyCalendarPython = '/home/zhou/AQ_ENVS/p6-macro-v1/bin/python'
$script:ForwardRawDailySource = Join-Path $PSScriptRoot 'Update-AlpacaQlibResearchData.ps1'
$script:ForwardRawDailyRunner = $PSCommandPath
$script:ForwardRawDailyValidator = Join-Path $PSScriptRoot 'verify_alpaca_qlib_refresh.py'
$requestedMode = $Mode
. $script:ForwardRawDailySource -Mode ForwardRawFetch
$Mode = $requestedMode

function Get-LastCompletedXnysSession {
    param(
        [datetimeoffset]$NowUtc = [datetimeoffset]::UtcNow,
        [string]$CalendarPython = $script:ForwardRawDailyCalendarPython,
        [string]$Validator = $script:ForwardRawDailyValidator
    )
    $instant = $NowUtc.ToUniversalTime()
    $nowText = $instant.ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ', [Globalization.CultureInfo]::InvariantCulture)
    $validatorLinux = Convert-WindowsPathToWsl $Validator
    $arguments = @('-e', $CalendarPython, $validatorLinux, 'xnys-last-completed', '--now-utc', $nowText)
    $output = & wsl.exe @arguments 2>&1
    if ($LASTEXITCODE -ne 0) { throw "XNYS_SESSION_SELECTION_FAILED_EXIT_$LASTEXITCODE" }
    $jsonLine = $output | Where-Object { [string]$_ -match '^\s*\{' } | Select-Object -Last 1
    if (!$jsonLine) { throw 'XNYS_SESSION_SELECTION_RESULT_MISSING' }
    $result = [string]$jsonLine | ConvertFrom-Json -ErrorAction Stop
    if ($result.calendar -ne 'XNYS' -or $result.package -ne 'exchange_calendars' -or !$result.status -or !$result.market_date) {
        throw 'XNYS_SESSION_SELECTION_RESULT_INVALID'
    }
    if ($result.status -in @('SKIPPED_NON_TRADING_DAY', 'SKIPPED_SESSION_NOT_COMPLETE')) { return $result }
    if ($result.status -ne 'SESSION_COMPLETE' -or !$result.session -or !$result.close_utc) { throw 'XNYS_SESSION_SELECTION_RESULT_INVALID' }
    $session = [datetime]::ParseExact((ConvertTo-ForwardRawDateText $result.session), 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture)
    $close = [datetimeoffset]::Parse((ConvertTo-ForwardRawTimestampText $result.close_utc), [Globalization.CultureInfo]::InvariantCulture).ToUniversalTime()
    if ($close -gt $instant -or $session.Date -gt $instant.UtcDateTime.Date) { throw 'XNYS_SESSION_NOT_COMPLETED' }
    return $result
}

function Get-CompletedXnysSessions {
    param(
        [datetimeoffset]$NowUtc = [datetimeoffset]::UtcNow,
        [string]$StartDate = $script:ForwardRawDailyAnchorDate,
        [int]$CloseBufferMinutes = $script:ForwardRawDailyCloseBufferMinutes,
        [string]$CalendarPython = $script:ForwardRawDailyCalendarPython,
        [string]$Validator = $script:ForwardRawDailyValidator
    )
    $start = [datetime]::ParseExact($StartDate, 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture)
    $instant = $NowUtc.ToUniversalTime()
    $nowText = $instant.ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ', [Globalization.CultureInfo]::InvariantCulture)
    $validatorLinux = Convert-WindowsPathToWsl $Validator
    $arguments = @('-e', $CalendarPython, $validatorLinux, 'xnys-completed-sessions', '--start-date', $StartDate, '--now-utc', $nowText, '--close-buffer-minutes', [string]$CloseBufferMinutes)
    $output = & wsl.exe @arguments 2>&1
    if ($LASTEXITCODE -ne 0) { throw "XNYS_SESSION_ENUMERATION_FAILED_EXIT_$LASTEXITCODE" }
    $jsonLine = $output | Where-Object { [string]$_ -match '^\s*\{' } | Select-Object -Last 1
    if (!$jsonLine) { throw 'XNYS_SESSION_ENUMERATION_RESULT_MISSING' }
    $result = [string]$jsonLine | ConvertFrom-Json -ErrorAction Stop
    if ($result.calendar -ne 'XNYS' -or $result.package -ne 'exchange_calendars' -or
        $result.start_date -ne $StartDate -or $result.close_buffer_minutes -ne $CloseBufferMinutes -or
        $result.status -notin @('SESSIONS_READY', 'NO_COMPLETED_SESSIONS') -or $null -eq $result.sessions) {
        throw 'XNYS_SESSION_ENUMERATION_RESULT_INVALID'
    }
    $sessions = @($result.sessions)
    if ($result.status -eq 'NO_COMPLETED_SESSIONS' -and $sessions.Count -ne 0) { throw 'XNYS_SESSION_ENUMERATION_RESULT_INVALID' }
    if ($result.status -eq 'SESSIONS_READY' -and $sessions.Count -eq 0) { throw 'XNYS_SESSION_ENUMERATION_RESULT_INVALID' }
    $previous = $null
    foreach ($session in $sessions) {
        $parsed = [datetime]::ParseExact([string]$session, 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture)
        if ($parsed -lt $start -or $parsed.Date -gt $instant.UtcDateTime.Date -or ($null -ne $previous -and $parsed -le $previous)) {
            throw 'XNYS_SESSION_ENUMERATION_ORDER_OR_RANGE_INVALID'
        }
        $previous = $parsed
    }
    return $sessions
}

function Get-ForwardRawDailyOutputId {
    param([Parameter(Mandatory)][string]$SessionDate)
    $parsed = [datetime]::ParseExact($SessionDate, 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture)
    return 'forwardraw-xnys-{0}-aapl-msft' -f $parsed.ToString('yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture)
}

function ConvertTo-ForwardRawDateText {
    param($Value)
    if ($Value -is [datetime]) { return $Value.ToString('yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture) }
    return [string]$Value
}

function ConvertTo-ForwardRawTimestampText {
    param($Value)
    if ($Value -is [datetime]) { return $Value.ToUniversalTime().ToString("yyyy-MM-dd'T'HH:mm:ss'Z'", [Globalization.CultureInfo]::InvariantCulture) }
    if ($Value -is [datetimeoffset]) { return $Value.ToUniversalTime().ToString("yyyy-MM-dd'T'HH:mm:ss'Z'", [Globalization.CultureInfo]::InvariantCulture) }
    return [string]$Value
}

function Get-ForwardRawDailyPowerShellExecutable {
    param(
        [string]$PowerShellHome = $PSHOME,
        [string]$Edition = $PSEdition,
        [version]$Version = $PSVersionTable.PSVersion
    )
    if ($Edition -ne 'Core' -or $Version.Major -lt 7) { throw 'FORWARD_RAW_DAILY_POWERSHELL_7_REQUIRED' }
    $executable = Join-Path $PowerShellHome 'pwsh.exe'
    if (!(Test-Path -LiteralPath $executable -PathType Leaf)) { throw 'FORWARD_RAW_DAILY_POWERSHELL_7_EXECUTABLE_MISSING' }
    return [IO.Path]::GetFullPath($executable)
}

function Assert-ForwardRawDailyBars {
    param([Parameter(Mandatory)]$Payload, [Parameter(Mandatory)][string]$Symbol, [Parameter(Mandatory)][string]$SessionDate)
    if ($Payload.next_page_token) { throw "FORWARD_RAW_DAILY_PAGINATION_INCOMPLETE:$Symbol" }
    $bars = @($Payload.bars)
    if ($bars.Count -ne 1) { throw "FORWARD_RAW_DAILY_BAR_COUNT_INVALID:$Symbol" }
    try {
        $bar = $bars[0]
        if ($bar.t -is [datetime]) { $day = $bar.t.ToUniversalTime().ToString('yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture) }
        else { $day = ([datetimeoffset]::Parse([string]$bar.t, [Globalization.CultureInfo]::InvariantCulture)).ToUniversalTime().ToString('yyyy-MM-dd') }
        $values = @([double]$bar.o, [double]$bar.h, [double]$bar.l, [double]$bar.c, [double]$bar.v)
    }
    catch { throw "FORWARD_RAW_DAILY_BAR_SCHEMA_INVALID:$Symbol" }
    if ($day -ne $SessionDate) { throw "FORWARD_RAW_DAILY_BAR_DATE_MISMATCH:$Symbol" }
    foreach ($value in $values) {
        if ([double]::IsNaN($value) -or [double]::IsInfinity($value)) { throw "FORWARD_RAW_DAILY_BAR_NONFINITE:$Symbol" }
    }
    if ($values[0] -le 0 -or $values[1] -lt [Math]::Max($values[0], $values[3]) -or $values[2] -gt [Math]::Min($values[0], $values[3]) -or $values[4] -lt 0) {
        throw "FORWARD_RAW_DAILY_BAR_OHLCV_INVALID:$Symbol"
    }
}

function Test-ForwardRawDailyOutput {
    param(
        [Parameter(Mandatory)][string]$ForwardRawRoot,
        [Parameter(Mandatory)][string]$OutputId,
        [Parameter(Mandatory)][string]$SessionDate
    )
    $rootPath = [IO.Path]::GetFullPath($ForwardRawRoot)
    $outputPath = Join-Path $rootPath $OutputId
    if (!(Test-Path -LiteralPath $outputPath)) { return $false }
    $directory = Get-Item -LiteralPath $outputPath -Force
    if (!$directory.PSIsContainer -or ($directory.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'FORWARD_RAW_DAILY_EXISTING_OUTPUT_UNTRUSTED' }

    $expectedNames = @('AAPL.json', 'MSFT.json', 'manifest.json') | Sort-Object
    $actualNames = @(Get-ChildItem -LiteralPath $outputPath -Force | ForEach-Object Name | Sort-Object)
    if (($actualNames -join '|') -ne ($expectedNames -join '|')) { throw 'FORWARD_RAW_DAILY_EXISTING_OUTPUT_FILESET_INVALID' }
    foreach ($name in $expectedNames) {
        $item = Get-Item -LiteralPath (Join-Path $outputPath $name) -Force
        if ($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw "FORWARD_RAW_DAILY_EXISTING_FILE_UNTRUSTED:$name" }
    }

    try { $manifest = Get-Content -LiteralPath (Join-Path $outputPath 'manifest.json') -Raw | ConvertFrom-Json -ErrorAction Stop }
    catch { throw 'FORWARD_RAW_DAILY_EXISTING_MANIFEST_INVALID' }
    if ($manifest.status -ne 'FORWARD_RAW_FETCH_COMPLETE' -or
        $manifest.source_attestation -ne 'CONTROLLED_ALPACA_FETCH_BY_EXISTING_ENTRYPOINT' -or
        $manifest.storage_class -ne 'FORWARD_RAW_ONLY' -or
        $manifest.qlib_conversion -ne $false -or
        $manifest.p3_research_access -ne $false -or
        $manifest.p2_certification_authority -ne $false -or
        $manifest.training_or_trading_authority -ne $false -or
        (ConvertTo-ForwardRawDateText $manifest.start) -ne $SessionDate -or (ConvertTo-ForwardRawDateText $manifest.end) -ne $SessionDate) {
        throw 'FORWARD_RAW_DAILY_EXISTING_MANIFEST_SCOPE_INVALID'
    }
    $parameters = $manifest.acquisition.parameters
    if ($manifest.acquisition.provider -ne 'Alpaca Market Data API' -or
        $parameters.timeframe -ne '1Day' -or
        (ConvertTo-ForwardRawTimestampText $parameters.start) -ne ('{0}T00:00:00Z' -f $SessionDate) -or
        (ConvertTo-ForwardRawTimestampText $parameters.end) -ne ('{0}T23:59:59Z' -f $SessionDate) -or
        $parameters.feed -ne 'sip' -or $parameters.adjustment -ne 'raw' -or
        $parameters.asof -ne '-' -or $parameters.limit -ne 10000 -or
        $manifest.acquisition.request_count -ne 2) {
        throw 'FORWARD_RAW_DAILY_EXISTING_ACQUISITION_SCOPE_INVALID'
    }

    $symbols = @('AAPL', 'MSFT')
    if (@($manifest.symbols).Count -ne 2 -or @($manifest.acquisition.responses).Count -ne 2) { throw 'FORWARD_RAW_DAILY_EXISTING_SYMBOL_COUNT_INVALID' }
    foreach ($symbol in $symbols) {
        $record = @($manifest.symbols | Where-Object symbol -eq $symbol)
        $response = @($manifest.acquisition.responses | Where-Object symbol -eq $symbol)
        if ($record.Count -ne 1 -or $response.Count -ne 1 -or $response[0].http_status -ne 200 -or
            $record[0].bars -ne 1 -or $response[0].bar_count -ne 1 -or
            (ConvertTo-ForwardRawDateText $record[0].first_date) -ne $SessionDate -or (ConvertTo-ForwardRawDateText $record[0].last_date) -ne $SessionDate -or
            (ConvertTo-ForwardRawDateText $response[0].first_date) -ne $SessionDate -or (ConvertTo-ForwardRawDateText $response[0].last_date) -ne $SessionDate) {
            throw "FORWARD_RAW_DAILY_EXISTING_SYMBOL_RECORD_INVALID:$Symbol"
        }
        $file = Join-Path $outputPath ($symbol + '.json')
        $actualHash = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant()
        $length = (Get-Item -LiteralPath $file).Length
        if ($actualHash -ne [string]$record[0].sha256 -or $actualHash -ne [string]$response[0].response_sha256 -or
            $length -ne [long]$record[0].bytes -or $length -ne [long]$response[0].response_bytes) {
            throw "FORWARD_RAW_DAILY_EXISTING_HASH_MISMATCH:$Symbol"
        }
        try { $payload = Get-Content -LiteralPath $file -Raw | ConvertFrom-Json -ErrorAction Stop }
        catch { throw "FORWARD_RAW_DAILY_EXISTING_JSON_INVALID:$Symbol" }
        Assert-ForwardRawDailyBars -Payload $payload -Symbol $symbol -SessionDate $SessionDate
    }
    return $true
}

function Find-ExistingForwardRawDailyOutput {
    param([Parameter(Mandatory)][string]$ForwardRawRoot, [Parameter(Mandatory)][string]$SessionDate)
    $rootPath = [IO.Path]::GetFullPath($ForwardRawRoot)
    if (@(Get-ChildItem -LiteralPath $rootPath -File -Force).Count -gt 0) { throw 'FORWARD_RAW_DAILY_UNEXPECTED_ROOT_FILE_FAIL_CLOSED' }
    $matches = @()
    foreach ($item in Get-ChildItem -LiteralPath $rootPath -Directory -Force) {
        if ($item.Name -eq '.staging') { continue }
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'FORWARD_RAW_DAILY_EXISTING_OUTPUT_UNTRUSTED' }
        $manifestPath = Join-Path $item.FullName 'manifest.json'
        if (!(Test-Path -LiteralPath $manifestPath -PathType Leaf)) { throw "FORWARD_RAW_DAILY_EXISTING_MANIFEST_MISSING:$($item.Name)" }
        try { $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json -ErrorAction Stop }
        catch { throw "FORWARD_RAW_DAILY_EXISTING_MANIFEST_INVALID:$($item.Name)" }
        try {
            $manifestStart = [datetime]::ParseExact((ConvertTo-ForwardRawDateText $manifest.start), 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture).ToString('yyyy-MM-dd')
            $manifestEnd = [datetime]::ParseExact((ConvertTo-ForwardRawDateText $manifest.end), 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture).ToString('yyyy-MM-dd')
        }
        catch { throw "FORWARD_RAW_DAILY_EXISTING_MANIFEST_DATE_INVALID:$($item.Name)" }
        $targetDate = [datetime]::ParseExact($SessionDate, 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture)
        $rangeStart = [datetime]::ParseExact($manifestStart, 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture)
        $rangeEnd = [datetime]::ParseExact($manifestEnd, 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture)
        if ($rangeStart -gt $rangeEnd) { throw "FORWARD_RAW_DAILY_EXISTING_MANIFEST_RANGE_INVALID:$($item.Name)" }
        if ($rangeStart -le $targetDate -and $targetDate -le $rangeEnd) {
            if ($manifestStart -ne $SessionDate -or $manifestEnd -ne $SessionDate) {
                throw "FORWARD_RAW_DAILY_EXISTING_DATE_COVERAGE_CONFLICT:$($item.Name):${manifestStart}..${manifestEnd}:$SessionDate"
            }
            if (!(Test-ForwardRawDailyOutput -ForwardRawRoot $rootPath -OutputId $item.Name -SessionDate $SessionDate)) {
                throw 'FORWARD_RAW_DAILY_EXISTING_OUTPUT_UNEXPECTEDLY_MISSING'
            }
            $matches += [pscustomobject]@{ OutputId = $item.Name; OutputPath = $item.FullName }
        }
    }
    if ($matches.Count -gt 1) { throw 'FORWARD_RAW_DAILY_DUPLICATE_COMPLETED_OUTPUTS_FAIL_CLOSED' }
    if ($matches.Count -eq 1) { return $matches[0] }
    return $null
}

function Invoke-ForwardRawDaily {
    param(
        [datetimeoffset]$NowUtc = [datetimeoffset]::UtcNow,
        [string]$ForwardRawRoot = $script:ForwardRawDailyRoot,
        [scriptblock]$SessionResolver,
        [scriptblock]$FetchAction,
        [string]$Entrypoint = $script:ForwardRawDailySource,
        [string]$MutexName = $script:ForwardRawDailyMutexName
    )
    $mutex = [Threading.Mutex]::new($false, $MutexName)
    $ownsMutex = $false
    try {
        try { $ownsMutex = $mutex.WaitOne(0) }
        catch [Threading.AbandonedMutexException] {
            $ownsMutex = $true
            throw 'FORWARD_RAW_DAILY_PREVIOUS_INSTANCE_ABANDONED'
        }
        if (!$ownsMutex) { throw 'FORWARD_RAW_DAILY_ALREADY_RUNNING' }

        if ($SessionResolver) { $resolution = & $SessionResolver $NowUtc $script:ForwardRawDailyAnchorDate $script:ForwardRawDailyCloseBufferMinutes }
        else { $resolution = [pscustomobject]@{ status = 'SESSIONS_READY'; sessions = @(Get-CompletedXnysSessions -NowUtc $NowUtc) } }
        if ($resolution -is [string]) { $sessionDates = @($resolution) }
        elseif ($resolution.status -in @('SKIPPED_NON_TRADING_DAY', 'SKIPPED_SESSION_NOT_COMPLETE')) {
            return [pscustomobject]@{ Status = $resolution.status; SessionDate = $null; OutputId = $null; OutputPath = $null; FetchedSessions = @(); SkippedSessions = @() }
        }
        elseif ($resolution.status -eq 'SESSION_COMPLETE') { $sessionDates = @((ConvertTo-ForwardRawDateText $resolution.session)) }
        elseif ($resolution.status -eq 'NO_COMPLETED_SESSIONS') {
            return [pscustomobject]@{ Status = 'SKIPPED_NO_COMPLETED_SESSIONS'; SessionDate = $null; OutputId = $null; OutputPath = $null; FetchedSessions = @(); SkippedSessions = @() }
        }
        elseif ($resolution.status -eq 'SESSIONS_READY') { $sessionDates = @($resolution.sessions) }
        else { throw 'XNYS_SESSION_SELECTION_RESULT_INVALID' }
        if ($sessionDates.Count -eq 0) { return [pscustomobject]@{ Status = 'SKIPPED_NO_COMPLETED_SESSIONS'; SessionDate = $null; OutputId = $null; OutputPath = $null; FetchedSessions = @(); SkippedSessions = @() } }
        $previousDate = $null
        foreach ($dateText in $sessionDates) {
            $parsed = [datetime]::ParseExact([string]$dateText, 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture)
            $anchor = [datetime]::ParseExact($script:ForwardRawDailyAnchorDate, 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture)
            if ($parsed.Date -lt $anchor.Date -or $parsed.Date -gt $NowUtc.UtcDateTime.Date -or ($null -ne $previousDate -and $parsed -le $previousDate)) {
                throw 'FORWARD_RAW_DAILY_SESSION_ORDER_OR_ANCHOR_INVALID'
            }
            $previousDate = $parsed
        }
        $rootPath = [IO.Path]::GetFullPath($ForwardRawRoot)
        if (!(Test-Path -LiteralPath $rootPath)) { $null = New-Item -ItemType Directory -Path $rootPath }
        $rootItem = Get-Item -LiteralPath $rootPath -Force
        if (!$rootItem.PSIsContainer -or ($rootItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'FORWARD_RAW_DAILY_ROOT_UNTRUSTED' }
        # Inspect every eligible session and every existing manifest before performing any fetch.
        $missing = @()
        $existing = @()
        foreach ($sessionDate in $sessionDates) {
            $found = Find-ExistingForwardRawDailyOutput -ForwardRawRoot $ForwardRawRoot -SessionDate ([string]$sessionDate)
            if ($found) { $existing += [pscustomobject]@{ SessionDate = [string]$sessionDate; Output = $found } }
            else { $missing += [string]$sessionDate }
        }
        if ($missing.Count -gt $script:ForwardRawDailyMaxMissingSessions) {
            throw "FORWARD_RAW_DAILY_MISSING_SESSION_LIMIT_EXCEEDED:$($missing.Count):$script:ForwardRawDailyMaxMissingSessions"
        }
        if ($missing.Count -eq 0) {
            return [pscustomobject]@{ Status = 'SKIPPED_ALREADY_COMPLETE'; SessionDate = $sessionDates[-1]; OutputId = $existing[-1].Output.OutputId; OutputPath = $existing[-1].Output.OutputPath; FetchedSessions = @(); SkippedSessions = @($sessionDates) }
        }

        $stagingPath = Join-Path $rootPath '.staging'
        if (Test-Path -LiteralPath $stagingPath) {
            $stagingItem = Get-Item -LiteralPath $stagingPath -Force
            if (!$stagingItem.PSIsContainer -or ($stagingItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'FORWARD_RAW_DAILY_STAGING_ROOT_UNTRUSTED' }
            if (@(Get-ChildItem -LiteralPath $stagingPath -Force).Count -gt 0) { throw 'FORWARD_RAW_DAILY_STAGING_LEFTOVER_FAIL_CLOSED' }
        }

        $fetchDates = @($missing | Select-Object -First $script:ForwardRawDailyMaxFetchSessionsPerRun)
        $fetched = @()
        foreach ($sessionDate in $fetchDates) {
            $outputId = Get-ForwardRawDailyOutputId -SessionDate $sessionDate
            $outputPath = Join-Path $rootPath $outputId
            if (Test-Path -LiteralPath $outputPath) { throw "FORWARD_RAW_DAILY_OUTPUT_ALREADY_EXISTS_FAIL_CLOSED:$sessionDate" }
            if ($FetchAction) {
                $null = & $FetchAction $outputId $sessionDate $rootPath
            }
            else {
                $pwsh = Get-ForwardRawDailyPowerShellExecutable
                & $pwsh -NoLogo -NoProfile -File $Entrypoint -Mode ForwardRawFetch -StartDate $sessionDate -EndDate $sessionDate -ForwardRawOutputId $outputId
                if ($LASTEXITCODE -ne 0) { throw "FORWARD_RAW_DAILY_FETCH_FAILED_EXIT_${LASTEXITCODE}:$sessionDate" }
            }
            if (!(Test-ForwardRawDailyOutput -ForwardRawRoot $ForwardRawRoot -OutputId $outputId -SessionDate $sessionDate)) {
                throw "FORWARD_RAW_DAILY_FETCH_DID_NOT_PUBLISH_OUTPUT:$sessionDate"
            }
            $fetched += [pscustomobject]@{ SessionDate = $sessionDate; OutputId = $outputId; OutputPath = $outputPath }
        }
        $stillMissing = $missing.Count - $fetched.Count
        if ($stillMissing -gt 0) {
            return [pscustomobject]@{ Status = 'PARTIAL_BACKFILL_PENDING'; SessionDate = $fetched[-1].SessionDate; OutputId = $fetched[-1].OutputId; OutputPath = $fetched[-1].OutputPath; FetchedSessions = @($fetched); SkippedSessions = @($existing | ForEach-Object SessionDate); MissingSessions = @($missing | Select-Object -Skip $fetched.Count) }
        }
        $status = if ($fetched.Count -eq 1) { 'FORWARD_RAW_DAILY_FETCH_COMPLETE' } else { 'FORWARD_RAW_DAILY_BACKFILL_COMPLETE' }
        return [pscustomobject]@{ Status = $status; SessionDate = $fetched[-1].SessionDate; OutputId = $fetched[-1].OutputId; OutputPath = $fetched[-1].OutputPath; FetchedSessions = @($fetched); SkippedSessions = @($existing | ForEach-Object SessionDate); MissingSessions = @() }
    }
    finally {
        if ($ownsMutex) { $mutex.ReleaseMutex() }
        $mutex.Dispose()
    }
}

function Test-ForwardRawDailyCodexTemporaryPath {
    param([Parameter(Mandatory)][string]$Path)
    $normalized = $Path.Replace('/', '\')
    return $normalized -match '(?i)(?:^|\\)\.codex\\worktrees(?:\\|$)|(?:^|\\)\.cache\\codex-runtimes(?:\\|$)'
}

function Resolve-ForwardRawDailyTaskPlanPath {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][ValidateSet('PowerShellExecutable', 'RunnerScript')][string]$Kind
    )
    $kindName = $Kind.ToUpperInvariant()
    if (![IO.Path]::IsPathFullyQualified($Path)) { throw "TASK_PLAN_${kindName}_PATH_MUST_BE_ABSOLUTE" }
    $fullPath = [IO.Path]::GetFullPath($Path)
    if (Test-ForwardRawDailyCodexTemporaryPath -Path $fullPath) { throw "TASK_PLAN_CODEX_TEMPORARY_${kindName}_PATH_REJECTED" }
    if (!(Test-Path -LiteralPath $fullPath -PathType Leaf)) { throw "TASK_PLAN_${kindName}_FILE_MISSING" }
    if ($Kind -eq 'PowerShellExecutable' -and [IO.Path]::GetFileName($fullPath) -ine 'pwsh.exe') {
        throw 'TASK_PLAN_REQUIRES_POWERSHELL_7_PWSH_EXE'
    }
    if ($Kind -eq 'RunnerScript' -and [IO.Path]::GetExtension($fullPath) -ine '.ps1') { throw 'TASK_PLAN_RUNNER_MUST_BE_POWERSHELL_SCRIPT' }
    return $fullPath
}

function New-ForwardRawDailyTaskPlan {
    param(
        [Parameter(Mandatory)][ValidatePattern('^([01]\d|2[0-3]):[0-5]\d$')][string]$DailyAt,
        [Parameter(Mandatory)][string]$PowerShellExecutablePath,
        [Parameter(Mandatory)][string]$RunnerScriptPath,
        [string]$UserSid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    )
    $executablePath = Resolve-ForwardRawDailyTaskPlanPath -Path $PowerShellExecutablePath -Kind PowerShellExecutable
    $scriptPath = Resolve-ForwardRawDailyTaskPlanPath -Path $RunnerScriptPath -Kind RunnerScript
    $workingDirectory = [IO.Path]::GetDirectoryName($scriptPath)
    if (!(Test-Path -LiteralPath $workingDirectory -PathType Container)) { throw 'TASK_PLAN_WORKING_DIRECTORY_MISSING' }
    $triggerTime = [datetime]::ParseExact($DailyAt, 'HH:mm', [Globalization.CultureInfo]::InvariantCulture)
    $startBoundary = (Get-Date -Hour $triggerTime.Hour -Minute $triggerTime.Minute -Second 0).ToString('yyyy-MM-ddTHH:mm:ss', [Globalization.CultureInfo]::InvariantCulture)
    $escapedUser = [Security.SecurityElement]::Escape($UserSid)
    $escapedExecutable = [Security.SecurityElement]::Escape($executablePath)
    $escapedWorkingDirectory = [Security.SecurityElement]::Escape($workingDirectory)
    $arguments = [Security.SecurityElement]::Escape('-NoLogo -NoProfile -File "' + $scriptPath + '" -Mode Run')
    return @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo><Description>Review-only plan for AQ ForwardRawOnly daily collection. Disabled; do not register without separate approval.</Description></RegistrationInfo>
  <Triggers><CalendarTrigger><StartBoundary>$startBoundary</StartBoundary><Enabled>false</Enabled><ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay></CalendarTrigger></Triggers>
  <Principals><Principal id="Author"><UserId>$escapedUser</UserId><LogonType>InteractiveToken</LogonType><RunLevel>LeastPrivilege</RunLevel></Principal></Principals>
  <Settings><MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy><StartWhenAvailable>false</StartWhenAvailable><RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable><Enabled>false</Enabled><ExecutionTimeLimit>PT1H</ExecutionTimeLimit></Settings>
  <Actions Context="Author"><Exec><Command>$escapedExecutable</Command><Arguments>$arguments</Arguments><WorkingDirectory>$escapedWorkingDirectory</WorkingDirectory></Exec></Actions>
</Task>
"@
}

function Get-ForwardRawDailyProcessExitCode {
    param([Parameter(Mandatory)][string]$Status)
    switch ($Status) {
        { $_ -in @('FORWARD_RAW_DAILY_FETCH_COMPLETE', 'FORWARD_RAW_DAILY_BACKFILL_COMPLETE', 'SKIPPED_ALREADY_COMPLETE', 'SKIPPED_NON_TRADING_DAY', 'SKIPPED_SESSION_NOT_COMPLETE', 'SKIPPED_NO_COMPLETED_SESSIONS') } { return 0 }
        'PARTIAL_BACKFILL_PENDING' { return 2 }
        default { throw "FORWARD_RAW_DAILY_RESULT_STATUS_UNRECOGNIZED:$Status" }
    }
}

function Write-ForwardRawDailyResult {
    param([Parameter(Mandatory)]$Result)
    [Console]::Out.WriteLine(($Result | ConvertTo-Json -Depth 4))
    return Get-ForwardRawDailyProcessExitCode -Status ([string]$Result.Status)
}

if ($MyInvocation.InvocationName -eq '.') { return }

try {
    if ($Mode -eq 'TaskPlan') {
        if (!$DailyAt) { throw 'DAILY_TRIGGER_TIME_REQUIRED_FOR_TASK_PLAN' }
        if (!$PowerShellExecutablePath -or !$RunnerScriptPath) { throw 'TASK_PLAN_NOT_READY_STABLE_DEPLOYMENT_PATHS_REQUIRED' }
        Write-Output (New-ForwardRawDailyTaskPlan -DailyAt $DailyAt -PowerShellExecutablePath $PowerShellExecutablePath -RunnerScriptPath $RunnerScriptPath)
        exit 0
    }
    $result = Invoke-ForwardRawDaily
    exit (Write-ForwardRawDailyResult -Result $result)
}
catch {
    Write-Error ("FORWARD_RAW_DAILY_FAILED:{0}" -f $_.Exception.Message)
    exit 1
}
