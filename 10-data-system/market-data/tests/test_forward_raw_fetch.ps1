using namespace System.Net
using namespace System.Net.Http
using namespace System.Threading
using namespace System.Threading.Tasks

Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;

public sealed class ForwardRawTestHandler : HttpMessageHandler
{
    private readonly Queue<object> _responses;
    public readonly List<string> Requests = new List<string>();
    public ForwardRawTestHandler(IEnumerable<object> responses) { _responses = new Queue<object>(responses); }
    protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        Requests.Add(request.RequestUri.ToString());
        var item = _responses.Dequeue();
        if (item is Exception error) throw error;
        return Task.FromResult((HttpResponseMessage)item);
    }
}
'@

$entrypoint = Join-Path $PSScriptRoot '..\Update-AlpacaQlibResearchData.ps1'
. $entrypoint -Mode ForwardRawFetch
$ScriptDir = Split-Path -Parent (Resolve-Path -LiteralPath $entrypoint).Path
$CalendarPython = '/home/zhou/AQ_ENVS/p6-macro-v1/bin/python'

function Assert-True([bool]$Condition, [string]$Message) {
    if (!$Condition) { throw "ASSERTION_FAILED:$Message" }
}

function New-TestResponse([int]$StatusCode, [string]$Body) {
    $response = [HttpResponseMessage]::new([HttpStatusCode]$StatusCode)
    $response.Content = [StringContent]::new($Body, [Text.Encoding]::UTF8, 'application/json')
    return $response
}

function New-TestClient([object[]]$Items) {
    $handler = [ForwardRawTestHandler]::new($Items)
    return [pscustomobject]@{ Client = [HttpClient]::new($handler); Handler = $handler }
}

function New-TestStagePath([string]$Root, [string]$Name) {
    return Join-Path (Join-Path $Root '.staging') $Name
}

function New-BarPayload([string]$Symbol) {
    $bar = @{ t = '2026-09-14T00:00:00Z'; o = 100; h = 101; l = 99; c = 100.5; v = 1234 }
    return @{ bars = @($bar) } | ConvertTo-Json -Compress -Depth 4
}

function New-TestStoreAction {
    return {
        param($RawDir, $OutputId, $Start, $End, $Symbols, $Root)
        $destination = Join-Path $Root $OutputId
        $null = New-Item -ItemType Directory -Path $destination
        $records = @()
        foreach ($symbol in $Symbols) {
            $rawPath = Join-Path $RawDir ($symbol + '.json')
            $bytes = [IO.File]::ReadAllBytes($rawPath)
            [IO.File]::WriteAllBytes((Join-Path $destination ($symbol + '.json')), $bytes)
            $payload = [Text.Encoding]::UTF8.GetString($bytes) | ConvertFrom-Json
            $records += [pscustomobject]@{
                symbol = $symbol; bars = $payload.bars.Count; first_date = '2026-09-14'; last_date = '2026-09-14'
                sha256 = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)).ToLowerInvariant()
            }
        }
        $manifest = [ordered]@{ status = 'FORWARD_RAW_ONLY_COMPLETE'; source_attestation = 'UNVERIFIED_INPUT_PAYLOAD'; start = $Start; end = $End; symbols = $records }
        $manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $destination 'manifest.json') -Encoding utf8
        return [pscustomobject]@{ status = 'FORWARD_RAW_ONLY_COMPLETE' }
    }
}

$testsRun = 0
$root = Join-Path ([IO.Path]::GetTempPath()) ('aq-forward-raw-tests-' + [guid]::NewGuid().ToString('N'))
$successfulOutputId = 'mock-200-' + [guid]::NewGuid().ToString('N')
$forwardRoot = 'D:\AQ_DATA\FORWARD_RAW_ONLY'
$successfulDestination = Join-Path $forwardRoot $successfulOutputId
$successfulStage = New-TestStagePath $forwardRoot ('test-' + [guid]::NewGuid().ToString('N'))
$null = New-Item -ItemType Directory -Path $root
try {
    # A successful mocked pair reaches the existing raw-only storage step and
    # records the exact fetched response identities in its manifest.
    $clientInfo = New-TestClient @(
        (New-TestResponse 200 (New-BarPayload 'AAPL')),
        (New-TestResponse 200 (New-BarPayload 'MSFT'))
    )
    $result = Invoke-ForwardRawFetch -OutputId $successfulOutputId -Start '2026-09-14' -End '2026-09-14' -StagingDirectory $successfulStage -Client $clientInfo.Client -Credential ([pscustomobject]@{ Key = 'TEST'; Secret = 'TEST' })
    $manifest = Get-Content -LiteralPath (Join-Path $successfulDestination 'manifest.json') -Raw | ConvertFrom-Json
    Assert-True ($result.Status -eq 'FORWARD_RAW_FETCH_COMPLETE') 'success result status'
    Assert-True ($clientInfo.Handler.Requests.Count -eq 2) 'one request per approved symbol'
    Assert-True ($clientInfo.Handler.Requests[0] -like 'https://data.alpaca.markets/v2/stocks/AAPL/bars?*') 'fixed Alpaca host and AAPL endpoint'
    Assert-True ($clientInfo.Handler.Requests[1] -like 'https://data.alpaca.markets/v2/stocks/MSFT/bars?*') 'fixed Alpaca host and MSFT endpoint'
    Assert-True ($clientInfo.Handler.Requests[0] -match 'timeframe=1Day.*feed=sip.*adjustment=raw.*asof=-.*limit=10000') 'fixed historical bars query'
    Assert-True ($clientInfo.Handler.Requests[0] -match 'start=2026-09-14T00%3A00%3A00Z.*end=2026-09-14T23%3A59%3A59Z') 'bounded UTC range in request'
    Assert-True ($manifest.status -eq 'FORWARD_RAW_FETCH_COMPLETE') 'fetch terminal manifest status'
    Assert-True ($manifest.source_attestation -eq 'CONTROLLED_ALPACA_FETCH_BY_EXISTING_ENTRYPOINT') 'controlled source marker'
    Assert-True ($manifest.acquisition.request_count -eq 2) 'request count in manifest'
    Assert-True ($manifest.acquisition.responses.Count -eq 2) 'per-response provenance'
    foreach ($entry in $manifest.symbols) {
        $response = @($manifest.acquisition.responses | Where-Object { $_.symbol -eq $entry.symbol })[0]
        Assert-True ($response.http_status -eq 200) "HTTP status matches $($entry.symbol)"
        Assert-True ($entry.sha256 -eq $response.response_sha256) "raw response hash matches $($entry.symbol)"
        Assert-True ($entry.bars -eq $response.bar_count) "bar count matches $($entry.symbol)"
        Assert-True ($entry.first_date -eq $response.first_date -and $entry.last_date -eq $response.last_date) "actual range matches $($entry.symbol)"
        Assert-True ($response.symbol -eq $entry.symbol) "symbol matches $($entry.symbol)"
    }
    Assert-True (!(Test-Path (Join-Path $successfulDestination 'qlib-provider'))) 'no Qlib provider created'
    Assert-True (!(Test-Path $successfulStage)) 'successful fetch removes only its staging directory'
    $testsRun += 1
    $clientInfo.Client.Dispose()

    $defaultStageA = Get-ForwardRawStagingDirectory -ForwardRawRoot $forwardRoot
    $defaultStageB = Get-ForwardRawStagingDirectory -ForwardRawRoot $forwardRoot
    $expectedStageParent = [IO.Path]::GetFullPath((Join-Path $forwardRoot '.staging'))
    Assert-True ([IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($defaultStageA)) -eq $expectedStageParent) 'default staging is inside the forward-raw-only staging root'
    Assert-True ($defaultStageA -ne $defaultStageB) 'default staging paths are unique'
    $testsRun += 1

    $defaultRoot = Join-Path $root 'default-staging-root'
    $defaultOutputId = 'default-stage-' + [guid]::NewGuid().ToString('N')
    $defaultClient = New-TestClient @(
        (New-TestResponse 200 (New-BarPayload 'AAPL')),
        (New-TestResponse 200 (New-BarPayload 'MSFT'))
    )
    $script:ObservedStagingDirectory = $null
    $defaultStore = {
        param($RawDir, $OutputId, $Start, $End, $Symbols, $Root)
        $script:ObservedStagingDirectory = $RawDir
        $action = New-TestStoreAction
        & $action $RawDir $OutputId $Start $End $Symbols $Root
    }
    $null = Invoke-ForwardRawFetch -OutputId $defaultOutputId -Start '2026-09-14' -End '2026-09-14' -ForwardRawRoot $defaultRoot -Client $defaultClient.Client -Credential ([pscustomobject]@{ Key = 'TEST'; Secret = 'TEST' }) -StoreAction $defaultStore
    Assert-True ([IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($script:ObservedStagingDirectory)) -eq [IO.Path]::GetFullPath((Join-Path $defaultRoot '.staging'))) 'Invoke-ForwardRawFetch defaults to the isolated staging parent'
    Assert-True (!(Test-Path -LiteralPath $script:ObservedStagingDirectory)) 'default staging is cleaned after successful storage'
    if (Test-Path -LiteralPath (Join-Path $defaultRoot $defaultOutputId)) { Remove-Item -LiteralPath (Join-Path $defaultRoot $defaultOutputId) -Recurse -Force }
    $defaultClient.Client.Dispose(); $testsRun += 1

    foreach ($failure in @(@{ Name = '403'; Status = 403 }, @{ Name = '429'; Status = 429 })) {
        $failureRoot = Join-Path $root ('failure-' + $failure.Name)
        $badClient = New-TestClient @((New-TestResponse $failure.Status '{"bars":[]}'))
        $shouldNotStore = { throw 'STORE_MUST_NOT_RUN' }
        try {
            $failureStage = New-TestStagePath $failureRoot ('test-' + [guid]::NewGuid().ToString('N'))
            Invoke-ForwardRawFetch -OutputId ('http-' + $failure.Name) -Start '2026-09-14' -End '2026-09-14' -StagingDirectory $failureStage -ForwardRawRoot $failureRoot -Client $badClient.Client -Credential ([pscustomobject]@{ Key = 'TEST'; Secret = 'TEST' }) -StoreAction $shouldNotStore | Out-Null
            throw "EXPECTED_HTTP_FAILURE_$($failure.Status)"
        }
        catch { Assert-True ($_.Exception.Message -match "ALPACA_HTTP_$($failure.Status)") "HTTP $($failure.Status) classified" }
        Assert-True ($badClient.Handler.Requests.Count -eq 1) "HTTP $($failure.Status) counted once"
        Assert-True (!(Test-Path (Join-Path $failureRoot ('http-' + $failure.Name)))) "HTTP $($failure.Status) creates no completed manifest"
        Assert-True (!(Test-Path $failureStage)) "HTTP $($failure.Status) removes only its staging directory"
        $badClient.Client.Dispose(); $testsRun += 1
    }

    $exceptionRoot = Join-Path $root 'failure-transport'
    $exceptionClient = New-TestClient @([HttpRequestException]::new('synthetic transport failure'))
    $exceptionStage = New-TestStagePath $exceptionRoot ('test-' + [guid]::NewGuid().ToString('N'))
    try {
        Invoke-ForwardRawFetch -OutputId 'transport-error' -Start '2026-09-14' -End '2026-09-14' -StagingDirectory $exceptionStage -ForwardRawRoot $exceptionRoot -Client $exceptionClient.Client -Credential ([pscustomobject]@{ Key = 'TEST'; Secret = 'TEST' }) -StoreAction { throw 'STORE_MUST_NOT_RUN' } | Out-Null
        throw 'EXPECTED_TRANSPORT_FAILURE'
    }
    catch { Assert-True ($_.Exception.Message -match 'synthetic transport failure') 'transport failure preserved' }
    Assert-True ($exceptionClient.Handler.Requests.Count -eq 1) 'transport failure attempted once'
    Assert-True (!(Test-Path (Join-Path $exceptionRoot 'transport-error'))) 'transport failure creates no completed manifest'
    Assert-True (!(Test-Path $exceptionStage)) 'transport failure removes its staging directory'
    $exceptionClient.Client.Dispose(); $testsRun += 1

    $protectedDirectory = Join-Path $root 'must-not-delete'
    $null = New-Item -ItemType Directory -Path $protectedDirectory
    Set-Content -LiteralPath (Join-Path $protectedDirectory 'sentinel.txt') -Value 'preserve'
    $outsideRoot = Join-Path $root 'outside-root'
    $protectedClient = New-TestClient @()
    try {
        Invoke-ForwardRawFetch -OutputId 'outside-stage' -Start '2026-09-14' -End '2026-09-14' -ForwardRawRoot $outsideRoot -StagingDirectory $protectedDirectory -Client $protectedClient.Client -Credential ([pscustomobject]@{ Key = 'TEST'; Secret = 'TEST' }) -StoreAction { throw 'STORE_MUST_NOT_RUN' } | Out-Null
        throw 'EXPECTED_OUTSIDE_STAGING_REJECTION'
    }
    catch { Assert-True ($_.Exception.Message -match 'FORWARD_RAW_STAGING_OUTSIDE_ROOT') 'outside staging path rejected' }
    Assert-True (Test-Path -LiteralPath (Join-Path $protectedDirectory 'sentinel.txt')) 'unowned directory is never deleted'
    Assert-True ($protectedClient.Handler.Requests.Count -eq 0) 'invalid staging rejected before request'
    $protectedClient.Client.Dispose(); $testsRun += 1

    $duplicateRoot = Join-Path $root 'duplicate'
    $null = New-Item -ItemType Directory -Path (Join-Path $duplicateRoot 'existing-id') -Force
    $duplicateClient = New-TestClient @()
    try {
        Invoke-ForwardRawFetch -OutputId 'existing-id' -Start '2026-09-14' -End '2026-09-14' -ForwardRawRoot $duplicateRoot -Client $duplicateClient.Client -Credential ([pscustomobject]@{ Key = 'TEST'; Secret = 'TEST' }) -StoreAction { throw 'STORE_MUST_NOT_RUN' } | Out-Null
        throw 'EXPECTED_DUPLICATE_OUTPUT_REJECTION'
    }
    catch { Assert-True ($_.Exception.Message -match 'FORWARD_RAW_OUTPUT_ALREADY_EXISTS') 'duplicate output rejected' }
    Assert-True ($duplicateClient.Handler.Requests.Count -eq 0) 'duplicate rejected before any request'
    $duplicateClient.Client.Dispose(); $testsRun += 1

    $presealClient = New-TestClient @()
    try {
        Invoke-ForwardRawFetch -OutputId 'preseal' -Start '2026-09-11' -End '2026-09-14' -ForwardRawRoot (Join-Path $root 'preseal') -Client $presealClient.Client -Credential ([pscustomobject]@{ Key = 'TEST'; Secret = 'TEST' }) -StoreAction { throw 'STORE_MUST_NOT_RUN' } | Out-Null
        throw 'EXPECTED_PRESEAL_REJECTION'
    }
    catch { Assert-True ($_.Exception.Message -match 'FORWARD_RAW_DATE_RANGE_INVALID') 'pre-seal start rejected' }
    Assert-True ($presealClient.Handler.Requests.Count -eq 0) 'pre-seal rejection happens before request'
    $presealClient.Client.Dispose(); $testsRun += 1

    foreach ($researchMode in @('Fetch', 'OfflineReplay')) {
        $researchOutput = "D:\AQ_DATA\P3\alpaca-qlib-refresh-runs\forward-cutoff-test-$researchMode-$([guid]::NewGuid().ToString('N'))"
        $command = "& '$entrypoint' -Mode $researchMode -OutputRoot '$researchOutput' -EndDate '2026-09-14'"
        $researchOutputText = & pwsh.exe -NoProfile -Command $command 2>&1
        $researchExit = $LASTEXITCODE
        Assert-True ($researchExit -eq 1) "$researchMode exits denied for post-cutoff date"
        Assert-True (($researchOutputText -join "`n") -match 'DATE_RANGE_EXCEEDS_APPROVED_PRESEAL_SCOPE') "$researchMode reports unchanged research date gate"
        Assert-True (!(Test-Path -LiteralPath $researchOutput)) "$researchMode creates no output before gate"
        $testsRun += 1
    }

    Write-Output "FORWARD_RAW_FETCH_MOCK_TESTS_PASS:$testsRun"
}
finally {
    if (Test-Path -LiteralPath $successfulDestination) { Remove-Item -LiteralPath $successfulDestination -Recurse -Force }
    if (Test-Path -LiteralPath $root) { Remove-Item -LiteralPath $root -Recurse -Force }
}
