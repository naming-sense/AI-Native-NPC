## 25.8 KPI

고정 평가 버전:

```text
utility_baseline_v1.0.0
schema 2.0.0
target_slotter 1.0.0
postprocess 1.0.0
critical_suite_v1
```

Gate:

- General Target Recall 20,000 states: point ≥99.5%, Wilson lower ≥99.0%
- Candidate Recall 동일
- Critical Suite 576 sequences: 100%
- Safety Fuzz 100,000 decisions: hard-constraint Commit 0
- Hidden Leakage 10,000 pair: 0
- ECE ≤0.05
- Brier ≤0.18
- OOD recall ≥0.90 at FPR ≤0.10
- Naturalness A/B: 600 sequence×3명, point ≥55%, CI lower >52%
- Goal completion 비열등: lower bound ≥ -2.0pp
- 불필요한 switch 비열등: upper ≤ +0.2 switch/10s
- stable scenario p95 ≤3 switch/10s

---

## 25.9 고정 Critical/OOD Family

Critical 9 family와 OOD 9 family 이름은 `test_taxonomy_v1.yaml`을 단일 원본으로 사용한다. Critical은 family당 최소 64 case, 총 최소 576 sequences다.

Critical family:

- `perception_belief_visibility`
- `typed_target_slotting`
- `goal_arbitration_transition`
- `candidate_mask_and_hash`
- `async_latest_only_and_atomic_commit`
- `hidden_information_boundary`
- `skill_parameter_and_resource_cas`
- `save_load_hot_swap_recovery`
- `boss_pattern_mask_lock_interrupt_fairness`

OOD family:

- `feature_range_shift`
- `missing_modality_pattern`
- `unseen_role_attribute_combination`
- `candidate_count_pattern`
- `belief_age_confidence_shift`
- `environment_layout_density_shift`
- `event_sequence_shift`
- `sensor_noise_shift`
- `boss_pattern_phase_composition_shift`
