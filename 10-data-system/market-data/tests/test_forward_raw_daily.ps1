$ErrorActionPreference = 'Stop'
$runner = Join-Path $PSScriptRoot '..\Invoke-ForwardRawDaily.ps1'
. $runner -Mode Run

function Assert-True([bool]$Condition, [string]$Message) {
    if (!$Condition) { throw "ASSERTION_FAILED:$Message" }
}

function Write-MockForwardOutput([string]$Root, [string]$OutputId, [string]$SessionDate, [string]$StartDate = $SessionDate, [string]$EndDate = $SessionDate) {
    $destination = Join-Path $Root $OutputId
    $null = New-Item -ItemType Directory -Path $destination
    $symbols = @()
    $responses = @()
    $barDates = @()
    $rangeStart = [datetime]::ParseExact($StartDate, 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture)
    $rangeEnd = [datetime]::ParseExact($EndDate, 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture)
    for ($date = $rangeStart; $date -le $rangeEnd; $date = $date.AddDays(1)) {
        if ($date.DayOfWeek -notin @([DayOfWeek]::Saturday, [DayOfWeek]::Sunday)) { $barDates += $date.ToString('yyyy-MM-dd') }
    }
    foreach ($symbol in @('AAPL', 'MSFT')) {
        $bars = @($barDates | ForEach-Object { @{ t = "${_}T00:00:00Z"; o = 100.0; h = 101.0; l = 99.0; c = 100.5; v = 1000.0 } })
        $payload = @{ bars = $bars } | ConvertTo-Json -Compress -Depth 4
        $bytes = [Text.Encoding]::UTF8.GetBytes($payload)
        $path = Join-Path $destination ($symbol + '.json')
        [IO.File]::WriteAllBytes($path, $bytes)
        $hash = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
        $symbols += [pscustomobject]@{ symbol = $symbol; bars = $bars.Count; first_date = $barDates[0]; last_date = $barDates[-1]; bytes = $bytes.Length; sha256 = $hash }
        $responses += [pscustomobject]@{ symbol = $symbol; http_status = 200; bar_count = $bars.Count; first_date = $barDates[0]; last_date = $barDates[-1]; response_bytes = $bytes.Length; response_sha256 = $hash }
    }
    $manifest = [ordered]@{
        status = 'FORWARD_RAW_FETCH_COMPLETE'
        source_attestation = 'CONTROLLED_ALPACA_FETCH_BY_EXISTING_ENTRYPOINT'
        storage_class = 'FORWARD_RAW_ONLY'
        qlib_conversion = $false
        p3_research_access = $false
        p2_certification_authority = $false
        training_or_trading_authority = $false
        start = $StartDate
        end = $EndDate
        symbols = $symbols
        acquisition = [ordered]@{
            provider = 'Alpaca Market Data API'
            request_count = 2
            parameters = [ordered]@{ timeframe = '1Day'; start = "${SessionDate}T00:00:00Z"; end = "${SessionDate}T23:59:59Z"; feed = 'sip'; adjustment = 'raw'; asof = '-'; limit = 10000 }
            responses = $responses
        }
    }
    $manifest | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $destination 'manifest.json') -Encoding utf8
}

$tests = 0
$root = Join-Path ([IO.Path]::GetTempPath()) ('aq-forward-raw-daily-tests-' + [guid]::NewGuid().ToString('N'))
$mutexName = 'Local\AQ.ForwardRawDaily.Tests.' + [guid]::NewGuid().ToString('N')
$null = New-Item -ItemType Directory -Path $root
try {
    $calendarSelection = Get-LastCompletedXnysSession -NowUtc ([datetimeoffset]'2026-10-20T20:01:00Z')
    Assert-True ($calendarSelection.status -eq 'SESSION_COMPLETE') 'PowerShell invokes the pinned XNYS helper and recognizes a completed close'
    Assert-True ((ConvertTo-ForwardRawDateText $calendarSelection.session) -eq '2026-10-20') 'calendar CLI returns the expected session date'
    $calendarSkip = Get-LastCompletedXnysSession -NowUtc ([datetimeoffset]'2026-10-24T16:00:00Z')
    Assert-True ($calendarSkip.status -eq 'SKIPPED_NON_TRADING_DAY') 'calendar CLI skips weekend without falling back to Friday'
    $tests += 1

    $sessionDate = '2026-10-19'
    $id = Get-ForwardRawDailyOutputId -SessionDate $sessionDate
    $calls = 0
    $resolver = { param($NowUtc) $sessionDate }
    $fetch = {
        param($OutputId, $Date, $OutputRoot)
        $script:calls += 1
        Assert-True ($OutputRoot -eq $root) 'writes only under the injected forward-only test root'
        Write-MockForwardOutput -Root $OutputRoot -OutputId $OutputId -SessionDate $Date
    }

    $first = Invoke-ForwardRawDaily -NowUtc ([datetimeoffset]'2026-10-20T20:01:00Z') -ForwardRawRoot $root -SessionResolver $resolver -FetchAction $fetch -MutexName $mutexName
    Assert-True ($first.Status -eq 'FORWARD_RAW_DAILY_FETCH_COMPLETE') 'mocked daily run completes'
    Assert-True ($first.OutputId -eq 'forwardraw-xnys-2026-10-19-aapl-msft') 'stable output id binds date and symbol scope'
    Assert-True ($calls -eq 1) 'one mocked fetch dispatch'
    $beforeHash = (Get-FileHash -LiteralPath (Join-Path $first.OutputPath 'AAPL.json') -Algorithm SHA256).Hash
    $second = Invoke-ForwardRawDaily -NowUtc ([datetimeoffset]'2026-10-20T20:02:00Z') -ForwardRawRoot $root -SessionResolver $resolver -FetchAction $fetch -MutexName $mutexName
    $afterHash = (Get-FileHash -LiteralPath (Join-Path $first.OutputPath 'AAPL.json') -Algorithm SHA256).Hash
    Assert-True ($second.Status -eq 'SKIPPED_ALREADY_COMPLETE') 'completed day is skipped'
    Assert-True ($calls -eq 1) 'skip performs no extra dispatch'
    Assert-True ($beforeHash -eq $afterHash) 'replay does not overwrite output'
    $tests += 1

    foreach ($skipStatus in @('SKIPPED_NON_TRADING_DAY', 'SKIPPED_SESSION_NOT_COMPLETE')) {
        $callsBefore = $calls
        $skipResolver = { param($NowUtc) [pscustomobject]@{ status = $skipStatus } }
        $skipped = Invoke-ForwardRawDaily -NowUtc ([datetimeoffset]'2026-10-24T16:00:00Z') -ForwardRawRoot $root -SessionResolver $skipResolver -FetchAction $fetch -MutexName ($mutexName + $skipStatus)
        Assert-True ($skipped.Status -eq $skipStatus) "$skipStatus skips without choosing an earlier session"
        Assert-True ($calls -eq $callsBefore) "$skipStatus makes no fetch call"
        $tests += 1
    }

    $legacyRoot = Join-Path $root 'legacy-output-id'
    $legacyId = 'manual-forward-' + [guid]::NewGuid().ToString('N')
    Write-MockForwardOutput -Root $legacyRoot -OutputId $legacyId -SessionDate $sessionDate
    $callsBefore = $calls
    $legacySkip = Invoke-ForwardRawDaily -NowUtc ([datetimeoffset]'2026-10-20T20:01:00Z') -ForwardRawRoot $legacyRoot -SessionResolver $resolver -FetchAction $fetch -MutexName ($mutexName + 'legacy')
    Assert-True ($legacySkip.Status -eq 'SKIPPED_ALREADY_COMPLETE' -and $legacySkip.OutputId -eq $legacyId) 'existing valid same-day output is found regardless of its original output id'
    Assert-True ($calls -eq $callsBefore) 'legacy same-day output is not fetched again'
    $tests += 1

    $overlapRoot = Join-Path $root 'overlapping-multiday-output'
    $overlapId = 'forwardraw-range-2026-10-19_2026-10-23'
    Write-MockForwardOutput -Root $overlapRoot -OutputId $overlapId -SessionDate '2026-10-21' -StartDate '2026-10-19' -EndDate '2026-10-23'
    $overlapManifestPath = Join-Path $overlapRoot "$overlapId\manifest.json"
    $overlapDataPath = Join-Path $overlapRoot "$overlapId\AAPL.json"
    $overlapManifestHash = (Get-FileHash -LiteralPath $overlapManifestPath -Algorithm SHA256).Hash
    $overlapDataHash = (Get-FileHash -LiteralPath $overlapDataPath -Algorithm SHA256).Hash
    $callsBefore = $calls
    try {
        Invoke-ForwardRawDaily -NowUtc ([datetimeoffset]'2026-10-22T20:01:00Z') -ForwardRawRoot $overlapRoot -SessionResolver { param($NowUtc) '2026-10-21' } -FetchAction $fetch -MutexName ($mutexName + 'overlap') | Out-Null
        throw 'EXPECTED_DATE_COVERAGE_CONFLICT'
    }
    catch { Assert-True ($_.Exception.Message -match 'FORWARD_RAW_DAILY_EXISTING_DATE_COVERAGE_CONFLICT:.*2026-10-19\.\.2026-10-23:2026-10-21') 'overlapping multi-day output fails closed with the covered range' }
    Assert-True ($calls -eq $callsBefore) 'overlapping multi-day output performs no fetch'
    Assert-True ((Get-FileHash -LiteralPath $overlapManifestPath -Algorithm SHA256).Hash -eq $overlapManifestHash) 'overlap detection preserves the existing manifest'
    Assert-True ((Get-FileHash -LiteralPath $overlapDataPath -Algorithm SHA256).Hash -eq $overlapDataHash) 'overlap detection preserves existing raw data'
    $tests += 1

    $incompleteId = Get-ForwardRawDailyOutputId -SessionDate '2026-10-16'
    $incompletePath = Join-Path $root $incompleteId
    $null = New-Item -ItemType Directory -Path $incompletePath
    Set-Content -LiteralPath (Join-Path $incompletePath 'manifest.json') -Value '{"status":"INCOMPLETE","start":"2026-10-16","end":"2026-10-16"}'
    $callsBefore = $calls
    try {
        Invoke-ForwardRawDaily -NowUtc ([datetimeoffset]'2026-10-19T20:01:00Z') -ForwardRawRoot $root -SessionResolver { param($NowUtc) '2026-10-16' } -FetchAction $fetch -MutexName $mutexName | Out-Null
        throw 'EXPECTED_INCOMPLETE_FAIL_CLOSED'
    }
    catch { Assert-True ($_.Exception.Message -match 'EXISTING_OUTPUT') 'incomplete output fails closed' }
    Assert-True ($calls -eq $callsBefore) 'incomplete output is never refetched'
    $tests += 1

    foreach ($failureName in @('403', '429', 'timeout')) {
        $failureRoot = Join-Path $root ('failure-' + $failureName)
        $attempts = 0
        $failureAction = {
            param($OutputId, $Date, $OutputRoot)
            $script:attempts += 1
            throw "MOCK_HTTP_$failureName"
        }
        try {
            Invoke-ForwardRawDaily -NowUtc ([datetimeoffset]'2026-10-20T20:01:00Z') -ForwardRawRoot $failureRoot -SessionResolver $resolver -FetchAction $failureAction -MutexName ($mutexName + $failureName) | Out-Null
            throw "EXPECTED_FAILURE_$failureName"
        }
        catch { Assert-True ($_.Exception.Message -match "MOCK_HTTP_$failureName") "$failureName failure is surfaced" }
        Assert-True ($attempts -eq 1) "$failureName is not retried"
        Assert-True (!(Test-Path -LiteralPath (Join-Path $failureRoot $id))) "$failureName does not create success output"
        $tests += 1
    }

    $leftoverRoot = Join-Path $root 'leftover-stage'
    $stage = Join-Path $leftoverRoot '.staging\interrupted-attempt'
    $null = New-Item -ItemType Directory -Path $stage -Force
    Set-Content -LiteralPath (Join-Path $stage 'AAPL.json') -Value 'partial'
    $callsBefore = $calls
    try {
        Invoke-ForwardRawDaily -NowUtc ([datetimeoffset]'2026-10-20T20:01:00Z') -ForwardRawRoot $leftoverRoot -SessionResolver $resolver -FetchAction $fetch -MutexName ($mutexName + 'leftover') | Out-Null
        throw 'EXPECTED_LEFTOVER_FAIL_CLOSED'
    }
    catch { Assert-True ($_.Exception.Message -match 'STAGING_LEFTOVER_FAIL_CLOSED') 'interrupted stage fails closed' }
    Assert-True ($calls -eq $callsBefore) 'leftover stage does not dispatch again'
    $tests += 1

    $holderScript = Join-Path $root 'hold-mutex.ps1'
    @'
param([string]$MutexName, [string]$ReadyPath, [string]$ReleasePath)
$m = [Threading.Mutex]::new($false, $MutexName)
try {
    $null = $m.WaitOne()
    [IO.File]::WriteAllText($ReadyPath, 'ready')
    while (!(Test-Path -LiteralPath $ReleasePath)) { Start-Sleep -Milliseconds 50 }
}
finally { $m.ReleaseMutex(); $m.Dispose() }
'@ | Set-Content -LiteralPath $holderScript -Encoding utf8
    $readyPath = Join-Path $root 'mutex-ready'
    $releasePath = Join-Path $root 'mutex-release'
    $info = [Diagnostics.ProcessStartInfo]::new()
    $info.FileName = (Get-Command pwsh.exe).Source
    foreach ($arg in @('-NoLogo', '-NoProfile', '-File', $holderScript, $mutexName, $readyPath, $releasePath)) { $info.ArgumentList.Add($arg) }
    $holder = [Diagnostics.Process]::Start($info)
    try {
        $deadline = [datetime]::UtcNow.AddSeconds(10)
        while (!(Test-Path -LiteralPath $readyPath) -and [datetime]::UtcNow -lt $deadline) { Start-Sleep -Milliseconds 50 }
        Assert-True (Test-Path -LiteralPath $readyPath) 'second process acquired the native mutex'
        $callsBefore = $calls
        try {
            Invoke-ForwardRawDaily -NowUtc ([datetimeoffset]'2026-10-20T20:01:00Z') -ForwardRawRoot $root -SessionResolver $resolver -FetchAction $fetch -MutexName $mutexName | Out-Null
            throw 'EXPECTED_MUTEX_REJECTION'
        }
        catch { Assert-True ($_.Exception.Message -match 'ALREADY_RUNNING') 'concurrent daily run is rejected' }
        Assert-True ($calls -eq $callsBefore) 'concurrency rejection performs no fetch'
        $tests += 1
    }
    finally {
        [IO.File]::WriteAllText($releasePath, 'release')
        if (!$holder.WaitForExit(10000)) { $holder.Kill(); throw 'MUTEX_HOLDER_DID_NOT_EXIT' }
    }

    $plan = [xml](New-ForwardRawDailyTaskPlan -DailyAt '17:30')
    $ns = [Xml.XmlNamespaceManager]::new($plan.NameTable)
    $ns.AddNamespace('t', 'http://schemas.microsoft.com/windows/2004/02/mit/task')
    Assert-True ($plan.SelectSingleNode('//t:MultipleInstancesPolicy', $ns).InnerText -eq 'IgnoreNew') 'Task Scheduler uses native IgnoreNew'
    Assert-True ($plan.SelectSingleNode('//t:Principal/t:LogonType', $ns).InnerText -eq 'InteractiveToken') 'task runs only in the original interactive user context'
    Assert-True ($plan.SelectSingleNode('//t:Principal/t:UserId', $ns).InnerText -eq [Security.Principal.WindowsIdentity]::GetCurrent().User.Value) 'task principal is the current user SID'
    Assert-True ($plan.SelectSingleNode('//t:Settings/t:Enabled', $ns).InnerText -eq 'false') 'plan is disabled and unregistered'
    Assert-True ($plan.SelectSingleNode('//t:Triggers/t:CalendarTrigger/t:Enabled', $ns).InnerText -eq 'false') 'plan trigger is disabled'
    Assert-True ($plan.SelectSingleNode('//t:Triggers/t:CalendarTrigger/t:ScheduleByDay/t:DaysInterval', $ns).InnerText -eq '1') 'plan describes a daily trigger'
    $tests += 1

    Write-Output "FORWARD_RAW_DAILY_TESTS_PASS:$tests"
}
finally {
    if (Test-Path -LiteralPath $root) { Remove-Item -LiteralPath $root -Recurse -Force }
}
