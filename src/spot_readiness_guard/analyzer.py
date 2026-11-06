"""Policy engine for interruptible Kubernetes AI workloads."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

WORKLOAD_KINDS = {"Deployment", "StatefulSet", "Job"}


def load_documents(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open(encoding="utf-8") as handle:
        return [doc for doc in yaml.safe_load_all(handle) if isinstance(doc, dict)]


def _finding(rule: str, severity: str, passed: bool, message: str) -> dict[str, Any]:
    return {"rule": rule, "severity": severity, "passed": passed, "message": message}


def _labels_match(selector: dict[str, Any], labels: dict[str, Any]) -> bool:
    expected = selector.get("matchLabels", {})
    return bool(expected) and all(labels.get(key) == value for key, value in expected.items())


def analyze_documents(documents: list[dict[str, Any]], minimum_grace: int = 120) -> dict[str, Any]:
    pdbs = [doc for doc in documents if doc.get("kind") == "PodDisruptionBudget"]
    workloads = [doc for doc in documents if doc.get("kind") in WORKLOAD_KINDS]
    results: list[dict[str, Any]] = []

    for workload in workloads:
        metadata = workload.get("metadata", {})
        spec = workload.get("spec", {})
        template = spec.get("template", {})
        pod_meta = template.get("metadata", {})
        labels = {**metadata.get("labels", {}), **pod_meta.get("labels", {})}
        annotations = {**metadata.get("annotations", {}), **pod_meta.get("annotations", {})}
        if labels.get("platform.example.com/capacity-class") != "interruptible":
            continue

        pod_spec = template.get("spec", {})
        containers = pod_spec.get("containers", [])
        workload_class = labels.get("platform.example.com/workload-class", "unknown")
        findings: list[dict[str, Any]] = []

        checkpoint_ok = workload_class != "ai-training" or (
            str(annotations.get("platform.example.com/checkpoint-uri", "")).startswith(("s3://", "gs://", "az://"))
            and int(annotations.get("platform.example.com/checkpoint-interval-seconds", 0) or 0) <= 90
            and int(annotations.get("platform.example.com/checkpoint-interval-seconds", 0) or 0) > 0
        )
        findings.append(_finding("durable-checkpoint", "block", checkpoint_ok, "Training state is checkpointed to durable object storage at least every 90 seconds."))

        grace = int(pod_spec.get("terminationGracePeriodSeconds", 30) or 0)
        findings.append(_finding("termination-grace", "block", grace >= minimum_grace, f"Termination grace is {grace}s; policy requires at least {minimum_grace}s."))
        prestop = bool(containers) and all(container.get("lifecycle", {}).get("preStop") for container in containers)
        findings.append(_finding("prestop-hook", "block", prestop, "Every container has a preStop hook for checkpointing or traffic drain."))
        readiness = bool(containers) and all(container.get("readinessProbe") for container in containers)
        findings.append(_finding("readiness-probe", "review", readiness, "Every container exposes a readiness probe."))

        pdb_ok = workload.get("kind") == "Job" or any(
            _labels_match(pdb.get("spec", {}).get("selector", {}), labels)
            and (pdb.get("spec", {}).get("minAvailable") is not None or pdb.get("spec", {}).get("maxUnavailable") is not None)
            for pdb in pdbs
        )
        findings.append(_finding("disruption-budget", "block", pdb_ok, "A matching PodDisruptionBudget controls voluntary disruption."))

        topologies = {item.get("topologyKey") for item in pod_spec.get("topologySpreadConstraints", [])}
        spread_ok = {"topology.kubernetes.io/zone", "kubernetes.io/hostname"}.issubset(topologies)
        findings.append(_finding("topology-spread", "review", spread_ok, "Pods are spread across zones and hosts."))

        required = pod_spec.get("affinity", {}).get("nodeAffinity", {}).get("requiredDuringSchedulingIgnoredDuringExecution", {})
        required_text = str(required).lower()
        hard_spot_only = "spot" in required_text or "interruptible" in required_text
        fallback_ok = annotations.get("platform.example.com/on-demand-fallback") == "enabled" and not hard_spot_only
        findings.append(_finding("on-demand-fallback", "block", fallback_ok, "On-demand fallback is enabled and scheduling is not hard-pinned to interruptible capacity."))

        notice_ok = annotations.get("platform.example.com/interruption-handler") in {"aws-node-termination-handler", "karpenter"}
        findings.append(_finding("interruption-handler", "review", notice_ok, "An interruption handler is declared."))

        replicas = int(spec.get("replicas", 1) or 1)
        replica_ok = workload_class != "ai-inference" or replicas >= 2
        findings.append(_finding("inference-redundancy", "block", replica_ok, "Inference deployments keep at least two replicas."))

        failed_block = sum(1 for item in findings if not item["passed"] and item["severity"] == "block")
        failed_review = sum(1 for item in findings if not item["passed"] and item["severity"] == "review")
        decision = "BLOCK" if failed_block else ("REVIEW" if failed_review else "PASS")
        score = round(100 * sum(1 for item in findings if item["passed"]) / len(findings))
        results.append({"name": metadata.get("name", "unnamed"), "kind": workload.get("kind"), "decision": decision, "score": score, "findings": findings})

    counts = {decision: sum(1 for result in results if result["decision"] == decision) for decision in ("PASS", "REVIEW", "BLOCK")}
    return {"workloads": results, "counts": counts, "overall_decision": "BLOCK" if counts["BLOCK"] else ("REVIEW" if counts["REVIEW"] else "PASS")}
