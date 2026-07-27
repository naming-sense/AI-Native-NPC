## E.1 고정 평가 버전

- Utility Baseline: `utility_baseline_v1.0.0`
- Schema: `2.0.0`
- Target Slotter: `1.0.0`
- Post-process: `1.0.0`
- Critical Suite: `critical_suite_v1`, **512 sequences = 8 family × 64 case**

### E.1.1 Critical Family

1. `perception_belief_visibility`
2. `typed_target_slotting`
3. `goal_arbitration_transition`
4. `candidate_mask_and_hash`
5. `async_latest_only_and_atomic_commit`
6. `hidden_information_boundary`
7. `skill_parameter_and_resource_cas`
8. `save_load_hot_swap_recovery`

### E.1.2 OOD Family

1. `feature_range_shift`
2. `missing_modality_pattern`
3. `unseen_role_attribute_combination`
4. `candidate_count_pattern`
5. `belief_age_confidence_shift`
6. `environment_layout_density_shift`
7. `event_sequence_shift`
8. `sensor_noise_shift`

## E.2 Candidate/Target

| Metric | Dataset | Gate |
|---|---|---|
| Target Recall | General Test 20,000 states | point ≥99.5%, Wilson 95% lower bound ≥99.0% |
| Any-Acceptable Candidate Recall | General Test 20,000 states | point ≥99.5%, Wilson 95% lower bound ≥99.0% |
| Critical Target/Candidate Recall | Critical Suite 512 sequences | 100%, 분모와 miss 모두 보고 |
| MandatoryOverflow | Critical + General | 0건 |

## E.3 Safety

절대 Gate:

- Critical Suite 512 sequences에서 hard-constraint 위반 Commit 0건
- Randomized Safety Fuzz 100,000 decision에서 hard-constraint 위반 Commit 0건
- Hidden Information Leakage Test 10,000 pair에서 Tensor/행동 누출 0건
- Server authority 우회 0건

Safety는 Baseline 비열등만으로 대체할 수 없다.
