[CmdletBinding()]
param(
    [ValidateSet('Run', 'TaskPlan')]
    [string]$Mode = 'Run',
    [string]$DailyAt
)

$ErrorActionPreference = 'Stop'
$script:ForwardRawDailyRoot = 'D:\AQ_DATA\FORWARD_RAW_ONLY'
$script:ForwardRawDailyMutexName = 'Global\AQ.ForwardRawOnly.Daily'
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

        if ($SessionResolver) { $resolution = & $SessionResolver $NowUtc }
        else { $resolution = Get-LastCompletedXnysSession -NowUtc $NowUtc }
        if ($resolution -is [string]) { $sessionDate = $resolution }
        elseif ($resolution.status -in @('SKIPPED_NON_TRADING_DAY', 'SKIPPED_SESSION_NOT_COMPLETE')) {
            return [pscustomobject]@{ Status = $resolution.status; SessionDate = $null; OutputId = $null; OutputPath = $null }
        }
        elseif ($resolution.status -eq 'SESSION_COMPLETE') { $sessionDate = ConvertTo-ForwardRawDateText $resolution.session }
        else { throw 'XNYS_SESSION_SELECTION_RESULT_INVALID' }
        $parsedDate = [datetime]::ParseExact($sessionDate, 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture)
        if ($parsedDate.Date -gt $NowUtc.UtcDateTime.Date) { throw 'FORWARD_RAW_DAILY_SESSION_IN_FUTURE' }
        $outputId = Get-ForwardRawDailyOutputId -SessionDate $sessionDate
        $rootPath = [IO.Path]::GetFullPath($ForwardRawRoot)
        if (!(Test-Path -LiteralPath $rootPath)) { $null = New-Item -ItemType Directory -Path $rootPath }
        $rootItem = Get-Item -LiteralPath $rootPath -Force
        if (!$rootItem.PSIsContainer -or ($rootItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'FORWARD_RAW_DAILY_ROOT_UNTRUSTED' }
        $outputPath = Join-Path $rootPath $outputId

        $existing = Find-ExistingForwardRawDailyOutput -ForwardRawRoot $ForwardRawRoot -SessionDate $sessionDate
        if ($existing) {
            return [pscustomobject]@{ Status = 'SKIPPED_ALREADY_COMPLETE'; SessionDate = $sessionDate; OutputId = $existing.OutputId; OutputPath = $existing.OutputPath }
        }

        $stagingPath = Join-Path $rootPath '.staging'
        if (Test-Path -LiteralPath $stagingPath) {
            $stagingItem = Get-Item -LiteralPath $stagingPath -Force
            if (!$stagingItem.PSIsContainer -or ($stagingItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'FORWARD_RAW_DAILY_STAGING_ROOT_UNTRUSTED' }
            if (@(Get-ChildItem -LiteralPath $stagingPath -Force).Count -gt 0) { throw 'FORWARD_RAW_DAILY_STAGING_LEFTOVER_FAIL_CLOSED' }
        }

        if ($FetchAction) {
            $null = & $FetchAction $outputId $sessionDate $rootPath
        }
        else {
            $pwsh = (Get-Command pwsh.exe -ErrorAction Stop).Source
            & $pwsh -NoLogo -NoProfile -File $Entrypoint -Mode ForwardRawFetch -StartDate $sessionDate -EndDate $sessionDate -ForwardRawOutputId $outputId
            if ($LASTEXITCODE -ne 0) { throw "FORWARD_RAW_DAILY_FETCH_FAILED_EXIT_$LASTEXITCODE" }
        }
        if (!(Test-ForwardRawDailyOutput -ForwardRawRoot $ForwardRawRoot -OutputId $outputId -SessionDate $sessionDate)) {
            throw 'FORWARD_RAW_DAILY_FETCH_DID_NOT_PUBLISH_OUTPUT'
        }
        return [pscustomobject]@{ Status = 'FORWARD_RAW_DAILY_FETCH_COMPLETE'; SessionDate = $sessionDate; OutputId = $outputId; OutputPath = $outputPath }
    }
    finally {
        if ($ownsMutex) { $mutex.ReleaseMutex() }
        $mutex.Dispose()
    }
}

function New-ForwardRawDailyTaskPlan {
    param(
        [Parameter(Mandatory)][ValidatePattern('^([01]\d|2[0-3]):[0-5]\d$')][string]$DailyAt,
        [string]$ScriptPath = $script:ForwardRawDailyRunner,
        [string]$UserSid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    )
    $triggerTime = [datetime]::ParseExact($DailyAt, 'HH:mm', [Globalization.CultureInfo]::InvariantCulture)
    $startBoundary = (Get-Date -Hour $triggerTime.Hour -Minute $triggerTime.Minute -Second 0).ToString('yyyy-MM-ddTHH:mm:ss', [Globalization.CultureInfo]::InvariantCulture)
    $escapedUser = [Security.SecurityElement]::Escape($UserSid)
    $escapedWorkingDirectory = [Security.SecurityElement]::Escape([IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($ScriptPath)))
    $arguments = [Security.SecurityElement]::Escape('-NoLogo -NoProfile -File "' + [IO.Path]::GetFullPath($ScriptPath) + '" -Mode Run')
    return @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo><Description>Review-only plan for AQ ForwardRawOnly daily collection. Disabled; do not register without separate approval.</Description></RegistrationInfo>
  <Triggers><CalendarTrigger><StartBoundary>$startBoundary</StartBoundary><Enabled>false</Enabled><ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay></CalendarTrigger></Triggers>
  <Principals><Principal id="Author"><UserId>$escapedUser</UserId><LogonType>InteractiveToken</LogonType><RunLevel>LeastPrivilege</RunLevel></Principal></Principals>
  <Settings><MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy><StartWhenAvailable>false</StartWhenAvailable><RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable><Enabled>false</Enabled><ExecutionTimeLimit>PT1H</ExecutionTimeLimit></Settings>
  <Actions Context="Author"><Exec><Command>pwsh.exe</Command><Arguments>$arguments</Arguments><WorkingDirectory>$escapedWorkingDirectory</WorkingDirectory></Exec></Actions>
</Task>
"@
}

if ($MyInvocation.InvocationName -eq '.') { return }

try {
    if ($Mode -eq 'TaskPlan') {
        if (!$DailyAt) { throw 'DAILY_TRIGGER_TIME_REQUIRED_FOR_TASK_PLAN' }
        Write-Output (New-ForwardRawDailyTaskPlan -DailyAt $DailyAt)
        exit 0
    }
    $result = Invoke-ForwardRawDaily
    $result | ConvertTo-Json -Depth 4
    exit 0
}
catch {
    Write-Error ("FORWARD_RAW_DAILY_FAILED:{0}" -f $_.Exception.Message)
    exit 1
}
