from copy import deepcopy

import yaml

from spot_readiness_guard.analyzer import analyze_documents


def docs():
    with open("samples/compliant-workload.yaml", encoding="utf-8") as handle:
        return list(yaml.safe_load_all(handle))


def workload(items):
    return next(item for item in items if item.get("kind") == "Deployment")


def test_compliant_manifest_passes():
    report = analyze_documents(docs())
    assert report["overall_decision"] == "PASS"
    assert report["workloads"][0]["score"] == 100


def test_non_interruptible_workload_is_ignored():
    items = docs()
    workload(items)["spec"]["template"]["metadata"]["labels"]["platform.example.com/capacity-class"] = "on-demand"
    assert analyze_documents(items)["workloads"] == []


def mutate(path, value):
    items = deepcopy(docs())
    obj = workload(items)
    current = obj
    for key in path[:-1]:
        current = current[key]
    current[path[-1]] = value
    return items


def test_short_grace_blocks():
    assert analyze_documents(mutate(["spec", "template", "spec", "terminationGracePeriodSeconds"], 30))["overall_decision"] == "BLOCK"


def test_missing_prestop_blocks():
    items = docs(); del workload(items)["spec"]["template"]["spec"]["containers"][0]["lifecycle"]
    assert analyze_documents(items)["overall_decision"] == "BLOCK"


def test_missing_readiness_requires_review():
    items = docs(); del workload(items)["spec"]["template"]["spec"]["containers"][0]["readinessProbe"]
    assert analyze_documents(items)["overall_decision"] == "REVIEW"


def test_missing_pdb_blocks():
    items = [item for item in docs() if item.get("kind") != "PodDisruptionBudget"]
    assert analyze_documents(items)["overall_decision"] == "BLOCK"


def test_missing_host_spread_requires_review():
    items = docs(); workload(items)["spec"]["template"]["spec"]["topologySpreadConstraints"].pop()
    assert analyze_documents(items)["overall_decision"] == "REVIEW"


def test_hard_spot_affinity_blocks_fallback():
    items = docs(); workload(items)["spec"]["template"]["spec"]["affinity"] = {"nodeAffinity": {"requiredDuringSchedulingIgnoredDuringExecution": {"nodeSelectorTerms": [{"matchExpressions": [{"key": "capacity", "operator": "In", "values": ["spot"]}]}]}}}
    assert analyze_documents(items)["overall_decision"] == "BLOCK"


def test_missing_handler_requires_review():
    items = docs(); del workload(items)["spec"]["template"]["metadata"]["annotations"]["platform.example.com/interruption-handler"]
    assert analyze_documents(items)["overall_decision"] == "REVIEW"


def test_single_inference_replica_blocks():
    assert analyze_documents(mutate(["spec", "replicas"], 1))["overall_decision"] == "BLOCK"


def test_training_without_checkpoint_blocks():
    items = docs(); meta = workload(items)["spec"]["template"]["metadata"]; meta["labels"]["platform.example.com/workload-class"] = "ai-training"; meta["annotations"].pop("platform.example.com/checkpoint-uri")
    assert analyze_documents(items)["overall_decision"] == "BLOCK"


def test_training_with_durable_checkpoint_passes():
    items = docs(); workload(items)["spec"]["template"]["metadata"]["labels"]["platform.example.com/workload-class"] = "ai-training"
    assert analyze_documents(items)["overall_decision"] == "PASS"
