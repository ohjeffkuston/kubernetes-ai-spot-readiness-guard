# Safe deployment guidance

1. Run the CLI in pull requests before GitOps reconciliation.
2. Start in report-only mode and measure false positives.
3. Make BLOCK fail CI only after policy owners approve thresholds.
4. Require human review for exceptions; record owner, reason, and expiry.
5. Test checkpoint restore and traffic drain with controlled interruption game days.
6. Monitor interruption notice delivery, checkpoint freshness, replacement latency, quota, and recovery time.
7. Keep on-demand fallback bounded by budgets and quota alerts.

The tool does not deploy nodes or workloads. Infrastructure-impacting actions remain behind human approval. In production, pin dependencies and container images, sign the release, restrict CI permissions, and export only non-sensitive metrics.
