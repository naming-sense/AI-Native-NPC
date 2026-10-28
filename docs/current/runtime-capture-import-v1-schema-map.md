# Runtime import provenance artifact grammar and structural checks

This stage defines the closed artifact grammar and a read-only structure validator for the approved [Runtime import contract](runtime-capture-import-v1-contract.md). Every sidecar remains an untrusted declaration. A successful validation report has `authorization_status=structure_only`, `origin_authorized=false`, `label_authorized=false`, `training_eligible=false`, and `production_eligible=false`.

## Scope and execution boundary

The validator reads one submitted JSON byte image. It checks the local Schema, exact numeric types, canonical encoding, lexical paths, and declared cross-field consistency. Descriptor targets are never opened. No owner storage, provider, Editor, build tool, Capture decoder, Snapshot reader, Dataset mapper, or authorization factory is invoked. Filesystem containment, symlink/ancestor/ABA defenses and same-byte target readback belong to the later immutable-artifact resolver. Shape-valid fabricated evidence is possible and grants no authority.

The base collection index remains `format, version, session_id, entries`; it has no session/episode descriptors. Dataset v2 record and manifest fields remain unchanged. Status fields live in sidecars and validation reports. No new trainer, DAgger authority, direct Capture→Human route, or remote attestation service is introduced.

## Field-to-contract map

Mechanical names below resolve spellings left open by the approved contract; they add no issuance or product permissions.

| Definition / fields | Contract section | Structural meaning / later responsibility |
|---|---|---|
| `descriptor`: `path,size_bytes,sha256` | §2.1, §3.1 | Exact-byte declaration; target readback is deferred. Collection descriptors reuse existing collection artifact bounds. General evidence descriptors allow an empty file (e.g. failed-provider stdout). |
| `completion_item`: `authority_namespace,completion_item_id` | §2.1, §5 | Independent completion-item **identity reference**, never a serialized pin or capability. Owner acquisition remains external. |
| `completion_closure`: final index/session, all ordered episode references, replay predecessors, catalog raw descriptor plus canonical digest, execution profile/build descriptor plus digests, start evidence | §2.1 | Mandatory closure inventory. Episode wrappers carry collection identity, final state, exact descriptor and nullable replay reference. Include failed/cancelled/no-Capture episodes. Array order is execution order; it is never sorted. External replay entries carry their own completion-item identity and session/episode descriptors. External graph/custody checks require later contexts. |
| `collection_execution_profile` | §3.1 | Exact declared fields; source/mode/controller/limits reuse collection constraints. Offline/fixture profiles remain representable without acquiring real Runtime authority. |
| `utility_profile_source` | §3.1 | Exact generated Utility profile ID and four project-root source descriptors. |
| `runtime_build_evidence` | §3.2 | Closed before/after inventories, argv, project target/platform/configuration, clean/forced mode, exit/log/receipt/modules, installed engine/toolchain descriptors and source digests. Actual compile/link/dependency completeness remains a producer responsibility. |
| `session_start_evidence` | §3.3 | PID plus OS start identity, argv/executable, loaded modules/source inventory/log, disabled Live Coding/hot-reload states. Actual cold launch, installed/loaded byte equality and lifetime monitoring remain Runtime responsibilities. |
| `tool_identity`: `version,source` | §2.1, §8 | Source descriptor and version for parser/importer/transformation code. Operator tool allowlisting is deferred. |
| `import_index`: collection identity/closure, parser/importer, Snapshot descriptors, entries | §4, §8 | Candidate, Utility-unreviewed, weight-zero Snapshot declarations; raw Dagger=2 never grants label authority. |
| `entries[].raw_capture` | §4.1–4.4 | Exact raw identities, optional hash **strings**, eight ordered groups, generator/prompt text, labels, handles, switch facts, tensors, and standard-base64 CBOR/Candidate blocks. Empty raw hashes remain empty strings; normalized mapping uses null. |
| `entries[].snapshot_row` | §4 | Zero-based row ordinal and identity, fixed tensor/group/contract order, closure template/profile, importer policy, semantic binding versions and independent normalized policy lineage. This is a mapping declaration, not a new Snapshot format. |
| `teacher_completion_evidence` | §5.1 | Exact profile/prompt/request/response-schema descriptors, existing provider identity/decoding, source/import references, per-row exact request and all five ordered attempt stdout descriptors/outcomes/errors, annotation and review queue. Actual provider issuance and consensus/routing replay are deferred. |
| `human_completion_evidence` | §5.2 | Teacher-run reference, decision/source exact descriptors and digests, collection/import identities, exact reviewer-list and owner workflow authorization bindings. Reviewer text grants no identity authority. |
| `derived_index`: original import/Snapshot, Teacher/Human references, Dataset/manifest, transformation code, rows | §4.1, §4.5, §6, §8 | Original and label-derived sample identities remain separate. Silver/0.25 or Gold/1.0 declarations only; original Runtime build and transformation code identity are distinct fields. Derived index contains no self-hash and must later be published last. |

## Byte grammar

New artifact bytes are UTF-8 `json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)` plus exactly one LF. JSON duplicate keys, nonfinite values, Python-only values, unknown fields, malformed digests and coercion are rejected. JSON-Schema integer semantics alone are insufficient: the executable validator requires exact Python/JSON integers, excluding `1.0` and bool. Raw float fields preserve decoded float values without rounding repairs.

Catalog identity keeps the existing separate `catalog_digest` rule: strict catalog validation followed by sorted compact object bytes **without LF**. A catalog's raw-file descriptor digest may differ. YAML Teacher Profile identity hashes its original bytes.

Collection paths reuse the collection lexical grammar. Build inventory/evidence relative paths permit UTF-8 names and spaces but reject empty/dot/parent segments, absolute/drive paths, backslashes and control characters. `build_working_directory.path="."` alone denotes its declared base root. Installed tool paths are informational absolute OS paths and are never passed to a bundle resolver. Inventories alone sort by `(base,path)` UTF-8 bytes; semantic arrays retain their specified order.

## Executable CLI and API

From the repository root, use the existing Python environment with `jsonschema` installed:

```text
python tools/validate_capture_import_provenance.py /path/to/declaration.json
python tools/validate_capture_import_provenance.py /path/to/closure.json --kind completion_closure
python -m tools.validate_capture_import_provenance /path/to/declaration.json
```

These are current structure-only commands. Success exits `0` and prints the five-field non-authorizing report stated above. Invalid JSON, encoding, structure or declared consistency exits `1` with `INVALID STRUCTURE:` on stderr; CLI usage errors exit `2`. A missing input file is an availability error with exit `1`, not executable evidence of rejecting a hostile artifact. No output artifacts are written.

`validate_artifact(value, *, kind=None)` validates an already parsed exact JSON object; `validate_bytes(data, *, kind=None)` additionally enforces duplicate-key detection and exact byte grammar. `artifact_bytes(value)` only serializes JSON and is neither an artifact validator nor a pin issuer. A standalone closure has no invented format/version field and therefore requires `kind="completion_closure"`. All other kinds dispatch by their fixed `format` values. The derived format is `anpc_runtime_derived_provenance_v1`; session-start, Teacher, and Human evidence use `anpc_collection_session_start_evidence_v1`, `anpc_teacher_run_completion_evidence_v1`, and `anpc_human_review_completion_evidence_v1` respectively, all with exact integer version `1`. Utility source retains the specified version-in-format spelling and has no added version field.

Invalid parsed-object input to `validate_artifact` is rejected through this module's `ValidationError`, including out-of-range exact integers whose Schema diagnostic exceeds the interpreter's integer-string digit limit. Rejection preserves the submitted values and the interpreter digit limit; numeric bounds and successful non-authorizing reports remain unchanged.

### Exact mapping declaration

`raw_capture` uses decoder field names except binary fields acquire `_base64` suffixes. Each `tensor_blocks` element wraps its original bytes with fixed `name,dtype,shape,data_base64`; the ten names/shapes/dtypes follow §4.3 with the batch axis removed. `snapshot_row` describes a target row, not a serialized replacement Snapshot. Its `row_ordinal` is zero-based. Import entries follow Snapshot row order; derived rows follow Dataset row order. Source Snapshot ordinals in a derived subset need not be contiguous.

| Source | Target / provenance class |
|---|---|
| Raw `episode_id,decision_id,input_content_hash` | Exact Snapshot identity; repeated in `snapshot_row` for the row join. |
| Raw `captured_at_server_time,scenario_family_id,map_seed,simulation_seed,candidate_set_hash,feature_contract_hash,target_handles,switch_cost_terms,captured_switch_cost` | Same-named Snapshot fields, wire origin. |
| Raw `generator_version,prompt_version,candidate_bytes_base64` | `generator_template_version,prompt_or_teacher_version,candidate_set_canonical_bytes`, wire origin; empty prompt text is preserved. |
| Raw `labels.*` | Same-named Snapshot label fields, wire origin. The raw selected index, sample ID, record version, label hash, annotator hash/agreement and CBOR remain in the sidecar. |
| Raw `group_dimensions` | `snapshot_row.groups` in §4.2 order, including Role; no family-driven rearrangement. |
| Raw `contract_hashes` | Ordered names in `snapshot_row.contract_hash_order`; raw optional final hash remains `""`. Runtime build is the original producer. |
| Raw `parent_policy_hash` and final contract hash | Independent normalized `parent_policy_sha256` and `source_decision_contract_hash`; each empty string becomes null separately. |
| Raw tensor blocks | `tensors[name]` and same-named flattened row values; actual decode/encode/semantic parity belongs to ML. |
| Catalog/episode closure | `template_id`; `profile_sha256` comes from the collection execution profile, never the Teacher Profile. |
| Pinned generated source | `semantic_binding.source` descriptor and exact semantic version texts; these versions are absent from wire. Supporting a historical binding must later be checked by the importer. |
| Importer policy | Snapshot version, candidate scope, raw `dagger` source spelling, float `0.0` weight, and `abstain` derived solely from the acceptable set. |

The validator checks in-object identity equality, raw blob digest syntax/hash consistency, the existing sample-ID and `ANPCFEAT1` formulas, mandatory tag/namespace/build/profile declarations, optional-hash normalization, group ordering and fixed tensor block sizes. It deliberately leaves CBOR content interpretation, Candidate/mask/label/Tensor semantics, real raw→Snapshot readback and generated binding authentication to the existing decoder and later ML context. A structurally consistent declaration can still describe invalid Capture or Snapshot data.

Derived `generation_code_sha256` is the existing Dataset manifest's ML transformation-code aggregate identity. `transformation_code={version,source}` binds the archived source description; its descriptor hash is not substituted for that aggregate. `runtime_build_evidence_sha256` separately identifies the original Runtime producer. These identities have distinct roles even if two digest strings happen to coincide. Neither a self-hash nor a prepublication Dataset hash is added to a capability object.

### Evidence grammar details

- Completion item fields are opaque exact identity references. Supplying an owner-looking namespace, public digest, reviewer name or serialized report cannot change the validator's result flags. No `expected`, `approved`, origin authorization or label authorization fields are accepted as extension dictionaries.
- Build inventories are duplicate-free and byte-sorted by `(base,path)`, before and after must agree, the project descriptor must be listed, and the known minimum includes the four Utility sources, project file, Config entries, collection/Capture Schema, registries, catalog, observation mapping contract and generated lock. This is a necessary declared minimum only. Full `Source/`, active plugin and selected-map dependency completeness requires later receipt/source inspection. `collection_schema_sha256` must agree with its inventory descriptor. Target/platform/configuration strings are recorded, not guessed or certified.
- Module inventories use the same lexical ordering, unique paths and module names. Compiler/linker/build-tool arrays preserve invocation order and forbid duplicate installed paths within each role. Build/launch argv preserves empty non-executable arguments; element zero must name an executable. Teacher Profile command arguments follow the existing nonempty-string-array restriction.
- Start evidence records disabled Live Coding/hot-reload states alongside real-path descriptors and loader-log references. The state strings do not establish cold start, patch-module absence or lifetime stability.
- Teacher requests preserve execution order. Each has exactly five attempts ordered by `call_index=0..4`; failed attempts retain a mandatory nonempty `provider_error` and a `raw_stdout` descriptor, including size zero when applicable. Returned attempts require null error. The error string may preserve line breaks. Later consensus receives the existing empty-response treatment for errors while separately retaining original stdout. Shape validation never executes that consensus or a provider.
- Teacher Profile scope/version and replay-provider restrictions match the existing Profile grammar. A fixture Profile declaration may be structurally represented, but it grants no Runtime label authority. Candidate authorization rejection and external `fixture_only` reporting belong to the later runner/context; this harness always reports `structure_only`.
- Human evidence requires a Teacher completion reference. Decision/source digests must match both descriptors and the reviewer-authorization declaration. Decision reviewers must exactly equal the unique NFC, UTF-8-sorted principal list. Owner workflow identity is a required separate field; matching text still does not authenticate reviewers.
- Exact decoded float32/float64 fields and canonical base64 use executable Schema extension keywords `x-float-width`, `x-canonical-base64`, and `x-decoded-size`. Plain JSON-Schema engines validate the standard shape but may ignore these extensions. The harness is required for the complete structural contract. Its integer checker and recursive constant checker distinguish `1` from `1.0` and booleans. No coercion, normalization repair or remote Schema retrieval occurs.

## Clause and coverage map

All test fixtures are synthetic declarations. Behavioral rejection tests validate a positive fixture before mutating it. Availability failures are recorded separately from accepted-hostile-input failures.

| Contract clause | Dedicated executable tests / deferred limit |
|---|---|
| §2.1 mandatory closure, no-Capture outcomes, replay | `test_independent_positive_shapes_grant_no_authority`, `test_ordered_replay_graph_and_no_capture_episode`, `test_duplicate_identities_and_paths`, all-object required-field tests; no external custody or full replay graph claim. |
| §2.1 strict closed JSON/path/type rules | `test_every_object_is_closed_and_all_authored_fields_required`, `test_hostile_boundary_rejected`, `test_strict_json_byte_grammar`, `test_lexical_paths_rejected_without_resolving`, `test_python_only_inputs_and_unknown_kind`; no filesystem containment claim. |
| §3.1 digests/canonical bytes/collection constraints | `test_catalog_digest_remains_separate_no_lf`, `test_schema_is_closed_local_and_reuses_collection_constraints`, inventory and type mutations. |
| §3.2–3.3 evidence grammar | Build/start positive fixtures, argv/toolchain/module mutations, `test_source_inventory_required_known_closure`, `test_source_inventory_minimum_is_not_just_project_file`, `test_additional_cross_field_boundaries`; no compile/load history claim. |
| §4 identity, label retention, groups, tensors | Raw/Snapshot hostile mutations and `test_existing_generated_tensor_group_source_contracts`; decoder byte lengths and generated names/shapes/dtypes are independent oracles, not inferred from the new Schema. |
| §4.5 independent policy lineage | `test_policy_lineages_remain_independent` covers all four combinations; no source-decision fallback. |
| §5 Teacher/Human completion grammar | Independent Teacher/Human positives, five-attempt/error/routing shape and decision/source/principal mutations; no provider execution, consensus reconstruction or reviewer authorization claim. |
| §6 derived identity/publication boundary | Derived positives, sample formula, row ordinal/source-weight/Human-reference mutations and `test_derived_has_explicit_generation_code_identity`; no issuance/lifecycle capability. |
| §7–8 no authority, read-only API/CLI | Every success report stays false for origin/label/training/Production. `test_cli_valid_and_malformed`, `test_cli_usage_and_bad_json`, `test_no_descriptor_reads_or_remote_schema` exercise real calls and exit codes. |
| §9 named security regressions | Deferred executable authority/Runtime/ML work; structural tests do not close these acceptance cases. |

## Deferred enforcement and evidence classification

- **Issuer/storage:** independent anchors, actual execution observation, publish-last/readback, immutable custody, same-index/different-closure refusal, fixture namespace separation.
- **Resolver/context:** exact target bytes, symlinks and path races, full index/session/episode/replay/catalog closure, external replay cycles, supported historical binding, actual source and build provenance.
- **Runtime:** complete source/plugin/map dependency closure, clean compile/link receipt verification, current installed/source comparison, new process and loaded-module history, no post-start patch loads.
- **ML:** same-byte Capture decode; full raw→Snapshot tensor/label/group parity; semantic contract support; Teacher request projection/consensus/review routing; independent Teacher/reviewer issuance; mapping and public final Dataset acceptance; fresh-process reconstruction and qualification.

No Schema test is evidence that the named §9 security exploits are fixed. Synthetic fixtures in the dedicated tests represent artifact shapes only; they are never entered into owner storage or real Capture directories, and their build/provider/reviewer strings are not execution evidence. Later source-bound specification and quality reviews remain separate.
