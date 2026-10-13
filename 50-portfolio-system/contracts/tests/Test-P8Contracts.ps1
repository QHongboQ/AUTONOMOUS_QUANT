$ErrorActionPreference = 'Stop'

$contractRoot = Split-Path -Parent $PSScriptRoot
$targetSchemaPath = Join-Path $contractRoot 'target_portfolio_v1.schema.json'
$riskSchemaPath = Join-Path $contractRoot 'human_risk_envelope_reference_v1.schema.json'
$readmePath = Join-Path $contractRoot 'README.md'
$sha = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
$p2Instrument = 'P2SEC' + $sha.ToUpperInvariant()

function Test-SchemaCase([string]$name, [object]$value, [string]$schemaPath, [bool]$expected) {
    $json = ConvertTo-Json -InputObject $value -Depth 30 -Compress
    try {
        $actual = [bool](Test-Json -Json $json -SchemaFile $schemaPath -ErrorAction Stop)
    }
    catch {
        $actual = $false
    }
    if ($actual -ne $expected) {
        throw "${name}: expected schema result $expected, got $actual"
    }
    Write-Output "PASS $name"
}

$target = [ordered]@{
    contract_version = 'AQ_TARGET_PORTFOLIO_V1'
    target_portfolio_id = "sha256:$sha"
    effective_time = '2030-01-02T14:30:00Z'
    provenance = @{
        producer = 'QLIB'
        producer_version = 'synthetic-fixture'
        method_id = 'synthetic-only'
        output_artifact = @{ reference = 'fixture://target'; sha256 = $sha }
    }
    input_references = @(@{
        input_kind = 'P2_CERTIFIED_CANDIDATE'
        candidate_id = "sha256:$sha"
        strategy_artifact = @{ reference = 'fixture://candidate'; sha256 = $sha }
        p2_certification = @{
            status = 'CERTIFIED'
            decision = @{ reference = 'fixture://p2-decision'; sha256 = $sha }
        }
    })
    target_weights = @{ $p2Instrument = 0.75 }
    cash_target_weight = 0.25
    risk_envelope = @{
        contract_version = 'AQ_HUMAN_RISK_ENVELOPE_REFERENCE_V1'
        status = 'UNSET'
    }
}

Test-SchemaCase 'valid P2 Qlib instrument ID' $target $targetSchemaPath $true

$tickerAlias = $target | ConvertTo-Json -Depth 30 | ConvertFrom-Json -AsHashtable
$tickerAlias.target_weights = @{ AAPL = 0.75 }
Test-SchemaCase 'reject unverified ticker alias' $tickerAlias $targetSchemaPath $false

$cashOnly = $target | ConvertTo-Json -Depth 30 | ConvertFrom-Json -AsHashtable
$cashOnly.target_weights = @{}
$cashOnly.cash_target_weight = 1.0
Test-SchemaCase 'allow cash-only target with explicit cash weight' $cashOnly $targetSchemaPath $true

$withBrokerField = $target | ConvertTo-Json -Depth 30 | ConvertFrom-Json -AsHashtable
$withBrokerField['broker'] = 'synthetic'
Test-SchemaCase 'reject broker/order boundary fields' $withBrokerField $targetSchemaPath $false

$withoutP2 = $target | ConvertTo-Json -Depth 30 | ConvertFrom-Json -AsHashtable
$withoutP2.input_references[0].Remove('p2_certification')
Test-SchemaCase 'require P2 certification reference' $withoutP2 $targetSchemaPath $false

$notCertified = $target | ConvertTo-Json -Depth 30 | ConvertFrom-Json -AsHashtable
$notCertified.input_references[0].p2_certification.status = 'RESEARCH_CANDIDATE'
Test-SchemaCase 'reject non-certified P2 input' $notCertified $targetSchemaPath $false

$championWithoutP4 = $target | ConvertTo-Json -Depth 30 | ConvertFrom-Json -AsHashtable
$championWithoutP4.input_references[0].input_kind = 'P4_CHAMPION'
Test-SchemaCase 'require P4 decision for Champion' $championWithoutP4 $targetSchemaPath $false

$championWithP4 = $target | ConvertTo-Json -Depth 30 | ConvertFrom-Json -AsHashtable
$championWithP4.input_references[0].input_kind = 'P4_CHAMPION'
$championWithP4.input_references[0].p4_champion_decision = @{
    reference = 'fixture://p4-champion-decision'
    sha256 = $sha
}
Test-SchemaCase 'accept structurally referenced Champion fixture' $championWithP4 $targetSchemaPath $true

$approvedRisk = @{
    contract_version = 'AQ_HUMAN_RISK_ENVELOPE_REFERENCE_V1'
    status = 'HUMAN_APPROVED'
    risk_envelope_id = "sha256:$sha"
    effective_from = '2030-01-01T00:00:00Z'
    effective_until = '2030-12-31T23:59:59Z'
    human_authority_record = @{ reference = 'fixture://human-authority'; sha256 = $sha }
    risk_limit_set = @{ reference = 'fixture://human-limit-set'; sha256 = $sha }
}
Test-SchemaCase 'accept fully referenced synthetic risk envelope' $approvedRisk $riskSchemaPath $true

$withoutAuthority = $approvedRisk.Clone()
$withoutAuthority.Remove('human_authority_record')
Test-SchemaCase 'require human risk authority reference' $withoutAuthority $riskSchemaPath $false

$withoutLimitSet = $approvedRisk.Clone()
$withoutLimitSet.Remove('risk_limit_set')
Test-SchemaCase 'require immutable risk limit set reference' $withoutLimitSet $riskSchemaPath $false

$policyText = Get-Content -LiteralPath $readmePath -Raw
if ($policyText -notmatch 'Schema\s+validation alone proves none of those external facts' -or
    $policyText -notmatch 'P0 examples remain synthetic' -or
    $policyText -notmatch '`UNSET`, missing, expired, or\s+unverifiable references fail closed') {
    throw 'Contract documentation must explicitly separate fixture validity from real authorization.'
}
if ($target.risk_envelope.status -ne 'UNSET' -or
    $approvedRisk.human_authority_record.reference -notlike 'fixture://*' -or
    $approvedRisk.risk_limit_set.reference -notlike 'fixture://*') {
    throw 'Synthetic fixture references must remain non-authoritative.'
}
Write-Output 'PASS unset risk and synthetic fixture do not assert real authorization'
