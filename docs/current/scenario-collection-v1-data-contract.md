# Scenario collection V1 data contract

This contract defines validation-tool inputs and collection sidecars. It does not approve a training distribution or assert that spatial placements work in Unreal. All files and Python APIs below are new; existing Capture label `source_type` remains unchanged. No Snapshot, Teacher, Gold, Dataset row, or production implementation is produced by this harness.

## Authority and trust

- Authority: `contracts/current/scenario_collection_v1.schema.json` (JSON Schema 2020-12) and `contracts/current/scenario_catalog_v1.json`.
- Every object rejects unknown fields. JSON loading rejects duplicate keys and nonfinite numbers. Integers must be JSON integers, not booleans or integral floats. Hashes are lowercase hexadecimal SHA-256.
- `catalog_sha256` is SHA-256 of UTF-8 `json.dumps(catalog, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)`. Other artifact/contract hashes bind exact file bytes. Whitespace changes alone do not change catalog identity.
- The caller supplies trusted `expected_profile_sha256` and `expected_runtime_build_sha256`; comparing two untrusted declarations is not external provenance verification. Contract hashes bind this collection schema and the current Capture schema/skill/goal constants from the existing validator.
- All identifiers for sessions, collection episodes, replay links, and diagnostic entries are lowercase UUIDv4. The caller maintains the session-ID inventory across processes. IDs must never be reused; Capture `episode_id` is preserved separately as printable ASCII.
- Trusted collection roots must be private/stable while validating or publishing. Lexical absolute/drive/backslash/parent traversal paths and resolved symlink escapes are rejected. `confine_artifact_path(..., must_not_exist=True)` checks every existing alias before publication but is not an atomic writer: a production writer must additionally use exclusive creation and protect ancestor directories against concurrent substitution. This harness writes no artifacts.

## Catalog

Top-level fields: `format="scenario_catalog_v1"`, `version=1`, `scope="production_candidate"`, `support_semantics="code_supported_pending_runtime_validation"`, `variation_scope="tool_validation_defaults"`, `scenarios`.

Each scenario has `id`, `version=1`, `title`, `description`, `supported`, `unsupported_reason` (null for supported, nonempty for unsupported), `scenario_family_id`, `template_family`, `layout_family`, `event_sequence_family`, `map`, `variations`, `events`, `termination`.

The sole map is `/Game/AINativeNPC/Maps/L_AINativeNPC_MVP`. Variations are exactly `distance_cm=[400,600]`, `approach_angle_deg=[0]`, `seed=[0,1,2]`. These are tool-validation defaults, not approved placements or sample quotas. Relationship/identity/reachability parameters cannot be injected as new condition keys.

Supported IDs: `hearing_only`, `hearing_appearance`, `hearing_appearance_loss`. Unsupported IDs: `relationship_friendly`, `relationship_hostile`, `low_identity`, `unreachable_greet`. Each unsupported item has an explicit reason and an empty event list. The complete required set is enforced.

Supported ordered events use closed typed objects:

| Type | Fields in addition to `order`, `type`, `timeout_seconds` | Meaning |
|---|---|---|
| `move_for_hearing` | `trigger="episode_running"`, `movement_seconds` | Real player movement/footsteps through production sensing |
| `appear` | `trigger="hearing_observed"` | Real appearance after observed hearing, bounded by timeout |
| `lose_target` | `trigger="appearance_observed"` | Real target loss after observed appearance, bounded by timeout |

Orders are contiguous from zero; event types must match the scenario ID's sequence. Events specify causes, never expected NPC decisions, commands, classes, or asset references. Runtime must verify observed triggers rather than inject Knowledge. `termination` has positive `max_duration_seconds`, `preparation_timeout_seconds`, `max_decisions`; each event deadline and their sum fit the episode duration. Defaults are 30 seconds / 10 seconds / 100 decisions, with 10-second event bounds and 2-second hearing movement. Actual event timing is recorded on the episode.

## Observation mapping metadata

`observation_mapping_version` is required on sessions, resolved episodes, committed Capture sidecars and diagnostic entries, with the exact value `observed_geometry_goal_v1`. It follows `docs/current/scenario-observation-adapter-v1-contract.md` and is compared along with controller/mode/source at every sidecar boundary and on replay creation. It identifies the bounded observed geometry/Goal mapping; it does not claim all-feature runtime support or enable relationship, personality, identity-confidence or unreachable-path axes. This is collection provenance metadata, separate from the existing Capture label `source_type`. Current Capture envelope identity is unchanged; the harness binds the version to the sidecar and makes no assertion that a new field exists inside raw Capture bytes. Producer-to-sidecar readback and feature verification remain Runtime integration work.

## Session

`format="scenario_collection_session_v1"`, `version=1`, `session_id`, `catalog_sha256`, `profile_sha256`, `runtime_build_sha256`, `contract_hashes`, `observation_mapping_version`, `input_source`, `execution_mode`, `controller`, `limits`.

`contract_hashes` has exactly `collection_schema_sha256`, `capture_schema_sha256`, `skill_registry_sha256`, `goal_registry_sha256`. `limits` has `max_episodes`, `episode_timeout_seconds`, `preparation_timeout_seconds`, `storage_limit_bytes`; all are positive and schema-bounded. Episode limits also must fit the chosen scenario termination bounds. Time values are elapsed monotonic seconds, never fabricated wall-clock timestamps.

Collection `input_source` is exactly `human_play|automated_runtime|offline_procedural|test_fixture`. `execution_mode` is `manual|automatic|replay`. `controller` is `human|automated`.

- Human controller requires `human_play`, with manual or replay mode.
- Automated controller rejects `human_play`; manual mode requires a human controller.
- Automatic mode requires an automated controller. Replay explicitly retains the current controller/source; it never infers human provenance from its ancestor.
- Offline/test provenance is structurally representable for tooling but grants no production eligibility. Real Runtime collection must supply genuine automated-runtime or human provenance.

## Resolved episode

`format="scenario_collection_episode_v1"`, `version=1`, `session_id`, `collection_episode_id`, optional `replay_of`, `scenario_id`, `scenario_version`, `variant_id`, `map`, `conditions`, `seeds`, `family`, `observation_mapping_version`, `input_source`, `execution_mode`, `controller`, `state`, `reason`, `reset_result`, `event_observations`.

`conditions` is exactly `{distance_cm, approach_angle_deg, seed}` selected from catalog values. `seeds` is `{map_seed, simulation_seed}`, both equal to the chosen condition seed. `variant_id` is exactly `d{distance_cm}-a{approach_angle_deg}-s{seed}`. `family` contains the catalog's four family fields plus `split`, one of `unassigned|train|validation|calibration|test|ood|critical`.

`state` is `preparing|running|completed|cancelled|timed_out|failed`. Active states have null reason and `reset_result="not_attempted"`; terminal states require a nonempty reason, with `reset_result=not_attempted|verified|failed|unverified`. `event_observations` is an ordered prefix of `{order, observed_at_seconds}` with monotonic elapsed timestamps no later than `episode_timeout_seconds`. Preparing has no event observations; completed requires the entire supported sequence, with every required observation strictly before `episode_timeout_seconds`. An observation at expiration cannot establish completion, matching lifecycle timeout precedence. Timeout/failure records may retain a prefix at the deadline; diagnostic entries remain available for reporting expiration.

Replay mode requires `replay_of` and a supplied original episode; other modes forbid the link. `replay_episode(original, new_id, session)` creates a new preparing record with identical scenario/version/variant/map/conditions/seeds/family and a direct predecessor link, using the new session's source/controller. Full validation requires the original's linkage/conditions. It promises repeated conditions, not identical world results or Capture identity.

## Index and diagnostics

Top-level: `format="scenario_collection_index_v1"`, `version=1`, `session_id`, `entries`. Declared counts, row claims, and approval flags are rejected as unknown fields. Every entry has `kind`, `collection_episode_id`, `observation_mapping_version`, `input_source`, `execution_mode`, `controller`, `family`, matching the supplied episode/session.

Committed entry (`kind="committed"`) adds:

- `capture_identity={episode_id, decision_id, input_content_hash, sample_id}`: exact existing Capture identity, never derived from collection ID.
- `capture={path,size_bytes,sha256}` and `committed={path,size_bytes,sha256}`. Paths are canonical root-relative POSIX names; capture ends in `.anpccap2`, marker is precisely capture path plus `.committed`.
- Validation reads the Capture and marker once each, verifies their declared byte sizes and hashes, and passes those same immutable byte images to `tools.validate_anpc_capture_v2.decode_committed_capture_bytes`. The decoder checks marker binding and Capture validity without reopening either path. The existing root confinement and resolved Capture/marker alias checks still apply. Later path replacement cannot substitute the image being validated: an invalid pinned image is rejected, and a valid pinned image remains the validation input. This does not replace the caller's stable-root/publication obligations.
- `validate_committed_entry` compares the decoded identity and scenario family and returns exactly the existing Capture validator's summary fields, excluding decoded payload fields. `validate_index` additionally compares map/simulation seeds. Duplicate identities, sample IDs, episode/decision pairs and artifact paths are rejected. Each episode's committed decisions must fit its catalog `max_decisions`. Capture label source is not reinterpreted as collection source. Rehashing forged sidecar identities does not promote them.

Diagnostic entry (`kind="diagnostic"`) adds `diagnostic_id`, `observed_id` (null or actual observed printable identifier), `stage=preparation|execution|capture|storage|reset`, `reason`, `observed_at_seconds`, `snapshot_present`, `snapshot_ref` (null or the same artifact descriptor shape). `snapshot_present=false` requires `snapshot_ref=null`; true requires an existing, hash-verified artifact. Capture identity/committed fields are forbidden in diagnostics. Producers must only record observed identifiers; the validator cannot prove a supplied string was actually observed. Diagnostics never increment committed or validated-row counts.

`validate_index` validates all referenced episodes, pins the session, verifies bytes, checks family splits and referenced-artifact storage budget, and returns `{collection_episode_count, committed_capture_count, diagnostic_count, validated_row_count:0, production_eligible:false}`. A committed Capture is not a labeled Dataset row. Existing baseline counts and raw file counts are never validation evidence. Runtime must budget sidecar/index bytes and in-flight publication overhead as well; this read-only harness has no storage writer.

## Pure lifecycle and split APIs

Public reusable APIs live in `tools.validate_scenario_collection` and raise its `ValidationError(ValueError)` on invalid input:

- `load_catalog(path=CATALOG_PATH) -> dict`; `validate_catalog(catalog) -> None`; `catalog_digest(catalog) -> str`; `contract_hashes() -> dict`.
- `validate_structure(kind, value) -> None`, where kind is `catalog|session|episode|index|entry|diagnostic`.
- `validate_conditions(catalog, scenario_id, conditions) -> dict` returns the selected scenario after strict membership checks.
- `validate_session(session, catalog, *, expected_profile_sha256, expected_runtime_build_sha256, seen_session_ids=()) -> None`.
- `validate_episode(episode, session, catalog, *, replay_original=None) -> None`; `replay_episode(original, new_id, session) -> dict`.
- `confine_artifact_path(root, relative_path, *, must_exist=True, must_not_exist=False) -> Path`.
- `validate_committed_entry(entry, root) -> dict` returns the existing Capture validator summary after exact binding.
- `validate_family_splits(episodes) -> None`: rejects cross-split sharing of any scenario/template/layout/event-sequence family. `unassigned` is not a split assignment. Seeds do not make a new family. This initial catalog shares template/layout, so it cannot alone populate mutually independent splits.
- `validate_index(index, root, session, episodes, catalog, *, expected_profile_sha256, expected_runtime_build_sha256, replay_originals=()) -> dict`. `episodes` is the current session's ordered execution history: all but the final record require terminal state and verified reset. Replay lookup contains only external predecessors and the already validated current-session prefix; forward links, cycles and self-links are rejected. `replay_originals` supplies separately validated predecessor records from earlier sessions; each must have a different `session_id` from the current session and an ID distinct from every current episode and other external predecessor. These records are not counted as current-session episodes. The caller must validate those predecessors against their original trusted sessions before passing them; their structural/provenance validity and unchanged replay conditions are checked again here. An external predecessor followed by an ordered chain of current-session replays is permitted, preserving the same-conditions/new-ID rule.
- `new_lifecycle(session) -> Lifecycle`; `transition(lifecycle, event, *, at_seconds, collection_episode_id=None, reason=None) -> Lifecycle`.

Lifecycle is immutable. `start` enters preparing (fresh ID, episode budget, only idle). `ready` enters running. `completed`, `cancelled`, `failed` enter awaiting-reset and require a reason. `check_timeout` enters timed-out awaiting-reset at preparation or whole-episode deadlines. Reset callbacks (`reset_verified`, `reset_failed`, `reset_unverified`) require an already awaiting-reset state; this precondition is checked before deadline conversion, including at or past a deadline. An out-of-order reset raises `ValidationError` and returns no state. The caller/runner must terminate the session on a lifecycle validation error, rather than continue from the previous immutable state. At or past a deadline, non-reset actions are first converted to timeout, so late completion cannot hide expiration. Whole-episode time includes preparation. From awaiting-reset, `reset_verified` returns to idle; `reset_failed` or `reset_unverified` permanently blocks this session. Timeout conversion cannot discard an explicit reset result. Reset result is not inferred from absence of errors. No second active episode, reused ID, skipped reset, unknown event, backwards/nonfinite time or budget overrun is accepted. Terminal outcome/reason remain in `last_outcome`/`last_reason` through reset. The caller persists episode terminal records before starting another episode. Storage failure is represented as a failed terminal event followed by blocked/unverified reset; index byte limits separately fail closed.

## Runtime enforcement — Host와 회차 소유자

활성 [Host 관측·수집 발행 계약](scenario-host-capture-v1-contract.md)은 Task 2의 호출 순서·실패 latch·출처 vocabulary·append-only Writer/Reader·sidecar 집행을 정의한다. 현재 단계는 문서·하네스이며 Host/bridge Runtime 구현과 실제 owner/권한 검증은 후속이다. 위 closed field 집합과 immutable lifecycle은 유지한다.

- 잘못된 관측/모순된 target의 mapping 실패는 해당 회차를 종료하고 retry epoch/lease를 revoke한다. deadline 전에는 failed, at/after deadline에는 기존 timed_out 우선순위를 유지하며 실제 관측 실패를 diagnostic에 보존한다. terminal evidence의 persist/readback과 verified reset 뒤 새 회차만 허용한다. 같은 실패 회차의 Decision retry는 금지한다.
- 정상 sensor 부재·event trigger 미충족은 wait/timeout이며 유효 위치 전용 primary·missing sentinel은 정상 입력이다. adapter bool만 있는 실패 reason은 observation_mapping_failed다. 세부 원인은 직접 검사한 precondition만 사용한다. 비수집 legacy retry는 유지한다.
- reset failed/unverified, storage·sidecar·diagnostic persistence 실패는 session blocked다. 원본 Capture/marker를 보존하고 완료 pin 발행을 막는다. diagnostic artifact가 없는 메모리 Snapshot은 false/null로 남긴다.
- Host는 승격 전 Knowledge 복사와 Finalize 직전 Populate를 집행한다. producer의 실제 Skill start는 marker보다 앞이며, same-image committed readback 뒤 producer verified, sidecar exact readback 뒤 collection accepted를 별도로 기록한다. sidecar 실패로 실제 start/producer 성공 수를 소급 삭제하지 않는다.
- Task 2는 signal/lease/latch를 제공한다. Task 3 owner가 reentrant committed-start stack을 drain한 뒤 실제 입력·예약 사건을 정지하고 World reset을 검증한다. Task 4는 독립 completion pin/closure 권한을 검증한다. public bool/digest로 이 owner를 대체하지 않는다. 여덟 group의 정확한 생산·대조 규칙은 연결 계약을 따르며 새 wire/collection field는 추가하지 않는다.

## Executable boundary and pending work

CLI: `python -m tools.validate_scenario_collection [--catalog PATH]` validates the catalog and prints its digest and scenario count; invalid input exits 1. JSON Schema validation uses installed `jsonschema` (2020-12) without environment changes. The Python harness provides all session/episode/index/lifecycle operations; it is not a Runtime runner or ML importer.

Named pending integration: **capture_payload_import**. This harness reuses the parser owner's implemented immutable-byte decoder to validate the exact hash-bound Capture/marker images. Its public committed-entry result remains the existing summary (identity, seeds, family/group summary and validation results); decoded tensor/label payloads are not exposed by that result or imported into Dataset rows. A later importer must reuse the same decoder and explicitly map its detailed fields; it must not implement a second parser or synthesize payloads. The current sidecar binds externally pinned build/profile metadata but cannot independently prove those values came from Capture bytes. Group-dimension mapping, contract provenance beyond the existing parser's checks, model-input coverage fingerprints, exclusive Runtime publication, true event observations, reset verification, real placement validation and human play remain Runtime/ML integration acceptance work.
