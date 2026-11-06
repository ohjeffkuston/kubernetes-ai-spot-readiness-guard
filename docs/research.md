# Demand and technical validation

Checked 2026-11-06.

## Authoritative sources

- [Kubernetes disruptions](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/) explains voluntary/involuntary disruption and PodDisruptionBudgets.
- [Kubernetes pod termination](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-termination) defines graceful termination behavior.
- [Kubernetes topology spread constraints](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/) documents zone and node distribution.
- [AWS EC2 Spot interruption notices](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-instance-termination-notices.html) states that warnings are best effort and normally arrive two minutes before interruption.
- [Karpenter disruption](https://karpenter.sh/docs/concepts/disruption/) documents taint, pre-spin, drain, eviction, PDB, and termination flow.

## Live-job demand signal

Multiple current remote U.S. AI/platform postings reviewed during this portfolio series combine Kubernetes, Terraform/IaC, GPU or inference infrastructure, observability, production reliability, and cost efficiency. Examples included Deepgram's AI/ML platform scope, MOXFIVE's AI inference/platform reliability scope, and Runpod/Runway infrastructure-security roles. These were demand evidence only; they were separately screened for resume fit and sponsorship.

## Rationale

Interruptible accelerators are a credible FinOps lever, but safe adoption requires SRE controls. The project therefore combines Kubernetes, GitOps policy, AI workload operations, reliability, and cost engineering rather than demonstrating a generic model call.
