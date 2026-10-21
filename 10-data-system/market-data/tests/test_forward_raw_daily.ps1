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
$root = Join-Path (Join-Path $env:LOCALAPPDATA 'Temp') ('aq-forward-raw-daily-tests-' + [guid]::NewGuid().ToString('N'))
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
    $pwshExecutable = Get-ForwardRawDailyPowerShellExecutable
    Assert-True ([IO.Path]::GetFullPath($pwshExecutable) -eq [IO.Path]::GetFullPath((Join-Path $PSHOME 'pwsh.exe'))) 'internal child process path is resolved from the active PowerShell 7 installation, not PATH'
    Assert-True (Test-Path -LiteralPath $pwshExecutable -PathType Leaf) 'resolved PowerShell 7 executable exists'
    try { Get-ForwardRawDailyPowerShellExecutable -Edition Desktop -Version ([version]'5.1') | Out-Null; throw 'EXPECTED_WINDOWS_POWERSHELL_REJECTION' }
    catch { Assert-True ($_.Exception.Message -match 'POWERSHELL_7_REQUIRED') 'Windows PowerShell 5.1 is rejected without fallback' }
    try { Get-ForwardRawDailyPowerShellExecutable -PowerShellHome (Join-Path $root 'missing-powershell-home') | Out-Null; throw 'EXPECTED_MISSING_PWSH_REJECTION' }
    catch { Assert-True ($_.Exception.Message -match 'POWERSHELL_7_EXECUTABLE_MISSING') 'missing PowerShell 7 executable fails closed' }
    $tests += 1

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
    $info.FileName = $pwshExecutable
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

    $stablePathSample = 'C:\Program Files\PowerShell\7\pwsh.exe'
    Assert-True (!(Test-ForwardRawDailyCodexTemporaryPath -Path $stablePathSample)) 'stable installation paths are not rejected based on the current Codex execution location'
    $stableRunnerDirectory = Join-Path $root 'Stable Deployment & Owner Review'
    $null = New-Item -ItemType Directory -Path $stableRunnerDirectory -Force
    $stableRunner = Join-Path $stableRunnerDirectory 'Invoke-ForwardRawDaily.ps1'
    Copy-Item -LiteralPath $runner -Destination $stableRunner
    Copy-Item -LiteralPath (Join-Path (Split-Path $runner -Parent) 'Update-AlpacaQlibResearchData.ps1') -Destination $stableRunnerDirectory
    Copy-Item -LiteralPath (Join-Path (Split-Path $runner -Parent) 'verify_alpaca_qlib_refresh.py') -Destination $stableRunnerDirectory
    $stableRunnerHash = (Get-FileHash -LiteralPath $stableRunner -Algorithm SHA256).Hash
    Assert-True (!(Test-ForwardRawDailyCodexTemporaryPath -Path $stableRunner)) 'stable-style runner path is not rejected merely because tests execute from a Codex worktree'
    Assert-True ((Resolve-ForwardRawDailyTaskPlanPath -Path $stableRunner -Kind RunnerScript) -eq [IO.Path]::GetFullPath($stableRunner)) 'stable daily runner and same-directory dependencies resolve'
    foreach ($temporaryPath in @(
        'C:\CodexFixture\.codex\worktrees\task\pwsh.exe',
        'C:\CodexFixture\.cache\codex-runtimes\runtime\pwsh.exe'
    )) {
        Assert-True (Test-ForwardRawDailyCodexTemporaryPath -Path $temporaryPath) "temporary path is recognized independent of the active worktree: $temporaryPath"
    }

    $fakeRunnerDirectory = Join-Path $root 'Fake Runner Fixture'
    $null = New-Item -ItemType Directory -Path $fakeRunnerDirectory -Force
    $fakeExecutableDirectory = Join-Path $fakeRunnerDirectory 'PowerShell 7'
    $null = New-Item -ItemType Directory -Path $fakeExecutableDirectory -Force
    $plannedPwsh = Join-Path $fakeExecutableDirectory 'pwsh.exe'
    [IO.File]::WriteAllText($plannedPwsh, 'test substitute; deliberately not executable')
    $plannedRunner = Join-Path $fakeRunnerDirectory 'Invoke-ForwardRawDaily.ps1'
    [IO.File]::WriteAllText($plannedRunner, '# test path fixture; not a deployment')
    [IO.File]::WriteAllText((Join-Path $fakeRunnerDirectory 'Update-AlpacaQlibResearchData.ps1'), '# test dependency')
    [IO.File]::WriteAllText((Join-Path $fakeRunnerDirectory 'verify_alpaca_qlib_refresh.py'), '# test dependency')
    Assert-True ((Get-FileHash -LiteralPath $stableRunner -Algorithm SHA256).Hash -eq $stableRunnerHash) 'fake runner fixture is separate and does not replace the valid stable runner fixture'

    Assert-True (Test-ForwardRawDailyPowerShell7Executable -Path $pwshExecutable) 'actual active PowerShell 7 executable passes bounded local version and edition probe'
    try {
        New-ForwardRawDailyTaskPlan -DailyAt '17:30' -PowerShellExecutablePath $plannedPwsh -RunnerScriptPath $plannedRunner | Out-Null
        throw 'EXPECTED_FAKE_PWSH_REJECTION'
    }
    catch { Assert-True ($_.Exception.Message -match 'VERSION_PROBE_FAILED') 'existing fake pwsh.exe is not accepted as a deployable runtime' }
    try {
        Resolve-ForwardRawDailyTaskPlanPath -Path $plannedRunner -Kind RunnerScript | Out-Null
        throw 'EXPECTED_FAKE_RUNNER_REJECTION'
    }
    catch { Assert-True ($_.Exception.Message -match 'RUNNER_CONTENT_NOT_RECOGNIZED') 'test runner fixture is not accepted as the actual daily entrypoint' }
    try {
        Resolve-ForwardRawDailyTaskPlanPath -Path 'C:\CodexFixture\.codex\worktrees\task\Invoke-ForwardRawDaily.ps1' -Kind RunnerScript | Out-Null
        throw 'EXPECTED_CODEX_RUNNER_PATH_REJECTION'
    }
    catch { Assert-True ($_.Exception.Message -match 'CODEX_TEMPORARY_RUNNERSCRIPT_PATH_REJECTED') 'explicit Codex worktree runner path is rejected independently of active worktree location' }

    # Serializer-only fixture: this XML check does not claim that its test paths are deployment-ready.
    $plan = [xml](New-ForwardRawDailyTaskPlanXml -DailyAt '17:30' -ExecutablePath 'C:\Program Files\PowerShell 7\pwsh.exe' -ScriptPath $stableRunner -UserSid ([Security.Principal.WindowsIdentity]::GetCurrent().User.Value))
    $ns = [Xml.XmlNamespaceManager]::new($plan.NameTable)
    $ns.AddNamespace('t', 'http://schemas.microsoft.com/windows/2004/02/mit/task')
    Assert-True ($plan.SelectSingleNode('//t:Actions/t:Exec/t:Command', $ns).InnerText -eq 'C:\Program Files\PowerShell 7\pwsh.exe') 'serialized XML command is the explicit absolute PowerShell 7 path'
    Assert-True ($plan.SelectSingleNode('//t:Actions/t:Exec/t:Arguments', $ns).InnerText.Contains('"' + [IO.Path]::GetFullPath($stableRunner) + '"')) 'TaskPlan arguments preserve the absolute runner path with spaces'
    Assert-True ($plan.SelectSingleNode('//t:Actions/t:Exec/t:WorkingDirectory', $ns).InnerText -eq [IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($stableRunner))) 'TaskPlan working directory exists and is the runner directory'
    Assert-True ($plan.SelectSingleNode('//t:MultipleInstancesPolicy', $ns).InnerText -eq 'IgnoreNew') 'Task Scheduler uses native IgnoreNew'
    Assert-True ($plan.SelectSingleNode('//t:Principal/t:LogonType', $ns).InnerText -eq 'InteractiveToken') 'task runs only in the original interactive user context'
    Assert-True ($plan.SelectSingleNode('//t:Principal/t:UserId', $ns).InnerText -eq [Security.Principal.WindowsIdentity]::GetCurrent().User.Value) 'task principal is the current user SID'
    Assert-True ($plan.SelectSingleNode('//t:Settings/t:Enabled', $ns).InnerText -eq 'false') 'plan is disabled and unregistered'
    Assert-True ($plan.SelectSingleNode('//t:Triggers/t:CalendarTrigger/t:Enabled', $ns).InnerText -eq 'false') 'plan trigger is disabled'
    Assert-True ($plan.SelectSingleNode('//t:Triggers/t:CalendarTrigger/t:ScheduleByDay/t:DaysInterval', $ns).InnerText -eq '1') 'plan describes a daily trigger'
    $tests += 1

    $invalidExecutablePaths = @(
        @{ path = 'pwsh.exe'; expected = 'PATH_MUST_BE_ABSOLUTE' },
        @{ path = (Join-Path $fakeRunnerDirectory 'missing\pwsh.exe'); expected = 'FILE_MISSING' },
        @{ path = 'C:\CodexFixture\.cache\codex-runtimes\runtime\pwsh.exe'; expected = 'CODEX_TEMPORARY_POWERSHELLEXECUTABLE_PATH_REJECTED' },
        @{ path = 'C:\CodexFixture\.codex\worktrees\task\pwsh.exe'; expected = 'CODEX_TEMPORARY_POWERSHELLEXECUTABLE_PATH_REJECTED' }
    )
    foreach ($invalid in $invalidExecutablePaths) {
        try {
            Resolve-ForwardRawDailyTaskPlanPath -Path $invalid.path -Kind PowerShellExecutable | Out-Null
            throw "EXPECTED_EXECUTABLE_PATH_REJECTION:$($invalid.expected)"
        }
        catch { Assert-True ($_.Exception.Message -match $invalid.expected) "TaskPlan rejects invalid executable path: $($invalid.expected); actual=$($_.Exception.Message)" }
        $tests += 1
    }
    [IO.File]::WriteAllText((Join-Path $fakeRunnerDirectory 'other-runner.ps1'), '# not the daily runner')
    $invalidRunnerPaths = @(
        @{ path = 'C:\CodexFixture\.codex\worktrees\task\Invoke-ForwardRawDaily.ps1'; expected = 'CODEX_TEMPORARY_RUNNERSCRIPT_PATH_REJECTED' },
        @{ path = (Join-Path $fakeRunnerDirectory 'missing-runner.ps1'); expected = 'FILE_MISSING' },
        @{ path = (Join-Path $fakeRunnerDirectory 'other-runner.ps1'); expected = 'RUNNER_MUST_BE_DAILY_RUNNER' },
        @{ path = $plannedRunner; expected = 'RUNNER_CONTENT_NOT_RECOGNIZED' }
    )
    foreach ($invalid in $invalidRunnerPaths) {
        try {
            Resolve-ForwardRawDailyTaskPlanPath -Path $invalid.path -Kind RunnerScript | Out-Null
            throw "EXPECTED_RUNNER_PATH_REJECTION:$($invalid.expected)"
        }
        catch { Assert-True ($_.Exception.Message -match $invalid.expected) "TaskPlan rejects invalid runner path: $($invalid.expected); actual=$($_.Exception.Message)" }
        $tests += 1
    }
    if (Test-ForwardRawDailyCodexTemporaryPath -Path $pwshExecutable) {
        try {
            New-ForwardRawDailyTaskPlan -DailyAt '17:30' -PowerShellExecutablePath $pwshExecutable -RunnerScriptPath $stableRunner | Out-Null
            throw 'EXPECTED_CODEX_RUNTIME_NOT_READY'
        }
        catch { Assert-True ($_.Exception.Message -match 'CODEX_TEMPORARY_POWERSHELLEXECUTABLE_PATH_REJECTED') 'active Codex runtime path is classified temporary and cannot be emitted as deployment-ready' }
    }
    else {
        $stableRuntimePlan = [xml](New-ForwardRawDailyTaskPlan -DailyAt '17:30' -PowerShellExecutablePath $pwshExecutable -RunnerScriptPath $stableRunner)
        $stableRuntimeNs = [Xml.XmlNamespaceManager]::new($stableRuntimePlan.NameTable)
        $stableRuntimeNs.AddNamespace('t', 'http://schemas.microsoft.com/windows/2004/02/mit/task')
        Assert-True ($stableRuntimePlan.SelectSingleNode('//t:Actions/t:Exec/t:Command', $stableRuntimeNs).InnerText -eq [IO.Path]::GetFullPath($pwshExecutable)) 'actual stable PowerShell 7 and complete runner are accepted'
        Assert-True ($stableRuntimePlan.SelectSingleNode('//t:Settings/t:Enabled', $stableRuntimeNs).InnerText -eq 'false') 'accepted TaskPlan remains disabled'
    }
    $tests += 1

    $exitHarness = Join-Path $root 'probe-process-exit-code.ps1'
    @'
param([string]$RunnerPath, [string]$Status)
. $RunnerPath -Mode Run
$result = [pscustomobject]@{ Status = $Status; SessionDate = '2026-10-20' }
try { exit (Write-ForwardRawDailyResult -Result $result) }
catch { [Console]::Error.WriteLine('PROBE_FAILED'); exit 1 }
'@ | Set-Content -LiteralPath $exitHarness -Encoding utf8
    foreach ($probe in @(
        @{ status = 'FORWARD_RAW_DAILY_FETCH_COMPLETE'; expected = 0 },
        @{ status = 'FORWARD_RAW_DAILY_BACKFILL_COMPLETE'; expected = 0 },
        @{ status = 'SKIPPED_ALREADY_COMPLETE'; expected = 0 },
        @{ status = 'PARTIAL_BACKFILL_PENDING'; expected = 2 },
        @{ status = 'UNKNOWN_TEST_STATUS'; expected = 1 }
    )) {
        $probeInfo = [Diagnostics.ProcessStartInfo]::new()
        $probeInfo.FileName = $pwshExecutable
        $probeInfo.UseShellExecute = $false
        $probeInfo.RedirectStandardOutput = $true
        $probeInfo.RedirectStandardError = $true
        foreach ($arg in @('-NoLogo', '-NoProfile', '-File', $exitHarness, $runner, $probe.status)) { $probeInfo.ArgumentList.Add($arg) }
        $probeProcess = [Diagnostics.Process]::Start($probeInfo)
        $probeStdout = $probeProcess.StandardOutput.ReadToEnd()
        $probeStderr = $probeProcess.StandardError.ReadToEnd()
        $probeProcess.WaitForExit()
        Assert-True ($probeProcess.ExitCode -eq $probe.expected) "separate PowerShell process exits $($probe.expected) for $($probe.status); stderr=$probeStderr"
        Assert-True ($probeStdout -match ('"Status"\s*:\s*"' + [regex]::Escape($probe.status) + '"')) "process preserves JSON status $($probe.status)"
        $probeProcess.Dispose()
        $tests += 1
    }

    $taskPlanProbe = [Diagnostics.ProcessStartInfo]::new()
    $taskPlanProbe.FileName = $pwshExecutable
    $taskPlanProbe.UseShellExecute = $false
    $taskPlanProbe.RedirectStandardOutput = $true
    $taskPlanProbe.RedirectStandardError = $true
    foreach ($arg in @('-NoLogo', '-NoProfile', '-File', $runner, '-Mode', 'TaskPlan', '-DailyAt', '17:30')) { $taskPlanProbe.ArgumentList.Add($arg) }
    $taskPlanProcess = [Diagnostics.Process]::Start($taskPlanProbe)
    $taskPlanStdout = $taskPlanProcess.StandardOutput.ReadToEnd()
    $taskPlanStderr = $taskPlanProcess.StandardError.ReadToEnd()
    $taskPlanProcess.WaitForExit()
    Assert-True ($taskPlanProcess.ExitCode -ne 0 -and $taskPlanStderr -match 'TASK_PLAN_NOT_READY_STABLE_DEPLOYMENT_PATHS_REQUIRED' -and !$taskPlanStdout.Contains('<Task')) 'TaskPlan without explicit stable paths fails closed and emits no deployable XML'
    $taskPlanProcess.Dispose()
    $tests += 1

    Write-Output "FORWARD_RAW_DAILY_TESTS_PASS:$tests"
}
finally {
    if (Test-Path -LiteralPath $root) { Remove-Item -LiteralPath $root -Recurse -Force }
    foreach ($path in $isolatedRoots) { if (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path -Recurse -Force } }
}
