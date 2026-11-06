from __future__ import annotations

import argparse
import json

from .analyzer import analyze_documents, load_documents


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Kubernetes AI workloads for spot interruption readiness")
    parser.add_argument("manifest")
    parser.add_argument("--minimum-grace", type=int, default=120)
    args = parser.parse_args()
    report = analyze_documents(load_documents(args.manifest), args.minimum_grace)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["overall_decision"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
