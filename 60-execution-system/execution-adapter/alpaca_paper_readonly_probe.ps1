[CmdletBinding()]
param(
    [Parameter()]
    [string]$CredentialFile = (Join-Path $env:LOCALAPPDATA 'AUTONOMOUS_QUANT\secrets\alpaca-paper-credentials-20261013.dpapi'),

    [Parameter()]
    [string]$PythonExe = 'D:\AQ_ENVS\p6-news-realtime-poc\Scripts\python.exe'
)

$ErrorActionPreference = 'Stop'

function Get-LabeledValue([string[]]$Lines, [string[]]$Labels) {
    $captured = @()
    foreach ($line in $Lines) {
        foreach ($label in $Labels) {
            if ($line -match ('^\s*' + [regex]::Escape($label) + '\s*[:=]\s*(.*?)\s*$')) {
                $captured += $Matches[1]
                break
            }
        }
    }
    if ($captured.Count -ne 1 -or [string]::IsNullOrWhiteSpace($captured[0])) {
        throw 'CREDENTIAL_SCHEMA_REJECTED'
    }
    return $captured[0]
}

if (-not (Test-Path -LiteralPath $CredentialFile -PathType Leaf)) {
    throw 'PROTECTED_CREDENTIAL_NOT_FOUND'
}
if (-not (Test-Path -LiteralPath $PythonExe -PathType Leaf)) {
    throw 'APPROVED_SDK_RUNTIME_NOT_FOUND'
}

$rawEncrypted = [System.IO.File]::ReadAllText($CredentialFile, [System.Text.Encoding]::UTF8).Trim()
$secure = ConvertTo-SecureString -String $rawEncrypted
$plain = [System.Net.NetworkCredential]::new('', $secure).Password
$lines = $plain -split "`r?`n"
$endpoint = Get-LabeledValue $lines @('Endpoint', 'API Endpoint', 'Base URL')
$apiKey = Get-LabeledValue $lines @('Key', 'API Key', 'Key ID', 'API Key ID')
$apiSecret = Get-LabeledValue $lines @('Secret', 'API Secret', 'Secret Key', 'API Secret Key')
$uri = [Uri]$endpoint
if ($uri.Scheme -ne 'https' -or $uri.Host -ne 'paper-api.alpaca.markets' -or -not $uri.IsDefaultPort -or $uri.Query -or $uri.Fragment -or $uri.AbsolutePath.TrimEnd('/') -notin @('', '/v2')) {
    throw 'PAPER_ENDPOINT_GUARD_REJECTED'
}
if ([string]::IsNullOrWhiteSpace($apiKey) -or [string]::IsNullOrWhiteSpace($apiSecret)) {
    throw 'CREDENTIAL_FIELDS_EMPTY'
}

$scriptDir = Split-Path -Parent $PSCommandPath
$probe = Join-Path $scriptDir 'alpaca_paper_readonly_probe.py'
$start = [System.Diagnostics.ProcessStartInfo]::new()
$start.FileName = $PythonExe
    $start.Arguments = '-I "' + $probe + '"'
$start.UseShellExecute = $false
$start.CreateNoWindow = $true
$start.RedirectStandardInput = $true
$start.RedirectStandardOutput = $true
$start.RedirectStandardError = $true
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$start.StandardInputEncoding = $utf8NoBom
$start.StandardOutputEncoding = $utf8NoBom
$start.StandardErrorEncoding = $utf8NoBom

$process = [System.Diagnostics.Process]::new()
$process.StartInfo = $start
try {
    if (-not $process.Start()) { throw 'SDK_CHILD_START_FAILED' }
    $payload = @{ endpoint = $endpoint; api_key = $apiKey; api_secret = $apiSecret } | ConvertTo-Json -Compress
    $process.StandardInput.WriteLine($payload)
    $process.StandardInput.Close()
    if (-not $process.WaitForExit(45000)) {
        $process.Kill($true)
        $process.WaitForExit()
        throw 'SDK_READ_ONLY_PROBE_TIMEOUT'
    }
    $stdout = $process.StandardOutput.ReadToEnd()
    if ($process.ExitCode -ne 0) { throw 'SDK_READ_ONLY_PROBE_FAILED' }
    $result = $stdout | ConvertFrom-Json
    if ($result.endpoint -ne 'https://paper-api.alpaca.markets' -or $result.paper_client -ne $true) {
        throw 'PAPER_ENDPOINT_GUARD_REJECTED'
    }
    $result | ConvertTo-Json -Compress
}
finally {
    if ($process) { $process.Dispose() }
    $apiKey = $null
    $apiSecret = $null
    $plain = $null
    $payload = $null
    $secure = $null
    $rawEncrypted = $null
}
