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
$isolatedRoots = [System.Collections.Generic.List[string]]::new()
function New-IsolatedForwardRawTestRoot([string]$Name) {
    $path = Join-Path ([IO.Path]::GetTempPath()) ('aq-forward-raw-daily-' + $Name + '-' + [guid]::NewGuid().ToString('N'))
    $null = New-Item -ItemType Directory -Path $path
    $script:isolatedRoots.Add($path)
    return $path
}
$singleRoot = New-IsolatedForwardRawTestRoot 'single'
$legacyRoot = Join-Path ([IO.Path]::GetTempPath()) ('aq-forward-raw-daily-legacy-' + [guid]::NewGuid().ToString('N'))
$overlapRoot = Join-Path ([IO.Path]::GetTempPath()) ('aq-forward-raw-daily-overlap-' + [guid]::NewGuid().ToString('N'))
$isolatedRoots.Add($legacyRoot)
$isolatedRoots.Add($overlapRoot)
$mutexName = 'Local\AQ.ForwardRawDaily.Tests.' + [guid]::NewGuid().ToString('N')
$null = New-Item -ItemType Directory -Path $root
try {
    $calendarSelection = Get-LastCompletedXnysSession -NowUtc ([datetimeoffset]'2026-10-20T20:01:00Z')
    Assert-True ($calendarSelection.status -eq 'SESSION_COMPLETE') 'PowerShell invokes the pinned XNYS helper and recognizes a completed close'
    Assert-True ((ConvertTo-ForwardRawDateText $calendarSelection.session) -eq '2026-10-20') 'calendar CLI returns the expected session date'
    $bufferedSessions = @(Get-CompletedXnysSessions -NowUtc ([datetimeoffset]'2026-10-20T20:14:00Z'))
    Assert-True (($bufferedSessions -join ',') -eq '2026-10-19') '15-minute close buffer excludes the current session until it has elapsed'
    $afterBufferSessions = @(Get-CompletedXnysSessions -NowUtc ([datetimeoffset]'2026-10-20T20:15:00Z'))
    Assert-True (($afterBufferSessions -join ',') -eq '2026-10-19,2026-10-20') 'enumeration returns every anchored completed session in order'
    $beforeAnchorClose = @(Get-CompletedXnysSessions -NowUtc ([datetimeoffset]'2026-10-19T20:14:00Z'))
    Assert-True ($beforeAnchorClose.Count -eq 0) 'no session is eligible before the anchored session close buffer'
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
        Assert-True ($OutputRoot -eq $singleRoot) 'writes only under the injected forward-only test root'
        Write-MockForwardOutput -Root $OutputRoot -OutputId $OutputId -SessionDate $Date
    }

    $first = Invoke-ForwardRawDaily -NowUtc ([datetimeoffset]'2026-10-20T20:01:00Z') -ForwardRawRoot $singleRoot -SessionResolver $resolver -FetchAction $fetch -MutexName $mutexName
    Assert-True ($first.Status -eq 'FORWARD_RAW_DAILY_FETCH_COMPLETE') 'mocked daily run completes'
    Assert-True ($first.OutputId -eq 'forwardraw-xnys-2026-10-19-aapl-msft') 'stable output id binds date and symbol scope'
    Assert-True ($calls -eq 1) 'one mocked fetch dispatch'
    $beforeHash = (Get-FileHash -LiteralPath (Join-Path $first.OutputPath 'AAPL.json') -Algorithm SHA256).Hash
    $second = Invoke-ForwardRawDaily -NowUtc ([datetimeoffset]'2026-10-20T20:02:00Z') -ForwardRawRoot $singleRoot -SessionResolver $resolver -FetchAction $fetch -MutexName $mutexName
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

    $legacyId = 'manual-forward-' + [guid]::NewGuid().ToString('N')
    Write-MockForwardOutput -Root $legacyRoot -OutputId $legacyId -SessionDate $sessionDate
    $callsBefore = $calls
    $legacySkip = Invoke-ForwardRawDaily -NowUtc ([datetimeoffset]'2026-10-20T20:01:00Z') -ForwardRawRoot $legacyRoot -SessionResolver $resolver -FetchAction $fetch -MutexName ($mutexName + 'legacy')
    Assert-True ($legacySkip.Status -eq 'SKIPPED_ALREADY_COMPLETE' -and $legacySkip.OutputId -eq $legacyId) 'existing valid same-day output is found regardless of its original output id'
    Assert-True ($calls -eq $callsBefore) 'legacy same-day output is not fetched again'
    $tests += 1

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

    $lateConflictRoot = New-IsolatedForwardRawTestRoot 'late-overlap-preflight'
    $lateConflictId = 'forwardraw-range-2026-10-21_2026-10-23'
    Write-MockForwardOutput -Root $lateConflictRoot -OutputId $lateConflictId -SessionDate '2026-10-21' -StartDate '2026-10-21' -EndDate '2026-10-23'
    $script:lateConflictCalls = 0
    $lateConflictFetch = { param($OutputId, $Date, $OutputRoot) $script:lateConflictCalls += 1; Write-MockForwardOutput -Root $OutputRoot -OutputId $OutputId -SessionDate $Date }
    $lateConflictResolution = { param($NowUtc, $Anchor, $Buffer) [pscustomobject]@{ status = 'SESSIONS_READY'; sessions = @('2026-10-20', '2026-10-21') } }
    try {
        Invoke-ForwardRawDaily -NowUtc ([datetimeoffset]'2026-10-21T20:30:00Z') -ForwardRawRoot $lateConflictRoot -SessionResolver $lateConflictResolution -FetchAction $lateConflictFetch -MutexName ($mutexName + 'late-conflict') | Out-Null
        throw 'EXPECTED_LATE_DATE_COVERAGE_CONFLICT'
    }
    catch { Assert-True ($_.Exception.Message -match 'DATE_COVERAGE_CONFLICT') 'later overlapping record fails the preflight' }
    Assert-True ($script:lateConflictCalls -eq 0) 'all sessions are checked before fetching an earlier missing session'
    $tests += 1

    # A: catch up only the current missing session when the prior session is complete.
    $normalRoot = New-IsolatedForwardRawTestRoot 'normal-latest-session'
    Write-MockForwardOutput -Root $normalRoot -OutputId (Get-ForwardRawDailyOutputId -SessionDate '2026-10-19') -SessionDate '2026-10-19'
    $script:normalCalls = [System.Collections.Generic.List[string]]::new()
    $normalFetch = { param($OutputId, $Date, $OutputRoot) $script:normalCalls.Add($Date); Write-MockForwardOutput -Root $OutputRoot -OutputId $OutputId -SessionDate $Date }
    $normalResolution = { param($NowUtc, $Anchor, $Buffer) [pscustomobject]@{ status = 'SESSIONS_READY'; sessions = @('2026-10-19', '2026-10-20') } }
    $normalResult = Invoke-ForwardRawDaily -NowUtc ([datetimeoffset]'2026-10-20T20:30:00Z') -ForwardRawRoot $normalRoot -SessionResolver $normalResolution -FetchAction $normalFetch -MutexName ($mutexName + 'normal')
    Assert-True ($normalResult.Status -eq 'FORWARD_RAW_DAILY_FETCH_COMPLETE') 'normal run fetches only a currently missing final session'
    Assert-True (($script:normalCalls -join ',') -eq '2026-10-20') 'normal run skips already stored prior session'
    Assert-True (($normalResult.SkippedSessions -join ',') -eq '2026-10-19') 'normal run reports the verified skipped session'
    $tests += 1

    # B: recover two missed sessions in chronological order.
    $twoRoot = New-IsolatedForwardRawTestRoot 'two-session-recovery'
    $script:twoCalls = [System.Collections.Generic.List[string]]::new()
    $twoFetch = { param($OutputId, $Date, $OutputRoot) $script:twoCalls.Add($Date); Write-MockForwardOutput -Root $OutputRoot -OutputId $OutputId -SessionDate $Date }
    $twoResolution = { param($NowUtc, $Anchor, $Buffer) [pscustomobject]@{ status = 'SESSIONS_READY'; sessions = @('2026-10-20', '2026-10-21') } }
    $twoResult = Invoke-ForwardRawDaily -NowUtc ([datetimeoffset]'2026-10-21T20:30:00Z') -ForwardRawRoot $twoRoot -SessionResolver $twoResolution -FetchAction $twoFetch -MutexName ($mutexName + 'two')
    Assert-True ($twoResult.Status -eq 'FORWARD_RAW_DAILY_BACKFILL_COMPLETE') 'two missing sessions complete as a bounded backfill'
    Assert-True (($script:twoCalls -join ',') -eq '2026-10-20,2026-10-21') 'two missed sessions fetch oldest first'
    $tests += 1

    # C: exactly three missing sessions fit the per-run dispatch bound.
    $threeRoot = New-IsolatedForwardRawTestRoot 'three-session-recovery'
    $script:threeCalls = [System.Collections.Generic.List[string]]::new()
    $threeFetch = { param($OutputId, $Date, $OutputRoot) $script:threeCalls.Add($Date); Write-MockForwardOutput -Root $OutputRoot -OutputId $OutputId -SessionDate $Date }
    $threeResolution = { param($NowUtc, $Anchor, $Buffer) [pscustomobject]@{ status = 'SESSIONS_READY'; sessions = @('2026-10-19', '2026-10-20', '2026-10-21') } }
    $threeResult = Invoke-ForwardRawDaily -NowUtc ([datetimeoffset]'2026-10-21T20:30:00Z') -ForwardRawRoot $threeRoot -SessionResolver $threeResolution -FetchAction $threeFetch -MutexName ($mutexName + 'three')
    Assert-True ($threeResult.Status -eq 'FORWARD_RAW_DAILY_BACKFILL_COMPLETE') 'three missing sessions fit the per-run bound'
    Assert-True (($script:threeCalls -join ',') -eq '2026-10-19,2026-10-20,2026-10-21') 'three sessions fetch chronologically'
    $tests += 1

    # The five-missing-session allowance is separate from the three-session per-run fetch cap.
    $fiveRoot = New-IsolatedForwardRawTestRoot 'five-session-bounded-recovery'
    $script:fiveCalls = [System.Collections.Generic.List[string]]::new()
    $fiveFetch = { param($OutputId, $Date, $OutputRoot) $script:fiveCalls.Add($Date); Write-MockForwardOutput -Root $OutputRoot -OutputId $OutputId -SessionDate $Date }
    $fiveDates = @('2026-10-19', '2026-10-20', '2026-10-21', '2026-10-22', '2026-10-23')
    $fiveResolution = { param($NowUtc, $Anchor, $Buffer) [pscustomobject]@{ status = 'SESSIONS_READY'; sessions = $fiveDates } }
    $fiveResult = Invoke-ForwardRawDaily -NowUtc ([datetimeoffset]'2026-10-23T20:30:00Z') -ForwardRawRoot $fiveRoot -SessionResolver $fiveResolution -FetchAction $fiveFetch -MutexName ($mutexName + 'five')
    Assert-True ($fiveResult.Status -eq 'PARTIAL_BACKFILL_PENDING') 'five missing sessions are accepted but reported partial after the per-run cap'
    Assert-True (($script:fiveCalls -join ',') -eq '2026-10-19,2026-10-20,2026-10-21') 'no more than three sessions are fetched in one run'
    Assert-True (($fiveResult.MissingSessions -join ',') -eq '2026-10-22,2026-10-23') 'unprocessed dates remain explicitly pending'
    $fiveReplay = Invoke-ForwardRawDaily -NowUtc ([datetimeoffset]'2026-10-23T20:31:00Z') -ForwardRawRoot $fiveRoot -SessionResolver $fiveResolution -FetchAction $fiveFetch -MutexName ($mutexName + 'five')
    Assert-True ($fiveReplay.Status -eq 'FORWARD_RAW_DAILY_BACKFILL_COMPLETE') 'next invocation resumes only still-missing sessions'
    Assert-True (($script:fiveCalls -join ',') -eq '2026-10-19,2026-10-20,2026-10-21,2026-10-22,2026-10-23') 'completed sessions are not fetched again on resume'
    $tests += 1

    # D: reject a gap larger than the five-session lookback before any fetch.
    $tooManyRoot = New-IsolatedForwardRawTestRoot 'too-many-sessions'
    $script:tooManyCalls = 0
    $tooManyFetch = { param($OutputId, $Date, $OutputRoot) $script:tooManyCalls += 1 }
    $tooManyResolution = { param($NowUtc, $Anchor, $Buffer) [pscustomobject]@{ status = 'SESSIONS_READY'; sessions = @('2026-10-19', '2026-10-20', '2026-10-21', '2026-10-22', '2026-10-23', '2026-10-26') } }
    try {
        Invoke-ForwardRawDaily -NowUtc ([datetimeoffset]'2026-10-26T20:30:00Z') -ForwardRawRoot $tooManyRoot -SessionResolver $tooManyResolution -FetchAction $tooManyFetch -MutexName ($mutexName + 'too-many') | Out-Null
        throw 'EXPECTED_MISSING_SESSION_LIMIT'
    }
    catch { Assert-True ($_.Exception.Message -match 'MISSING_SESSION_LIMIT_EXCEEDED:6:5') 'more than five missing sessions fails closed with exact count' }
    Assert-True ($script:tooManyCalls -eq 0) 'over-limit gap is rejected before any fetch'
    $tests += 1

    # E: a weekend invocation still enumerates and recovers Friday sessions.
    $weekendRoot = New-IsolatedForwardRawTestRoot 'weekend-recovery'
    $script:weekendCalls = [System.Collections.Generic.List[string]]::new()
    $weekendFetch = { param($OutputId, $Date, $OutputRoot) $script:weekendCalls.Add($Date); Write-MockForwardOutput -Root $OutputRoot -OutputId $OutputId -SessionDate $Date }
    $weekendResolution = { param($NowUtc, $Anchor, $Buffer) [pscustomobject]@{ status = 'SESSIONS_READY'; sessions = @('2026-10-22', '2026-10-23') } }
    $weekendResult = Invoke-ForwardRawDaily -NowUtc ([datetimeoffset]'2026-10-24T16:00:00Z') -ForwardRawRoot $weekendRoot -SessionResolver $weekendResolution -FetchAction $weekendFetch -MutexName ($mutexName + 'weekend')
    Assert-True ($weekendResult.Status -eq 'FORWARD_RAW_DAILY_BACKFILL_COMPLETE') 'weekend invocation recovers the last missing XNYS sessions'
    Assert-True (($script:weekendCalls -join ',') -eq '2026-10-22,2026-10-23') 'weekend recovery runs missing sessions in order'
    $tests += 1

    # F/K: the calendar helper handles holidays, early closes, DST and preserves the research cutoff.
    $holidaySessions = @(Get-CompletedXnysSessions -NowUtc ([datetimeoffset]'2026-11-27T18:15:00Z') -StartDate '2026-11-25')
    Assert-True (($holidaySessions -join ',') -eq '2026-11-25,2026-11-27') 'XNYS enumeration excludes Thanksgiving and respects early close plus buffer'
    $tests += 1

    # I: failure on the second simulated session halts immediately without retrying it or starting the third.
    $partialRoot = New-IsolatedForwardRawTestRoot 'partial-429-recovery'
    $script:partialCalls = [System.Collections.Generic.List[string]]::new()
    $partialFetch = {
        param($OutputId, $Date, $OutputRoot)
        $script:partialCalls.Add($Date)
        if ($Date -eq '2026-10-20') { throw 'MOCK_HTTP_429' }
        Write-MockForwardOutput -Root $OutputRoot -OutputId $OutputId -SessionDate $Date
    }
    $partialResolution = { param($NowUtc, $Anchor, $Buffer) [pscustomobject]@{ status = 'SESSIONS_READY'; sessions = @('2026-10-19', '2026-10-20', '2026-10-21') } }
    try {
        Invoke-ForwardRawDaily -NowUtc ([datetimeoffset]'2026-10-21T20:30:00Z') -ForwardRawRoot $partialRoot -SessionResolver $partialResolution -FetchAction $partialFetch -MutexName ($mutexName + 'partial') | Out-Null
        throw 'EXPECTED_PARTIAL_429_FAILURE'
    }
    catch { Assert-True ($_.Exception.Message -match 'MOCK_HTTP_429') 'HTTP 429 fails the run immediately' }
    Assert-True (($script:partialCalls -join ',') -eq '2026-10-19,2026-10-20') '429 prevents third session and is not retried'
    Assert-True (Test-Path -LiteralPath (Join-Path $partialRoot (Get-ForwardRawDailyOutputId -SessionDate '2026-10-19'))) 'previously completed session remains valid after later failure'
    Assert-True (!(Test-Path -LiteralPath (Join-Path $partialRoot (Get-ForwardRawDailyOutputId -SessionDate '2026-10-21')))) 'third session is not started after failure'
    $tests += 1

    $incompleteId = Get-ForwardRawDailyOutputId -SessionDate '2026-10-20'
    $incompletePath = Join-Path $root $incompleteId
    $null = New-Item -ItemType Directory -Path $incompletePath
    Set-Content -LiteralPath (Join-Path $incompletePath 'manifest.json') -Value '{"status":"INCOMPLETE","start":"2026-10-20","end":"2026-10-20"}'
    $callsBefore = $calls
    try {
        Invoke-ForwardRawDaily -NowUtc ([datetimeoffset]'2026-10-20T20:30:00Z') -ForwardRawRoot $root -SessionResolver { param($NowUtc) '2026-10-20' } -FetchAction $fetch -MutexName $mutexName | Out-Null
        throw 'EXPECTED_INCOMPLETE_FAIL_CLOSED'
    }
    catch { Assert-True ($_.Exception.Message -match 'EXISTING_OUTPUT') ("incomplete output fails closed, got: " + $_.Exception.Message) }
    Assert-True ($calls -eq $callsBefore) 'incomplete output is never refetched'
    $tests += 1

    foreach ($failureName in @('403', '429', 'timeout')) {
        $failureRoot = New-IsolatedForwardRawTestRoot ('failure-' + $failureName)
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

    $leftoverRoot = New-IsolatedForwardRawTestRoot 'leftover-stage'
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
    $concurrentRoot = New-IsolatedForwardRawTestRoot 'concurrent'
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
            Invoke-ForwardRawDaily -NowUtc ([datetimeoffset]'2026-10-20T20:01:00Z') -ForwardRawRoot $concurrentRoot -SessionResolver $resolver -FetchAction $fetch -MutexName $mutexName | Out-Null
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
    foreach ($path in $isolatedRoots) { if (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path -Recurse -Force } }
}
