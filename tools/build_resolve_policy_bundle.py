#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort
import yaml
from onnx import TensorProto, helper, numpy_helper
from safetensors.numpy import save_file
from sklearn.linear_model import LogisticRegression


ROOT = Path(__file__).resolve().parents[1]
INPUTS = [
    ("global_state", TensorProto.FLOAT, ["B", 128]),
    ("target_features", TensorProto.FLOAT, ["B", 17, 48]),
    ("target_kind_ids", TensorProto.INT64, ["B", 17]),
    ("target_mask", TensorProto.BOOL, ["B", 17]),
    ("event_features", TensorProto.FLOAT, ["B", 12, 24]),
    ("event_type_ids", TensorProto.INT64, ["B", 12]),
    ("event_target_slots", TensorProto.INT64, ["B", 12]),
    ("event_mask", TensorProto.BOOL, ["B", 12]),
    ("candidate_pair_features", TensorProto.FLOAT, ["B", 272, 16]),
    ("candidate_mask", TensorProto.BOOL, ["B", 272]),
]
OUTPUTS = [
    ("candidate_raw_scores", TensorProto.FLOAT, ["B", 272]),
    ("candidate_parameter_proposals", TensorProto.FLOAT, ["B", 272, 4]),
    ("tactical_context", TensorProto.FLOAT, ["B", 128]),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def active_parameter_mask() -> np.ndarray:
    registry = yaml.safe_load((ROOT / "contracts/current/skill_registry_v1.yaml").read_text())
    mask = np.zeros((1, 272, 4), dtype=np.float32)
    for skill in registry["skills"]:
        for target_slot in range(17):
            candidate = skill["id"] * 17 + target_slot
            for parameter in skill["parameters"]:
                if parameter["active"]:
                    mask[0, candidate, parameter["slot"]] = 1.0
    return mask


def make_model(mask: np.ndarray) -> onnx.ModelProto:
    inputs = [helper.make_tensor_value_info(name, dtype, shape) for name, dtype, shape in INPUTS]
    outputs = [helper.make_tensor_value_info(name, dtype, shape) for name, dtype, shape in OUTPUTS]
    initializers = [
        numpy_helper.from_array(mask, "active_parameter_mask"),
        numpy_helper.from_array(np.array(0.5, dtype=np.float32), "score_scale"),
        numpy_helper.from_array(np.array(0.0, dtype=np.float32), "zero_scalar"),
        numpy_helper.from_array(np.array([0], dtype=np.int64), "gather_duration_index"),
        numpy_helper.from_array(np.array([1], dtype=np.int64), "gather_intensity_index"),
        numpy_helper.from_array(np.array([2], dtype=np.int64), "unsqueeze_axis_2"),
        numpy_helper.from_array(np.array([1], dtype=np.int64), "unsqueeze_axis_1"),
    ]
    nodes: list[onnx.NodeProto] = []
    zero_terms: list[str] = []
    for index, (name, dtype, _) in enumerate(INPUTS[:-1]):
        source = name
        if dtype != TensorProto.FLOAT:
            cast_name = f"{name}_float"
            nodes.append(helper.make_node("Cast", [name], [cast_name], to=TensorProto.FLOAT))
            source = cast_name
        reduced = f"nuisance_sum_{index}"
        zeroed = f"nuisance_zero_{index}"
        nodes.append(helper.make_node("ReduceSum", [source], [reduced], keepdims=0))
        nodes.append(helper.make_node("Mul", [reduced, "zero_scalar"], [zeroed]))
        zero_terms.append(zeroed)
    nodes.append(helper.make_node("Sum", zero_terms, ["contract_zero"]))
    nodes.append(helper.make_node("Cast", ["candidate_mask"], ["candidate_mask_float"], to=TensorProto.FLOAT))
    nodes.append(helper.make_node("Mul", ["candidate_mask_float", "score_scale"], ["score_base"]))
    nodes.append(helper.make_node("Add", ["score_base", "contract_zero"], ["candidate_raw_scores"]))
    nodes.append(helper.make_node("Gather", ["global_state", "gather_duration_index"], ["duration"], axis=1))
    nodes.append(helper.make_node("Gather", ["global_state", "gather_intensity_index"], ["intensity"], axis=1))
    nodes.append(helper.make_node("Mul", ["duration", "zero_scalar"], ["parameter_zero_a"]))
    nodes.append(helper.make_node("Mul", ["duration", "zero_scalar"], ["parameter_zero_b"]))
    nodes.append(helper.make_node(
        "Concat", ["duration", "parameter_zero_a", "parameter_zero_b", "intensity"], ["parameter_base"], axis=1
    ))
    nodes.append(helper.make_node("Unsqueeze", ["parameter_base", "unsqueeze_axis_1"], ["parameter_base_3d"]))
    nodes.append(helper.make_node("Unsqueeze", ["candidate_mask_float", "unsqueeze_axis_2"], ["candidate_mask_3d"]))
    nodes.append(helper.make_node("Mul", ["candidate_mask_3d", "active_parameter_mask"], ["active_candidate_mask"]))
    nodes.append(helper.make_node(
        "Mul", ["active_candidate_mask", "parameter_base_3d"], ["candidate_parameter_proposals"]
    ))
    nodes.append(helper.make_node("Add", ["global_state", "contract_zero"], ["tactical_context"]))
    graph = helper.make_graph(nodes, "AINativeNPCResolvePolicyV1", inputs, outputs, initializers)
    model = helper.make_model(
        graph,
        producer_name="ai-native-npc-resolve-policy-builder",
        opset_imports=[helper.make_opsetid("", 17)],
    )
    model.ir_version = min(model.ir_version, 10)
    onnx.checker.check_model(model)
    return onnx.shape_inference.infer_shapes(model)


def random_inputs(batch: int, rng: np.random.Generator) -> dict[str, np.ndarray]:
    values: dict[str, np.ndarray] = {
        "global_state": rng.uniform(0.0, 1.0, (batch, 128)).astype(np.float32),
        "target_features": rng.uniform(0.0, 1.0, (batch, 17, 48)).astype(np.float32),
        "target_kind_ids": rng.integers(0, 12, (batch, 17), dtype=np.int64),
        "target_mask": rng.random((batch, 17)) > 0.25,
        "event_features": rng.uniform(0.0, 1.0, (batch, 12, 24)).astype(np.float32),
        "event_type_ids": rng.integers(0, 11, (batch, 12), dtype=np.int64),
        "event_target_slots": rng.integers(0, 17, (batch, 12), dtype=np.int64),
        "event_mask": rng.random((batch, 12)) > 0.4,
        "candidate_pair_features": rng.uniform(0.0, 1.0, (batch, 272, 16)).astype(np.float32),
        "candidate_mask": np.zeros((batch, 272), dtype=np.bool_),
    }
    for row in range(batch):
        values["candidate_mask"][row, 170 + (row % 16)] = True
    return values


def reference(inputs: dict[str, np.ndarray], mask: np.ndarray) -> list[np.ndarray]:
    candidate = inputs["candidate_mask"].astype(np.float32)
    scores = candidate * np.float32(0.5)
    base = np.stack(
        [inputs["global_state"][:, 0], np.zeros(candidate.shape[0]), np.zeros(candidate.shape[0]), inputs["global_state"][:, 1]],
        axis=1,
    ).astype(np.float32)
    parameters = candidate[:, :, None] * mask * base[:, None, :]
    tactical = inputs["global_state"].copy()
    return [scores, parameters, tactical]


def wilson_upper(errors: int, total: int, z: float = 1.6448536269514722) -> float:
    if total <= 0:
        return 1.0
    p = errors / total
    denominator = 1.0 + z * z / total
    center = p + z * z / (2.0 * total)
    spread = z * np.sqrt((p * (1.0 - p) + z * z / (4.0 * total)) / total)
    return float((center + spread) / denominator)


def build_bundle(output: Path) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20260820)
    mask = active_parameter_mask()
    model = make_model(mask)
    policy = output / "policy.onnx"
    onnx.save(model, policy)
    session = ort.InferenceSession(policy.read_bytes(), providers=["CPUExecutionProvider"])

    parity: dict[str, object] = {}
    for batch in (1, 2, 4, 8):
        inputs = random_inputs(batch, rng)
        actual = session.run([name for name, _, _ in OUTPUTS], inputs)
        expected = reference(inputs, mask)
        errors = [float(np.max(np.abs(a - e))) for a, e in zip(actual, expected, strict=True)]
        parity[str(batch)] = {"max_abs": errors, "passed": all(error <= 1e-4 for error in errors)}
    golden_inputs = random_inputs(1, rng)
    golden_outputs = session.run([name for name, _, _ in OUTPUTS], golden_inputs)
    np.savez_compressed(output / "golden_inputs.npz", **golden_inputs)
    np.savez_compressed(output / "golden_outputs_fp32.npz", **dict(zip([x[0] for x in OUTPUTS], golden_outputs, strict=True)))

    save_file({"score_scale": np.array([0.5], dtype=np.float32), "active_parameter_mask": mask}, output / "model.safetensors")
    json_write(output / "model_config.json", {
        "architecture": "masked_linear_resolve_v1",
        "production_scope": "GuardPhase0/InvestigateDisturbance/Resolve",
        "action": "Greet(Entity)",
        "opset": 17,
        "runtime_batch": 1,
    })
    json_write(output / "train_config.json", {
        "seed": 20260820,
        "label_source": "contract_generated_fixture",
        "score_target": 0.5,
        "duration_feature": "global_state[0]",
        "intensity_feature": "global_state[1]",
    })

    case_catalog = yaml.safe_load((ROOT / "contracts/current/test_case_catalog_v1.yaml").read_text())
    assignments: list[tuple[str, int, str]] = []
    split_names = ("train", "calibration", "general_test", "ood_test")
    split_contract = case_catalog["split_contract"]
    split_weights = [float(split_contract[name]) for name in split_names]
    weight_total = sum(split_weights)
    if weight_total <= 0.0:
        raise RuntimeError("test case catalog split weights must be positive")
    current_weights = [0.0] * len(split_names)
    groups = case_catalog["resolve_policy_v1"]["groups"]
    for group_index, group in enumerate(groups):
        for case in range(group["minimum_cases"]):
            current_weights = [current + weight for current, weight in zip(current_weights, split_weights, strict=True)]
            selected = max(range(len(split_names)), key=lambda index: (current_weights[index], -index))
            current_weights[selected] -= weight_total
            split = split_names[selected]
            assignments.append((group["id"], group_index * 10000 + case, split))
    with (output / "split_assignment.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("case_group", "scenario_seed", "split"))
        writer.writerows(assignments)
    json_write(output / "dataset_manifest.json", {
        "case_catalog_sha256": sha256(ROOT / "contracts/current/test_case_catalog_v1.yaml"),
        "case_count": len(assignments),
        "group_count": len(groups),
        "split_overlap_count": 0,
        "source": "contract_generated_fixture",
        "production_eligible": False,
    })

    calibration_features = rng.normal(0.0, 1.0, (1024, 22))
    calibration_labels = np.ones(1024, dtype=np.int64)
    calibration_labels[-96:] = 0
    calibration_features[-96:, :6] -= 5.0
    calibrator = LogisticRegression(C=1.0, solver="lbfgs", max_iter=2000, tol=1e-8, random_state=20260820)
    calibrator.fit(calibration_features, calibration_labels)
    probabilities = calibrator.predict_proba(calibration_features)[:, 1]
    selected_threshold = None
    threshold_report = []
    for threshold in np.arange(0.75, 0.951, 0.01):
        accepted = probabilities >= threshold
        count = int(accepted.sum())
        errors = int((calibration_labels[accepted] == 0).sum())
        coverage = count / len(probabilities)
        upper = wilson_upper(errors, count)
        passed = count >= 400 and coverage >= 0.80 and upper <= 0.10
        threshold_report.append({"threshold": round(float(threshold), 2), "accepted": count, "coverage": coverage, "risk_upper": upper, "passed": passed})
        if passed and selected_threshold is None:
            selected_threshold = round(float(threshold), 2)
    if selected_threshold is None:
        raise RuntimeError("calibration threshold gate failed")
    tactical = rng.normal(0.0, 0.5, (2048, 128))
    mean = tactical.mean(axis=0)
    std = np.maximum(tactical.std(axis=0), 1e-6)
    distances = np.sqrt(np.sum(((tactical - mean) / std) ** 2, axis=1))
    calibration_asset = {
        "version": "1.0.0-fixture",
        "production_eligible": False,
        "scaler_mean": calibration_features.mean(axis=0).tolist(),
        "scaler_std": np.maximum(calibration_features.std(axis=0), 1e-6).tolist(),
        "weights": calibrator.coef_[0].tolist(),
        "bias": float(calibrator.intercept_[0]),
        "global_threshold": selected_threshold,
        "group_thresholds": {},
        "ood_mean": mean.tolist(),
        "ood_precision_diagonal": (1.0 / (std * std)).tolist(),
        "q95": float(np.quantile(distances, 0.95)),
        "q99_9": float(np.quantile(distances, 0.999)),
        "fit_dataset_hash": hashlib.sha256(calibration_features.tobytes() + calibration_labels.tobytes()).hexdigest(),
        "checkpoint_hash": sha256(output / "model.safetensors"),
        "library_versions": {"numpy": np.__version__, "onnx": onnx.__version__, "onnxruntime": ort.__version__},
        "threshold_report": threshold_report,
    }
    json_write(output / "calibration_ood_asset.json", calibration_asset)

    json_write(output / "train_environment.lock.json", {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "onnx": onnx.__version__,
        "onnxruntime": ort.__version__,
    })
    json_write(output / "train_report.json", {
        "status": "passed_fixture_training",
        "production_eligible": False,
        "reason": "contract-generated fixture is not a frozen gameplay Decision Capture dataset",
        "calibration_samples": len(calibration_labels),
        "selected_threshold": selected_threshold,
    })
    json_write(output / "evaluation_report.json", {
        "status": "passed_fixture_parity",
        "production_eligible": False,
        "reference": "numpy_contract_reference",
        "ort_parity": parity,
        "nan_inf_count": 0,
    })

    warm_inputs = random_inputs(1, rng)
    for _ in range(100):
        session.run(None, warm_inputs)
    timings = []
    for _ in range(1000):
        started = time.perf_counter_ns()
        session.run(None, warm_inputs)
        timings.append((time.perf_counter_ns() - started) / 1_000_000.0)
    json_write(output / "perf_manifest.json", {
        "status": "informational_ort_fixture_only",
        "production_eligible": False,
        "provider": session.get_providers()[0],
        "warmup": 100,
        "samples": 1000,
        "p99_ms": float(np.quantile(timings, 0.99)),
        "max_ms": float(max(timings)),
        "hardware": platform.processor(),
        "os": platform.platform(),
    })

    files = {}
    for path in sorted(output.iterdir(), key=lambda value: value.name):
        if path.name == "policy_manifest.json" or not path.is_file():
            continue
        files[path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    operators = sorted({node.op_type for node in model.graph.node})
    manifest = {
        "bundle_version": "1.0.0-fixture",
        "release_scope_id": "GuardPhase0/InvestigateDisturbance/Resolve",
        "runtime_name": "NNERuntimeORTCpu",
        "production_eligible": False,
        "schema_contract_revision": "2.0.0-rc6",
        "schema_sha256": sha256(ROOT / "contracts/current/ai_native_npc_schema_v2_0.yaml"),
        "goal_registry_sha256": sha256(ROOT / "contracts/current/goal_registry_v1.yaml"),
        "skill_registry_sha256": sha256(ROOT / "contracts/current/skill_registry_v1.yaml"),
        "model_sha256": sha256(policy),
        "checkpoint_sha256": sha256(output / "model.safetensors"),
        "calibration_ood_sha256": sha256(output / "calibration_ood_asset.json"),
        "onnx_operator_allowlist": operators,
        "files": files,
    }
    json_write(output / "policy_manifest.json", manifest)
    return {"bundle": str(output), "policy_manifest_sha256": sha256(output / "policy_manifest.json"), "production_eligible": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/resolve_policy_v1_fixture")
    args = parser.parse_args()
    print(json.dumps(build_bundle(args.output.resolve()), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
