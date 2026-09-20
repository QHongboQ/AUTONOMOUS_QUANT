# P5 Selective Build Contraction and Native Source Asset Audit 001

Status: **PASS**

The completed 711-CIK EntityFacts census remains frozen. No new CIK scan,
broad accession acquisition, or historical build ran in this task. Its prior
selection authority remains 36,206 required accessions, 1,215,056 selected
facts, and a projected persistent footprint of 27,552,947,880 bytes.

The production surface was contracted from 2,040 to 758 physical lines. The
one-off inventory, sample, and storage-calibration paths were removed from
production ownership. Numeric admission now delegates to
`aq_fundamental_evidence`; the EdgarTools `StandardConcept` projection now has
one home in `aq_hybrid_fundamentals`; and filing capability delegates to
EdgarTools `get_obj_info(form)`, retaining only the bounded structured-6-K
policy leaf.

EdgarTools 5.58.0 `XBRLAttachments` proves a deterministic multi-asset source
boundary: instance plus the available schema and linkbases actually consumed
by its XBRL parser. AQ records only a thin manifest with each SEC-relative
asset identity, URL, role, byte count, and SHA-256, plus one deterministic
manifest hash. EntityFacts remains discovery-only and never becomes final
immutable source authority.

On the same frozen 32-accession sample:

```text
SAMPLE_FULL_SUBMISSION_BYTES = 1,006,565,281
SAMPLE_NATIVE_REQUIRED_ASSET_BYTES = 310,556,432
SOURCE_NETWORK_REDUCTION_BYTES = 696,008,849
SOURCE_NETWORK_REDUCTION_RATE = 69.1469159664%
OLD_ESTIMATED_ONE_TIME_NETWORK_BYTES = 596,021,542,220
NEW_ESTIMATED_ONE_TIME_NETWORK_BYTES = 183,891,027,280
```

Private evidence is under:

`D:\AQ_DATA\P5\edgartools-native-full-universe-historical-build-001\reports`

Key evidence hashes:

```text
native_source_asset_audit.json = 0e678fc315e2c2d53444ba6058c96a16fdff546840035aca3c3a0902d8c72eaf
production_contraction_audit.json = da5e9c38a76cc6c209ff49950f40a10519ae3f3989df7f5f5bb0a1f205dda211
```

Authority:

```text
ENTITYFACTS_FIRST_PATH = PASS
SELECTED_SOURCE_ACQUISITION = EDGARTOOLS_NATIVE_REQUIRED_ASSETS_REMOTE_FIRST
DUPLICATE_DECIMAL_IMPLEMENTATION_COUNT = 0
AQ_FORM_ROUTER_ENGINE = NO
AQ_XBRL_ENGINE = NO
AQ_GENERIC_CHECKPOINT_FRAMEWORK = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
BROAD_ACCESSION_ACQUISITION_STARTED = NO
FULL_HISTORICAL_BUILD_STARTED = NO
P2_V2_SEALED_OOS_ACCESSED = NO
CURRENT_DEVELOPMENT_NEXT = P5_EDGARTOOLS_SELECTIVE_FULL_HISTORICAL_BUILD_EXECUTION_001
```
