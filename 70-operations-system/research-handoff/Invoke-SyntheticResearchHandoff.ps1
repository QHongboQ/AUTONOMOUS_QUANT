param(
    [Parameter(Mandatory = $true)][string]$RepoRoot,
    [Parameter(Mandatory = $true)][string]$RequestPath,
    [Parameter(Mandatory = $true)][string]$PolicyPath,
    [Parameter(Mandatory = $true)][string]$StateDirectory,
    [ValidateSet('INERT_LOCAL_EXECUTABLE', 'DOCKER_RDAGENT_PROXY_MOCK_SMOKE', 'DOCKER_RDAGENT_FINQUANT_TEST_ONLY')]
    [string]$Target = 'INERT_LOCAL_EXECUTABLE',
    [string]$DockerRuntimeDirectory
)

$ErrorActionPreference = 'Stop'
$wslExe = Join-Path $env:SystemRoot 'System32\wsl.exe'
$python = '/home/zhou/AQ_ENVS/rdagent/bin/python'
$rfc8785Lib = '/mnt/d/AQ_DATA/P3/candidate-v3-materialization-001/upstream-libs'

function ConvertTo-WslPath {
    param([Parameter(Mandatory = $true)][string]$WindowsPath)
    $full = [System.IO.Path]::GetFullPath($WindowsPath)
    if ($full -notmatch '^[A-Za-z]:\\') { throw 'Only absolute drive-letter paths are supported.' }
    $drive = $full.Substring(0, 1).ToLowerInvariant()
    $tail = $full.Substring(2).Replace('\', '/')
    return "/mnt/$drive$tail"
}

$repo = ConvertTo-WslPath $RepoRoot
$request = ConvertTo-WslPath $RequestPath
$policy = ConvertTo-WslPath $PolicyPath
$state = ConvertTo-WslPath $StateDirectory
$entry = "$repo/70-operations-system/research-handoff/p12_research_handoff.py"
$arguments = @(
    $entry, 'process', '--request', $request, '--policy', $policy,
    '--state-dir', $state, '--synthetic-only', '--target', $Target
)
if ($Target -in @('DOCKER_RDAGENT_PROXY_MOCK_SMOKE', 'DOCKER_RDAGENT_FINQUANT_TEST_ONLY')) {
    if (-not $DockerRuntimeDirectory) { throw 'DockerRuntimeDirectory is required for the Docker TEST_ONLY target.' }
    $runtime = ConvertTo-WslPath $DockerRuntimeDirectory
    $arguments += @('--docker-runtime-dir', $runtime)
}

& $wslExe -d Ubuntu-24.04 -u zhou -- env "PYTHONPATH=$rfc8785Lib" $python @arguments
exit $LASTEXITCODE
