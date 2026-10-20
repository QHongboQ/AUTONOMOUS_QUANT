# Minimal Alpaca -> Qlib candidate updater. Invoke with PowerShell 7 (`pwsh.exe`).
# It never switches an active provider pointer or registers a scheduled task.
# Fetch mode must run as the same Windows user whose CurrentUser DPAPI credential
# is approved for Alpaca data.
# Offline acceptance example:
#   .\Update-AlpacaQlibResearchData.ps1 -Mode OfflineReplay -OutputRoot D:\AQ_DATA\P3\alpaca-qlib-refresh-runs\offline-<unique>
# ForwardRawFetch stores only bounded post-seal raw JSON plus a manifest under
# D:\AQ_DATA\FORWARD_RAW_ONLY; it never creates a Qlib provider or moves a pointer.
# A future Task Scheduler action may call Fetch mode only within an approved
# date scope; this build rejects dates after the frozen pre-seal cutoff.
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('OfflineReplay', 'Fetch', 'ForwardRawFetch')]
    [string]$Mode,

    [string]$OutputRoot,

    [string]$ForwardRawOutputId,

    [string]$SavedDataset = 'D:\AQ_DATA\P3\alpaca-research-incremental-pilot-001\version-20261020T0736Z-1a68c39f\dataset',
    [string]$ParentDataset = 'D:\AQ_DATA\P3\alpaca-research-handoff-pilot-001\run-20261020T071730Z-f2cbf2dc',
    [string]$QlibSource = '/home/zhou/AQ_UPSTREAM/qlib-rdagent-v1-pin',
    [string]$CalendarPython = '/home/zhou/AQ_ENVS/p6-macro-v1/bin/python',
    [string]$ParentStartDate = '2025-01-02',
    [string]$ParentEndDate = '2026-08-18',
    [string]$EndDate = '2026-09-11',
    [string]$StartDate = '2026-08-17'
)

$ErrorActionPreference = 'Stop'
$Image = 'aq/p3-rdagent-qlib:rdagent-1.0.0-qlib-0.9.8.dev26-v1'
$ExpectedImageId = 'sha256:f0caceba9e06a618dda72bd999de78c13e34e0773831c8796936c80793e4eea2'
$ExpectedQlibCommit = '2fb9380b342556ddb50a4b24e4fe8655d548b2b8'
$ExpectedDumpSha = 'b8f34c57ce1ef4b1772f3909735e66058f21b25bd7ab8a5f16318822401fe53f'
$MaximumResearchDate = [datetime]'2026-09-11'
$SealedOosStart = [datetime]'2026-09-14'
$MaximumForwardRawRangeDays = 31
$ExpectedSymbols = @('AAPL', 'MSFT')
if ($OutputRoot) {
    $Incremental = Join-Path $OutputRoot 'incremental'
    $Raw = Join-Path $Incremental 'raw'
    $Csv = Join-Path $Incremental 'csv'
    $Provider = Join-Path $OutputRoot 'qlib-provider'
    $Logs = Join-Path $OutputRoot 'logs'
    $CalendarDir = Join-Path $OutputRoot 'calendar'
    $ManifestOut = Join-Path $OutputRoot 'dataset_manifest.json'
}
$ForwardRawRoot = 'D:\AQ_DATA\FORWARD_RAW_ONLY'
$ScriptDir = if ($PSCommandPath) { Split-Path -Parent $PSCommandPath } elseif ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
$Validator = Join-Path $ScriptDir 'verify_alpaca_qlib_refresh.py'

function Assert-ExternalOutput {
    $out = [IO.Path]::GetFullPath($OutputRoot).TrimEnd('\')
    $allowedRoot = [IO.Path]::GetFullPath('D:\AQ_DATA\P3\alpaca-qlib-refresh-runs').TrimEnd('\')
    if (!$out.StartsWith($allowedRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'OUTPUT_OUTSIDE_APPROVED_RESEARCH_ROOT' }
    $protected = @([IO.Path]::GetFullPath($SavedDataset).TrimEnd('\'), [IO.Path]::GetFullPath($ParentDataset).TrimEnd('\'))
    foreach ($path in $protected) {
        if ($out.Equals($path, [StringComparison]::OrdinalIgnoreCase) -or $out.StartsWith($path + '\', [StringComparison]::OrdinalIgnoreCase)) {
            throw 'OUTPUT_MUST_BE_OUTSIDE_PROTECTED_DATASETS'
        }
    }
    if (Test-Path -LiteralPath $out) { throw 'OUTPUT_ROOT_MUST_NOT_EXIST' }
    $script:OutputRoot = $out
}

function Convert-WindowsPathToWsl([string]$Path) {
    $full = [IO.Path]::GetFullPath($Path)
    if ($full -notmatch '^([A-Za-z]):\\(.*)$') { throw 'PATH_MUST_BE_ON_A_WINDOWS_DRIVE' }
    return '/mnt/' + $Matches[1].ToLowerInvariant() + '/' + ($Matches[2] -replace '\\','/')
}

function Invoke-Wsl([string[]]$Arguments) {
    & wsl.exe @Arguments
    if ($LASTEXITCODE -ne 0) { throw "WSL_COMMAND_FAILED_EXIT_$LASTEXITCODE" }
}

function Read-ExistingCredential([string]$Path) {
    if (!(Test-Path -LiteralPath $Path -PathType Leaf)) { throw 'CREDENTIAL_MISSING' }
    $secure = ConvertTo-SecureString -String ([IO.File]::ReadAllText($Path, [Text.Encoding]::UTF8).Trim())
    $plain = [Net.NetworkCredential]::new('', $secure).Password
    try {
        $lines = $plain -split "`r?`n"
        $map = @{}
        foreach ($line in $lines) {
            if ($line -match '^\s*([^:]+?)\s*:\s*(.*?)\s*$') { $map[$Matches[1].Trim()] = $Matches[2].Trim() }
        }
        $endpoint = $map['Endpoint']; if (!$endpoint) { $endpoint = $map['API Endpoint'] }; if (!$endpoint) { $endpoint = $map['Base URL'] }
        $uri = [Uri]$endpoint
        if ($uri.Scheme -ne 'https' -or $uri.Host -ne 'paper-api.alpaca.markets' -or $uri.Query -or $uri.Fragment) { throw 'CREDENTIAL_ENDPOINT_REJECTED' }
        $key = $map['Key']; if (!$key) { $key = $map['API Key'] }; if (!$key) { $key = $map['Key ID'] }; if (!$key) { $key = $map['API Key ID'] }
        $secret = $map['Secret']; if (!$secret) { $secret = $map['API Secret'] }; if (!$secret) { $secret = $map['Secret Key'] }; if (!$secret) { $secret = $map['API Secret Key'] }
        if (!$key -or !$secret) { throw 'CREDENTIAL_FIELDS_EMPTY' }
        return [pscustomobject]@{ Key = $key; Secret = $secret }
    }
    finally { $plain = $null; $secure = $null }
}

function Assert-ManifestFiles([string]$Root, $Manifest) {
    $entries = $Manifest.data_version.file_sha256
    if (!$entries) { throw "MANIFEST_FILE_HASHES_MISSING: $Root" }
    foreach ($property in $entries.PSObject.Properties) {
        $path = Join-Path $Root ($property.Name.Replace('/', '\'))
        if (!(Test-Path -LiteralPath $path -PathType Leaf)) { throw "MANIFEST_FILE_MISSING: $($property.Name)" }
        $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actual -ne [string]$property.Value) { throw "MANIFEST_FILE_HASH_MISMATCH: $($property.Name)" }
    }
}

function Get-ManifestHash($Manifest, [string]$RelativePath) {
    $property = $Manifest.data_version.file_sha256.PSObject.Properties | Where-Object { $_.Name -eq $RelativePath } | Select-Object -First 1
    if (!$property) { throw "MANIFEST_HASH_MISSING: $RelativePath" }
    return [string]$property.Value
}

function Fetch-IncrementalBars {
    if ([datetime]$EndDate -gt $MaximumResearchDate) { throw 'DATE_RANGE_EXCEEDS_APPROVED_PRESEAL_SCOPE' }
    if ([datetime]$StartDate -gt [datetime]$EndDate) { throw 'INVALID_DATE_RANGE' }
    $credPath = Join-Path $env:LOCALAPPDATA 'AUTONOMOUS_QUANT\secrets\alpaca-paper-credentials-20261013.dpapi'
    $credential = Read-ExistingCredential $credPath
    $rawDirectory = $Raw
    $client = New-AlpacaHttpClient
    try {
        $result = Invoke-AlpacaBarsRequests -Client $client -Credential $credential -Symbols $ExpectedSymbols -Start $StartDate -End $EndDate -RawDirectory $rawDirectory -MaximumTotalBytes 2MB
        return [pscustomobject]@{
            RequestCount = $result.RequestCount
            ResponseBytes = $result.ResponseBytes
            Symbols = @($result.Symbols | ForEach-Object { [pscustomobject]@{ Symbol = $_.symbol; Status = $_.http_status; Bars = $_.bar_count; Sha256 = $_.response_sha256 } })
        }
    }
    finally { $client.Dispose(); $credential = $null }
}

function New-AlpacaHttpClient {
    $handler = [Net.Http.HttpClientHandler]::new()
    $handler.AllowAutoRedirect = $false
    $client = [Net.Http.HttpClient]::new($handler)
    $client.Timeout = [TimeSpan]::FromSeconds(45)
    return $client
}

function Invoke-AlpacaBarsRequests {
    param(
        [Parameter(Mandatory)][Net.Http.HttpClient]$Client,
        [Parameter(Mandatory)]$Credential,
        [Parameter(Mandatory)][string[]]$Symbols,
        [Parameter(Mandatory)][string]$Start,
        [Parameter(Mandatory)][string]$End,
        [Parameter(Mandatory)][string]$RawDirectory,
        [Parameter(Mandatory)][long]$MaximumTotalBytes
    )
    $results = @(); $totalBytes = 0L; $requestCount = 0
    foreach ($symbol in $Symbols) {
        $query = 'timeframe=1Day&start={0}T00%3A00%3A00Z&end={1}T23%3A59%3A59Z&feed=sip&adjustment=raw&asof=-&limit=10000' -f $Start, $End
        $uri = [Uri]('https://data.alpaca.markets/v2/stocks/{0}/bars?{1}' -f $symbol, $query)
        $request = [Net.Http.HttpRequestMessage]::new([Net.Http.HttpMethod]::Get, $uri)
        [void]$request.Headers.TryAddWithoutValidation('APCA-API-KEY-ID', $Credential.Key)
        [void]$request.Headers.TryAddWithoutValidation('APCA-API-SECRET-KEY', $Credential.Secret)
        [void]$request.Headers.TryAddWithoutValidation('Accept', 'application/json')
        $response = $null
        try {
            $requestCount++
            $fetchedAt = [datetime]::UtcNow.ToString('o', [Globalization.CultureInfo]::InvariantCulture)
            $response = $Client.SendAsync($request, [Net.Http.HttpCompletionOption]::ResponseHeadersRead).GetAwaiter().GetResult()
            $status = [int]$response.StatusCode
            if ($status -ne 200) { throw "ALPACA_HTTP_$status" }
            if ($null -ne $response.Content.Headers.ContentLength -and $response.Content.Headers.ContentLength -gt 1MB) { throw 'RESPONSE_LIMIT_EXCEEDED' }
            $stream = $response.Content.ReadAsStreamAsync().GetAwaiter().GetResult()
            $memory = [IO.MemoryStream]::new(); $buffer = [byte[]]::new(8192)
            try {
                while (($read = $stream.Read($buffer, 0, $buffer.Length)) -gt 0) {
                    if (($memory.Length + $read) -gt 1MB) { throw 'RESPONSE_LIMIT_EXCEEDED' }
                    $memory.Write($buffer, 0, $read)
                }
            }
            finally { $stream.Dispose() }
            $data = $memory.ToArray(); $memory.Dispose(); $totalBytes += $data.Length
            if ($totalBytes -gt $MaximumTotalBytes) { [Array]::Clear($data, 0, $data.Length); throw 'TOTAL_RESPONSE_LIMIT_EXCEEDED' }
            $json = [Text.Encoding]::UTF8.GetString($data) | ConvertFrom-Json -AsHashtable -ErrorAction Stop
            if ($json.next_page_token) { [Array]::Clear($data, 0, $data.Length); throw 'PAGINATION_INCOMPLETE' }
            if ($null -eq $json.bars -or $json.bars -isnot [System.Collections.IList]) { [Array]::Clear($data, 0, $data.Length); throw 'BARS_ARRAY_INVALID' }
            [IO.File]::WriteAllBytes((Join-Path $RawDirectory ($symbol + '.json')), $data)
            $hash = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($data)).ToLowerInvariant()
            $results += [pscustomobject]@{
                symbol = $symbol; http_status = $status; bar_count = $json.bars.Count
                first_date = if ($json.bars.Count) { ([datetime]::Parse($json.bars[0].t).ToUniversalTime()).ToString('yyyy-MM-dd') } else { $null }
                last_date = if ($json.bars.Count) { ([datetime]::Parse($json.bars[-1].t).ToUniversalTime()).ToString('yyyy-MM-dd') } else { $null }
                response_bytes = $data.Length; response_sha256 = $hash; fetched_at_utc = $fetchedAt
            }
            [Array]::Clear($data, 0, $data.Length)
        }
        finally { if ($response) { $response.Dispose() }; $request.Dispose() }
    }
    return [pscustomobject]@{ RequestCount = $requestCount; ResponseBytes = $totalBytes; Symbols = $results }
}

function Fetch-ForwardRawResponses {
    param(
        [Parameter(Mandatory)][string]$Start,
        [Parameter(Mandatory)][string]$End,
        [Parameter(Mandatory)][string]$RawDirectory,
        [Net.Http.HttpClient]$Client,
        $Credential
    )
    $startValue = [datetime]::ParseExact($Start, 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture)
    $endValue = [datetime]::ParseExact($End, 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture)
    if ($startValue -lt $SealedOosStart -or $endValue -lt $startValue) { throw 'FORWARD_RAW_DATE_RANGE_INVALID' }
    if (($endValue - $startValue).TotalDays -ge $MaximumForwardRawRangeDays) { throw 'FORWARD_RAW_DATE_RANGE_EXCEEDS_31_DAYS' }
    $ownsClient = $false
    if (!$Client) {
        if (!$Credential) {
            $credPath = Join-Path $env:LOCALAPPDATA 'AUTONOMOUS_QUANT\secrets\alpaca-paper-credentials-20261013.dpapi'
            $Credential = Read-ExistingCredential $credPath
        }
        $Client = New-AlpacaHttpClient
        $ownsClient = $true
    }
    try {
        return Invoke-AlpacaBarsRequests -Client $Client -Credential $Credential -Symbols $ExpectedSymbols -Start $Start -End $End -RawDirectory $RawDirectory -MaximumTotalBytes 2MB
    }
    finally {
        if ($ownsClient) { $Client.Dispose() }
        $Credential = $null
    }
}

function Invoke-ForwardRawFetch {
    param(
        [Parameter(Mandatory)][string]$OutputId,
        [Parameter(Mandatory)][string]$Start,
        [Parameter(Mandatory)][string]$End,
        [string]$RawDirectory = (Join-Path $env:TEMP ('aq-forward-raw-' + [guid]::NewGuid().ToString('N'))),
        [string]$ForwardRawRoot = 'D:\AQ_DATA\FORWARD_RAW_ONLY',
        [Net.Http.HttpClient]$Client,
        $Credential,
        [scriptblock]$StoreAction
    )
    if ($OutputId -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$' -or $OutputId -in @('.', '..')) { throw 'FORWARD_RAW_OUTPUT_ID_INVALID' }
    $destination = Join-Path $ForwardRawRoot $OutputId
    if (Test-Path -LiteralPath $destination) { throw 'FORWARD_RAW_OUTPUT_ALREADY_EXISTS' }
    $null = New-Item -ItemType Directory -Path $RawDirectory
    try {
        $fetch = Fetch-ForwardRawResponses -Start $Start -End $End -RawDirectory $RawDirectory -Client $Client -Credential $Credential
        if ($StoreAction) {
            $storeResult = & $StoreAction $RawDirectory $OutputId $Start $End $ExpectedSymbols $ForwardRawRoot
        }
        else {
            $scriptLinux = Convert-WindowsPathToWsl $ScriptDir
            $rawLinux = Convert-WindowsPathToWsl $RawDirectory
            $args = @('-e', $CalendarPython, ($scriptLinux + '/verify_alpaca_qlib_refresh.py'), 'forward-raw-only', '--raw', $rawLinux, '--output-id', $OutputId, '--start', $Start, '--end', $End, '--symbols') + $ExpectedSymbols
            $storeOutput = & wsl.exe @args 2>&1
            if ($LASTEXITCODE -ne 0) { throw "FORWARD_RAW_VALIDATION_FAILED_EXIT_$LASTEXITCODE" }
            $jsonLine = $storeOutput | Where-Object { [string]$_ -match '^\s*\{' } | Select-Object -Last 1
            if (!$jsonLine) { throw 'FORWARD_RAW_VALIDATION_RESULT_MISSING' }
            $storeResult = [string]$jsonLine | ConvertFrom-Json -ErrorAction Stop
        }
        if (!$storeResult -or $storeResult.status -ne 'FORWARD_RAW_ONLY_COMPLETE') { throw 'FORWARD_RAW_STORAGE_NOT_COMPLETE' }
        $manifestPath = Join-Path $destination 'manifest.json'
        $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
        if ($manifest.start -ne $Start -or $manifest.end -ne $End -or $manifest.symbols.Count -ne $ExpectedSymbols.Count) { throw 'FORWARD_RAW_MANIFEST_SCOPE_MISMATCH' }
        foreach ($responseRecord in $fetch.Symbols) {
            $storedRecord = @($manifest.symbols | Where-Object { $_.symbol -eq $responseRecord.symbol })
            if ($storedRecord.Count -ne 1 -or $storedRecord[0].bars -ne $responseRecord.bar_count -or $storedRecord[0].sha256 -ne $responseRecord.response_sha256 -or $storedRecord[0].first_date -ne $responseRecord.first_date -or $storedRecord[0].last_date -ne $responseRecord.last_date) {
                throw "FORWARD_RAW_MANIFEST_RESPONSE_MISMATCH:$($responseRecord.symbol)"
            }
        }
        $manifest.status = 'FORWARD_RAW_FETCH_COMPLETE'
        $manifest.source_attestation = 'CONTROLLED_ALPACA_FETCH_BY_EXISTING_ENTRYPOINT'
        $acquisition = [ordered]@{
            provider = 'Alpaca Market Data API'
            endpoint_template = 'https://data.alpaca.markets/v2/stocks/{symbol}/bars'
            parameters = [ordered]@{ timeframe = '1Day'; start = "$Start`T00:00:00Z"; end = "$End`T23:59:59Z"; feed = 'sip'; adjustment = 'raw'; asof = '-'; limit = 10000 }
            fetched_at_utc = [datetime]::UtcNow.ToString('o', [Globalization.CultureInfo]::InvariantCulture)
            request_count = $fetch.RequestCount
            total_response_bytes = $fetch.ResponseBytes
            responses = $fetch.Symbols
        }
        $manifest | Add-Member -NotePropertyName acquisition -NotePropertyValue $acquisition -Force
        $tempManifest = $manifestPath + '.tmp'
        $manifest | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $tempManifest -Encoding utf8
        [IO.File]::Move($tempManifest, $manifestPath, $true)
        return [pscustomobject]@{ Status = 'FORWARD_RAW_FETCH_COMPLETE'; OutputPath = $destination; Acquisition = $manifest.acquisition }
    }
    finally {
        if (Test-Path -LiteralPath $RawDirectory) { Remove-Item -LiteralPath $RawDirectory -Recurse -Force }
    }
}

if ($MyInvocation.InvocationName -eq '.') { return }

try {
    if ($PSVersionTable.PSVersion.Major -lt 7) { throw 'POWERSHELL_7_REQUIRED' }
    if ($Mode -eq 'ForwardRawFetch') {
        if ($OutputRoot) { throw 'OUTPUT_ROOT_NOT_USED_FOR_FORWARD_RAW' }
        if (!$ForwardRawOutputId) { throw 'FORWARD_RAW_OUTPUT_ID_REQUIRED' }
        $forwardStart = [datetime]::ParseExact($StartDate, 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture)
        $forwardEnd = [datetime]::ParseExact($EndDate, 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture)
        if ($forwardStart -lt $SealedOosStart -or $forwardEnd -lt $forwardStart) { throw 'FORWARD_RAW_DATE_RANGE_INVALID' }
        if (($forwardEnd - $forwardStart).TotalDays -ge $MaximumForwardRawRangeDays) { throw 'FORWARD_RAW_DATE_RANGE_EXCEEDS_31_DAYS' }
        $forwardResult = Invoke-ForwardRawFetch -OutputId $ForwardRawOutputId -Start $StartDate -End $EndDate
        $forwardResult | ConvertTo-Json -Depth 8
        exit 0
    }
    if (!$OutputRoot) { throw 'OUTPUT_ROOT_REQUIRED_FOR_RESEARCH_MODES' }
    Assert-ExternalOutput
    $Incremental = Join-Path $OutputRoot 'incremental'
    $Raw = Join-Path $Incremental 'raw'
    $Csv = Join-Path $Incremental 'csv'
    $Provider = Join-Path $OutputRoot 'qlib-provider'
    $Logs = Join-Path $OutputRoot 'logs'
    $CalendarDir = Join-Path $OutputRoot 'calendar'
    $ManifestOut = Join-Path $OutputRoot 'dataset_manifest.json'
    foreach ($dateValue in @($StartDate, $EndDate, $ParentStartDate, $ParentEndDate)) {
        if ($dateValue -notmatch '^\d{4}-\d{2}-\d{2}$') { throw 'DATE_FORMAT_MUST_BE_YYYY_MM_DD' }
        [void][datetime]::ParseExact($dateValue, 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture)
    }
    $parentEndValue = [datetime]::ParseExact($ParentEndDate, 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture)
    $startValue = [datetime]::ParseExact($StartDate, 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture)
    $endValue = [datetime]::ParseExact($EndDate, 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture)
    if ($startValue -lt $parentEndValue.AddDays(-7) -or $startValue -gt $parentEndValue) { throw 'INCREMENTAL_START_MUST_OVERLAP_PARENT_WITHIN_SEVEN_DAYS' }
    if ($endValue -le $parentEndValue) { throw 'INCREMENTAL_END_MUST_EXTEND_PARENT' }
    if ([datetime]$EndDate -gt $MaximumResearchDate) { throw 'DATE_RANGE_EXCEEDS_APPROVED_PRESEAL_SCOPE' }
    foreach ($path in @($ParentDataset, $Validator)) { if (!(Test-Path -LiteralPath $path)) { throw "REQUIRED_INPUT_MISSING: $path" } }
    if ($Mode -eq 'OfflineReplay' -and !(Test-Path -LiteralPath $SavedDataset)) { throw "REQUIRED_INPUT_MISSING: $SavedDataset" }
    $parentManifest = Get-Content -Raw (Join-Path $ParentDataset 'dataset_manifest.json') | ConvertFrom-Json
    Assert-ManifestFiles $ParentDataset $parentManifest
    if ($parentManifest.status -notin @('QLIB_RESEARCH_HANDOFF_PASS','RESEARCH_INCREMENTAL_PILOT_PASS','RESEARCH_RAW_DATA_READY') -or $parentManifest.qlib.converter_sha256 -ne $ExpectedDumpSha -or $parentManifest.qlib.source_commit -ne $ExpectedQlibCommit -or $parentManifest.qlib.version -ne '0.9.8.dev26') { throw 'PARENT_QLIB_PROVENANCE_MISMATCH' }
    $savedManifest = $null
    if ($Mode -eq 'OfflineReplay') {
        $savedManifest = Get-Content -Raw (Join-Path $SavedDataset 'dataset_manifest.json') | ConvertFrom-Json
        Assert-ManifestFiles $SavedDataset $savedManifest
        if ($savedManifest.status -ne 'RESEARCH_INCREMENTAL_PILOT_PASS' -or $savedManifest.qlib.converter_sha256 -ne $ExpectedDumpSha -or $savedManifest.qlib.version -ne '0.9.8.dev26') { throw 'SAVED_DATASET_PROVENANCE_MISMATCH' }
        if ($savedManifest.parent.dataset_id -ne $parentManifest.data_version.dataset_id) { throw 'PARENT_DATASET_IDENTITY_MISMATCH' }
    }
    if ($Mode -eq 'OfflineReplay' -and ($StartDate -ne '2026-08-17' -or $EndDate -ne '2026-09-11')) { throw 'OFFLINE_REPLAY_SCOPE_MISMATCH' }
    $imageId = (& wsl.exe -e docker image inspect $Image --format '{{.Id}}' | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $imageId -ne $ExpectedImageId) { throw 'QLIB_IMAGE_ID_MISMATCH' }
    $dumpLinux = $QlibSource.TrimEnd('/') + '/scripts/dump_bin.py'
    $dumpCheck = (& wsl.exe -e sha256sum $dumpLinux | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $dumpCheck -notmatch $ExpectedDumpSha) { throw 'QLIB_DUMP_TOOL_HASH_MISMATCH' }
    $sourceCommit = (& wsl.exe -e git -C $QlibSource rev-parse HEAD | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $sourceCommit -ne $ExpectedQlibCommit) { throw 'QLIB_SOURCE_COMMIT_MISMATCH' }

    New-Item -ItemType Directory -Path $OutputRoot | Out-Null
    New-Item -ItemType Directory -Path $Raw -Force | Out-Null
    New-Item -ItemType Directory -Path $Csv -Force | Out-Null
    New-Item -ItemType Directory -Path $Logs -Force | Out-Null
    New-Item -ItemType Directory -Path $CalendarDir -Force | Out-Null
    $fetch = $null
    if ($Mode -eq 'OfflineReplay') {
        foreach ($symbol in $ExpectedSymbols) {
            $source = Join-Path $SavedDataset "incremental\raw\$symbol.json"
            $expected = Get-ManifestHash $savedManifest "incremental/raw/$symbol.json"
            if (!(Test-Path -LiteralPath $source) -or (Get-FileHash $source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) { throw "SAVED_RAW_HASH_MISMATCH: $symbol" }
            Copy-Item -LiteralPath $source -Destination (Join-Path $Raw "$symbol.json")
        }
    }
    else { $fetch = Fetch-IncrementalBars }

    $parentProviderWin = Join-Path $ParentDataset 'qlib-provider'
    $parentProviderLinux = Convert-WindowsPathToWsl $parentProviderWin
    $candidateProviderLinux = Convert-WindowsPathToWsl $Provider
    Invoke-Wsl -Arguments @('-e','cp','-a',$parentProviderLinux,$candidateProviderLinux)

    $rawLinux = Convert-WindowsPathToWsl $Raw
    $csvLinux = Convert-WindowsPathToWsl $Csv
    $dateStart = if ($Mode -eq 'OfflineReplay') { '2026-08-17' } else { $StartDate }
    $dateEnd = $EndDate
    $scriptLinux = Convert-WindowsPathToWsl $ScriptDir
    $calendarLinux = Convert-WindowsPathToWsl $CalendarDir
    $dumpLinux = $QlibSource.TrimEnd('/') + '/scripts/dump_bin.py'
    $calendarScript = $scriptLinux + '/verify_alpaca_qlib_refresh.py'
    $calendarPythonArgs = @('-e',$CalendarPython,$calendarScript,'calendar')
    foreach ($range in @(@{Name='incremental';Start=$dateStart;End=$dateEnd},@{Name='full';Start=$ParentStartDate;End=$dateEnd})) {
        $calendarResult = & wsl.exe @($calendarPythonArgs + @('--start',$range.Start,'--end',$range.End)) 2>&1
        if ($LASTEXITCODE -ne 0) { throw "XNYS_CALENDAR_GENERATION_FAILED_$($range.Name)" }
        $calendarJson = ($calendarResult -join "`n") | ConvertFrom-Json -ErrorAction Stop
        if ($calendarJson.version -ne '4.13.2') { throw 'XNYS_CALENDAR_VERSION_MISMATCH' }
        [IO.File]::WriteAllText((Join-Path $CalendarDir ($range.Name + '.json')), ($calendarResult -join "`n"), [Text.UTF8Encoding]::new($false))
    }
    $sharedArgs = @('run','--rm','--network','none','--read-only','--user','10001:10001','--tmpfs','/tmp:rw,noexec,nosuid,size=64m','--mount',"type=bind,src=$scriptLinux,dst=/opt/aq,readonly",'--mount',"type=bind,src=$rawLinux,dst=/raw,readonly",'--mount',"type=bind,src=$csvLinux,dst=/csv",'--mount',"type=bind,src=$parentProviderLinux,dst=/parent,readonly",'--mount',"type=bind,src=$candidateProviderLinux,dst=/provider",'--mount',"type=bind,src=$dumpLinux,dst=/opt/qlib/dump_bin.py,readonly",'--mount',"type=bind,src=$calendarLinux,dst=/calendar,readonly",'--entrypoint','/bin/bash',$Image)
    Invoke-Wsl -Arguments (@('-e','docker') + $sharedArgs + @('-lc', "conda run -n rdagent4qlib python /opt/aq/verify_alpaca_qlib_refresh.py prepare --raw /raw --csv /csv --calendar /calendar/incremental.json --start $dateStart --end $dateEnd"))

    $dumpLog = Join-Path $Logs 'dump-update.log'
    $dumpCommand = "conda run -n rdagent4qlib python /opt/qlib/dump_bin.py dump_update --data_path=/csv --qlib_dir=/provider --max_workers=1 --date_field_name=date --symbol_field_name=symbol --file_suffix=.csv --include_fields=open,high,low,close,volume"
    $dumpOutput = & wsl.exe -e docker @($sharedArgs + @('-lc', $dumpCommand)) 2>&1
    $dumpExit = $LASTEXITCODE
    $dumpOutput | Set-Content -LiteralPath $dumpLog -Encoding utf8
    if ($dumpExit -ne 0) { throw "QLIB_DUMP_UPDATE_EXIT_$dumpExit" }
    if (($dumpOutput -join "`n") -notmatch 'dump bin errors:\s*\{\}') { throw 'QLIB_FILE_LEVEL_ERROR_OR_MISSING_SUMMARY' }

    $verifyLog = Join-Path $Logs 'validation.json'
    $verifyCommand = "conda run -n rdagent4qlib python /opt/aq/verify_alpaca_qlib_refresh.py verify --parent /parent --provider /provider --raw /raw --calendar /calendar/full.json --start $ParentStartDate --parent-end $ParentEndDate --end $dateEnd"
    $verifyOutput = & wsl.exe -e docker @($sharedArgs + @('-lc', $verifyCommand)) 2>&1
    $verifyExit = $LASTEXITCODE
    $verifyOutput | Set-Content -LiteralPath $verifyLog -Encoding utf8
    if ($verifyExit -ne 0) { throw "QLIB_VALIDATION_EXIT_$verifyExit" }
    $jsonLine = $verifyOutput | Where-Object { [string]$_ -match '^\s*\{' } | Select-Object -Last 1
    if (!$jsonLine) { throw 'QLIB_VALIDATION_JSON_MISSING' }
    $validation = [string]$jsonLine | ConvertFrom-Json -ErrorAction Stop
    $fileHashes = @{}
    Get-ChildItem -LiteralPath $OutputRoot -File -Recurse | Where-Object { $_.Name -ne 'dataset_manifest.json' } | ForEach-Object {
        $relative = $_.FullName.Substring($OutputRoot.TrimEnd('\').Length + 1).Replace('\','/')
        $fileHashes[$relative] = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    $manifest = [ordered]@{
        schema = 'aq-alpaca-qlib-research-incremental-v1'
        status = 'RESEARCH_RAW_DATA_READY'
        parent_dataset_id = $parentManifest.data_version.dataset_id
        symbol_scope = $ExpectedSymbols
        date_start = $dateStart
        date_end = $dateEnd
        price_semantics = 'adjustment=raw; no split/dividend adjustment'
        provider = 'Alpaca Market Data API'
        qlib = [ordered]@{ version = '0.9.8.dev26'; source_commit = $ExpectedQlibCommit; converter_sha256 = $ExpectedDumpSha; image_id = $ExpectedImageId; update = 'official dump_bin.py dump_update'; fields = @('open','high','low','close','volume') }
        data_version = [ordered]@{ dataset_id = "alpaca-sip-aapl-msft-$($ParentStartDate)_$($dateEnd)-v1"; version = 1; file_sha256 = $fileHashes }
        parent = [ordered]@{ dataset_id = $parentManifest.data_version.dataset_id; dataset_path = $ParentDataset; last_session = $ParentEndDate }
        validation = $validation
        fetch = $fetch
        artifact_sha256 = $fileHashes
        published = $false
        p2_certified = $false
        pit_training_ready = $false
    }
    $manifest | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $ManifestOut -Encoding utf8
    [pscustomobject]@{Status='RESEARCH_RAW_DATA_READY';Mode=$Mode;OutputRoot=$OutputRoot;Provider=$Provider;Validation=$validation;Published=$false;ApiRequestCount=if($fetch){$fetch.RequestCount}else{0}} | ConvertTo-Json -Depth 8
    exit 0
}
catch {
    [Console]::Error.WriteLine("ALPACA_QLIB_REFRESH_FAILED: $($_.Exception.Message)")
    exit 1
}
