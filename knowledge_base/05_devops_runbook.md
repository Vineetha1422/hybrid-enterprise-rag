---
document_id: DEVOPS-RUN-001
department: DevOps
owner: Aisha Patel
reviewer: James Okafor
last_updated: 2025-03-10
version: 1.6
related_tickets: [TECH-36, TECH-38, TECH-56, TECH-60, TECH-67]
related_products: [InsightDash, StreamAPI, DataLake Pro]
related_docs: [ENG-ARCH-001, OPS-INC-001]
---

# XYZ Analytics — DevOps Runbook

## Table of Contents

1. [Purpose & Scope](#purpose--scope)
2. [Team Structure & On-Call Rotation](#team-structure--on-call-rotation)
3. [Infrastructure Overview](#infrastructure-overview)
4. [Deployment Procedures](#deployment-procedures)
5. [Observability & Alerting](#observability--alerting)
6. [Common Runbook Procedures](#common-runbook-procedures)
7. [Kubernetes Operations](#kubernetes-operations)
8. [Database Operations](#database-operations)
9. [Kafka & Streaming Operations](#kafka--streaming-operations)
10. [Airflow & Pipeline Operations](#airflow--pipeline-operations)
11. [Disaster Recovery Procedures](#disaster-recovery-procedures)
12. [Security Operations](#security-operations)
13. [Runbook Change Process](#runbook-change-process)

---

## 1. Purpose & Scope

This Runbook is the authoritative operational reference for the XYZ Analytics DevOps team. It documents the procedures, commands, escalation paths, and standards required to operate, monitor, and recover all production infrastructure across InsightDash, StreamAPI, and DataLake Pro.

**Runbook Owner:** Aisha Patel, DevOps Lead
**Contributors:** Lucia Ferreira, Omar Shaikh, Raj Iyer, Hannah Brooks
**Engineering Liaison:** Daniel Cruz, VP of Engineering

This document is a living reference and must be kept current. Any procedure that is executed more than twice in production must be documented here. If a procedure is found to be incorrect or outdated, the engineer who discovers it is responsible for raising a PR to correct it before the end of their shift.

This runbook is a companion to the **Engineering Architecture Document (ENG-ARCH-001)**, which describes the system architecture this runbook operates, and the **Incident Management SOP (OPS-INC-001)**, which governs how incidents are declared, communicated, and resolved.

> ⚠️ **NEVER run any destructive command in production without a second engineer confirming in the `#devops-prod-ops` Slack channel. No exceptions.**

---

## 2. Team Structure & On-Call Rotation

### 2.1 Team Members & Primary Responsibilities

| Name             | Role                          | Primary Ownership                         |
|------------------|-------------------------------|-------------------------------------------|
| Aisha Patel      | DevOps Lead                   | Overall infrastructure, security ops, escalation |
| Lucia Ferreira   | Senior DevOps Engineer        | Observability stack, InsightDash infra    |
| Omar Shaikh      | DevOps Engineer               | Airflow, centralized logging (TECH-68)    |
| Raj Iyer         | Site Reliability Engineer     | SLO/SLA tracking, Snowflake network, multi-region |
| Hannah Brooks    | Cloud Infrastructure Engineer | Terraform, S3 lifecycle, CI/CD pipelines  |

### 2.2 On-Call Rotation

The DevOps team operates a **weekly on-call rotation** using PagerDuty. The rotation schedule is maintained by Aisha Patel and published in the `#devops-oncall` Slack channel every Friday for the following week.

**On-call expectations:**
- Primary on-call: Responds to all P1 and P2 PagerDuty alerts within **15 minutes**.
- Secondary on-call: Backs up primary; escalated to if primary is unresponsive after 10 minutes.
- Escalation path: Primary → Secondary → Aisha Patel → James Okafor (CTO).

**Handoff process:**
1. Outgoing on-call engineer posts a handoff summary to `#devops-oncall` by 09:00 on the rotation change day.
2. Summary must include: open incidents, any known fragile system states, recent deployments that may have ongoing risk, and any deferred follow-up items.
3. Incoming on-call acknowledges the handoff in-thread.

### 2.3 Escalation Contacts

| Situation                         | Primary Contact   | Escalation        |
|-----------------------------------|-------------------|-------------------|
| Production infrastructure failure | On-call DevOps    | Aisha Patel       |
| Data pipeline outage              | Omar Shaikh       | Laura Hensley     |
| StreamAPI broker instability      | Raj Iyer          | Daniel Cruz       |
| Security incident                 | Aisha Patel       | James Okafor      |
| Snowflake access issue            | Raj Iyer          | Mei Lin (Data)    |

---

## 3. Infrastructure Overview

All XYZ Analytics production infrastructure is deployed on **AWS** and managed as code via **Terraform**. State files are stored in S3 (`xyz-terraform-state`) with DynamoDB locking (migrated in TECH-58 by Hannah Brooks). Infrastructure changes are applied exclusively via the CI/CD pipeline — no manual `terraform apply` in production without a documented emergency exception approved by Aisha Patel.

### 3.1 Key Infrastructure Components

| Component           | Service              | Owner           | Region(s)          |
|---------------------|---------------------|-----------------|-------------------|
| EKS Clusters (x3)   | Amazon EKS           | Lucia Ferreira  | us-east-1          |
| Kafka Brokers       | Amazon MSK           | Raj Iyer        | us-east-1          |
| PostgreSQL (RDS)    | Amazon RDS Multi-AZ  | Lucia Ferreira  | us-east-1          |
| Snowflake Warehouse | Snowflake (AWS)      | Raj Iyer        | us-east-1, eu-west-1 |
| Airflow             | Amazon MWAA          | Omar Shaikh     | us-east-1          |
| Object Storage      | Amazon S3            | Hannah Brooks   | us-east-1, us-west-2 |
| CDN                 | Amazon CloudFront    | Hannah Brooks   | Global             |
| Observability       | Grafana + Prometheus | Lucia Ferreira  | us-east-1          |
| Log Aggregation     | OpenSearch (TECH-68) | Omar Shaikh     | us-east-1          |

### 3.2 Access & Credentials

All AWS credentials are managed via AWS SSO. Engineers access production accounts via the AWS SSO portal at `sso.xyzanalytics.com`. Direct IAM user credentials are not permitted in production — any discovered IAM user credentials must be reported to Aisha Patel and rotated immediately.

Snowflake credentials are managed via AWS Secrets Manager. Access the Snowflake production warehouse only via the approved Snowflake role hierarchy defined in TECH-59 (Lucia Ferreira). Network policies are IP-allowlisted — VPN connection is required before Snowflake access.

---

## 4. Deployment Procedures

### 4.1 Standard Deployment (All Products)

XYZ Analytics uses a **GitOps deployment model** via ArgoCD. All deployments are triggered by merging to the `main` branch of the relevant service repository after passing CI checks. Manual deployments are only permitted in documented emergency scenarios.

Standard deployment flow:
1. Engineer opens a PR targeting `main`.
2. CI pipeline runs: unit tests, integration tests, Snyk security scan, Docker image build.
3. PR requires two approvals (at least one from a senior engineer, per ENG-ARCH-001).
4. On merge, ArgoCD detects the change and syncs the updated image to the staging EKS cluster.
5. Staging smoke tests run automatically (15-minute window).
6. If smoke tests pass, ArgoCD promotes the deployment to production via a manual approval gate in the pipeline. This gate must be acknowledged by the on-call DevOps engineer or a named Engineering lead.
7. Post-deployment: on-call engineer monitors the Grafana deployment dashboard for 30 minutes before closing the change record.

### 4.2 Hotfix Deployments

For critical production fixes (P1 incidents), the abbreviated hotfix process is:

1. Create a hotfix branch from the last known-good production tag (not from `main`).
2. Apply the minimal necessary fix. Do not bundle unrelated changes.
3. CI must pass fully — no skipping tests for hotfixes.
4. One approval required (senior engineer or team lead).
5. DevOps on-call performs a manual ArgoCD sync to production after confirming staging looks healthy.
6. Notify `#incidents` and `#deployments` Slack channels with the hotfix details and expected impact.

### 4.3 Deployment Freeze Windows

The following periods are **deployment freeze windows** — no production deployments (including hotfixes, unless P1) are permitted without explicit VP Engineering (Daniel Cruz) approval:

- Last 5 business days of each quarter (financial close risk)
- 48 hours before and during All-Hands events
- Any period when the primary on-call is actively managing a P1 incident

Hannah Brooks maintains the deployment calendar in Notion, updated weekly.

### 4.4 Airflow DAG Deployments

DataLake Pro Airflow DAG deployments follow a separate CI/CD pipeline, automated per **TECH-56** (Omar Shaikh). The pipeline:

1. Lints DAG files with `pyflakes` and validates DAG structure with `airflow dags test`.
2. Deploys to the staging MWAA environment.
3. Runs a DAG trigger test to verify successful execution.
4. Promotes to production MWAA on manual approval from the Data Engineering team lead (Mei Lin or Nadia Kowalski).

---

## 5. Observability & Alerting

XYZ Analytics operates a unified observability stack (TECH-67, Lucia Ferreira) based on **Prometheus** (metrics), **Grafana** (dashboards and alerting), and **OpenSearch** (log aggregation, TECH-68).

### 5.1 Grafana Dashboards

Access Grafana at `grafana.internal.xyzanalytics.com` (VPN required). Key dashboards:

| Dashboard Name               | Owner           | Refresh Rate |
|------------------------------|-----------------|--------------|
| Infrastructure Overview      | Lucia Ferreira  | 30s          |
| InsightDash Application      | Lucia Ferreira  | 30s          |
| StreamAPI Broker & Consumers | Raj Iyer        | 10s          |
| DataLake Pro Pipeline Health | Omar Shaikh     | 1m           |
| Kafka Consumer Lag (TECH-21) | Raj Iyer        | 10s          |
| Snowflake Cost & Utilization | Raj Iyer        | 5m           |
| Deployment Tracking          | Hannah Brooks   | 1m           |

### 5.2 Alerting Rules

Prometheus alerting rules are defined in `/infra/alerts/` in the `xyz-infrastructure` repository. The following are the critical alert definitions — firing any of these triggers an immediate PagerDuty page to the on-call engineer:

**Critical Alerts (immediate PagerDuty page):**
- `KafkaConsumerLagCritical` — Consumer lag >50,000 messages on any topic for >5 minutes. Defined per TECH-38 (Raj Iyer).
- `EKSNodeNotReady` — Any EKS node in NotReady state for >3 minutes.
- `RDSConnectionsCritical` — RDS connection pool utilization >90% for >2 minutes.
- `StreamAPIWebsocketDropRate` — WebSocket drop rate >5% over 1-minute window.
- `SnowflakePipelineOverdue` — Any Tier 3/4 pipeline overdue by >2 hours (TECH-50).
- `AirflowTaskFailure` — Any Airflow task failure in a Tier 3/4 pipeline (routed to PagerDuty per TECH-60, Raj Iyer).

**Warning Alerts (Slack `#devops-alerts` channel):**
- `KafkaConsumerLagWarning` — Consumer lag >10,000 messages for >10 minutes.
- `EKSPodRestartHigh` — Any pod restarting >5 times in 10 minutes.
- `HighCPUUtilization` — Any node at >80% CPU for >15 minutes.
- `SnowflakeCostAnomaly` — Daily Snowflake spend >20% above 7-day rolling average.
- `CertificateExpiringSoon` — Any TLS certificate expiring within 14 days.

### 5.3 SLO Definitions

| Service         | SLO Metric            | Target   | Measurement Window |
|-----------------|-----------------------|----------|--------------------|
| InsightDash     | Availability          | 99.9%    | Rolling 30 days    |
| InsightDash     | P95 Dashboard Load    | <3s      | Rolling 7 days     |
| StreamAPI       | Availability          | 99.95%   | Rolling 30 days    |
| StreamAPI       | P99 Event Delivery    | <200ms   | Rolling 7 days     |
| DataLake Pro    | Pipeline SLA          | 99.5%    | Rolling 30 days    |
| DataLake Pro    | API Availability      | 99.9%    | Rolling 30 days    |

SLO burn rate alerts are configured in Grafana. When the error budget burn rate exceeds 5x for >1 hour, Raj Iyer is automatically paged.

---

## 6. Common Runbook Procedures

### 6.1 Restarting a Kubernetes Pod

Use this procedure when a pod is stuck in CrashLoopBackOff, OOMKilled, or Pending state and the issue cannot be resolved by waiting.

**Steps:**
1. Identify the affected pod: `kubectl get pods -n <namespace> | grep <service-name>`
2. Check pod logs for root cause before restarting: `kubectl logs <pod-name> -n <namespace> --previous`
3. Check pod events: `kubectl describe pod <pod-name> -n <namespace>`
4. If OOMKilled, check current memory limits before restarting: `kubectl get pod <pod-name> -n <namespace> -o json | jq '.spec.containers[].resources'`
5. Delete the pod to trigger a fresh start: `kubectl delete pod <pod-name> -n <namespace>`
6. Monitor the replacement pod coming up: `kubectl get pods -n <namespace> -w`
7. Confirm the service is healthy in Grafana before closing.
8. If the pod restarts more than 3 times within 15 minutes, escalate — do not continue restarting manually.

### 6.2 Scaling a Deployment Manually

Use only when HPA is insufficient or misconfigured (e.g., during a traffic spike before HPA catches up — see TECH-36 context, resolved by Lucia Ferreira).

1. Check current replica count: `kubectl get deployment <deployment-name> -n <namespace>`
2. Scale up: `kubectl scale deployment <deployment-name> --replicas=<N> -n <namespace>`
3. Monitor pod readiness: `kubectl rollout status deployment/<deployment-name> -n <namespace>`
4. Notify `#devops-prod-ops` with the scaling action, reason, and intended duration.
5. Revert to HPA-managed scaling once the event is resolved by removing the manual replica override.

### 6.3 Rolling Back a Deployment

1. Identify the last known-good revision: `kubectl rollout history deployment/<deployment-name> -n <namespace>`
2. Roll back to the previous revision: `kubectl rollout undo deployment/<deployment-name> -n <namespace>`
3. Or roll back to a specific revision: `kubectl rollout undo deployment/<deployment-name> --to-revision=<N> -n <namespace>`
4. Confirm rollback: `kubectl rollout status deployment/<deployment-name> -n <namespace>`
5. Post a rollback notification to `#deployments` and `#incidents` (if incident is active).
6. Notify the Engineering lead for the affected service.

### 6.4 Clearing a Stuck Airflow DAG Run

1. Navigate to the Airflow UI at `airflow.internal.xyzanalytics.com` (VPN required).
2. Locate the stuck DAG run in the DAG view.
3. In the Airflow UI, set the stuck task state to "Failed" to unblock downstream tasks.
4. If the entire DAG run is stuck: use the CLI — `airflow dags clear <dag_id> --start-date <YYYY-MM-DD> --yes`
5. Notify the Data Engineering on-call (Nadia Kowalski or Mei Lin) before clearing any Tier 3/4 DAG.
6. Document the clearance in the `#data-ops` Slack channel with the DAG name, run ID, and reason.

---

## 7. Kubernetes Operations

### 7.1 Cluster Access

```bash
# Authenticate to production EKS clusters
aws eks update-kubeconfig --name xyz-prod-insightdash --region us-east-1
aws eks update-kubeconfig --name xyz-prod-streamapi --region us-east-1
aws eks update-kubeconfig --name xyz-prod-datalakepro --region us-east-1
```

Production kubectl access requires an approved AWS SSO role with `eks:DescribeCluster` and the relevant RBAC binding. Engineers must not use the `cluster-admin` ClusterRole for day-to-day operations — use the `devops-operator` role.

### 7.2 Namespace Conventions

| Namespace          | Contents                              |
|--------------------|---------------------------------------|
| `insightdash-prod` | All InsightDash production services   |
| `streamapi-prod`   | StreamAPI broker, consumer gateway    |
| `datalakepro-prod` | DataLake Pro API and orchestration    |
| `platform-prod`    | Unified auth service, feature flags   |
| `monitoring`       | Prometheus, Grafana, AlertManager     |
| `logging`          | OpenSearch, Fluent Bit log forwarders |

### 7.3 HPA Configuration Standards

All production deployments must have an HPA configured with:
- `minReplicas: 2` (ensures HA — no single pod failure takes down a service)
- `maxReplicas:` set based on load testing results (documented per-service in the infra repository)
- Scaling trigger: CPU utilization at 70% OR memory utilization at 75%, whichever fires first

Review TECH-36 notes (Lucia Ferreira) for the StreamAPI broker HPA misconfiguration post-mortem and the corrected configuration values now in the infra repo.

---

## 8. Database Operations

### 8.1 RDS Connection & Queries

All RDS access in production requires VPN + AWS SSO. Use the `xyz-rds-readonly` role for investigative queries. Write access requires the `xyz-rds-readwrite` role, which requires a second engineer's approval in `#devops-prod-ops`.

```bash
# Connect via AWS Session Manager (no direct inbound 5432 on RDS)
aws ssm start-session --target <bastion-instance-id> \
  --document-name AWS-StartPortForwardingSessionToRemoteHost \
  --parameters '{"portNumber":["5432"],"localPortNumber":["5432"],"host":["<rds-endpoint>"]}'
```

### 8.2 RDS Snapshot & Restore

**Taking a manual snapshot:**
```bash
aws rds create-db-snapshot \
  --db-instance-identifier xyz-prod-insightdash \
  --db-snapshot-identifier manual-$(date +%Y%m%d-%H%M) \
  --region us-east-1
```

**Restoring from snapshot (DR/staging only — never to production without VP Engineering approval):**
1. Identify the target snapshot: `aws rds describe-db-snapshots --db-instance-identifier xyz-prod-insightdash`
2. Restore to a new instance (not the existing production instance): `aws rds restore-db-instance-from-db-snapshot ...`
3. Update application config to point to restored instance only after validating data integrity.
4. Notify James Okafor and Daniel Cruz before any production restore operation.

### 8.3 Snowflake Warehouse Sizing

Snowflake warehouse size adjustments must be reviewed against the cost optimization findings from TECH-41 (Mei Lin). Current production warehouse sizes are documented in the Snowflake governance runbook maintained by Raj Iyer. Sizing changes require:
1. A written justification referencing query performance data.
2. Approval from Laura Hensley (Head of Data) for XS→S or larger increases.
3. Implementation via Terraform (not manual Snowflake UI changes).

---

## 9. Kafka & Streaming Operations

### 9.1 Checking Consumer Lag

```bash
# Via AWS MSK CLI
aws kafka list-clusters --region us-east-1
kafka-consumer-groups.sh --bootstrap-server <broker-endpoint>:9092 \
  --describe --group <consumer-group-name>
```

Consumer lag thresholds and alerting are defined in TECH-38 (Raj Iyer). If lag is above the warning threshold, first check whether consumers are alive and processing before taking any action.

### 9.2 Restarting a Kafka Consumer Group

1. Identify the consumer group with elevated lag.
2. Check consumer pod health in the `streamapi-prod` namespace.
3. If pods are healthy but lag is growing, check for a schema mismatch or DLQ backlog (TECH-25).
4. To restart consumer pods gracefully: `kubectl rollout restart deployment/<consumer-deployment> -n streamapi-prod`
5. Monitor lag recovery in the Kafka Consumer Lag Grafana dashboard (10-second refresh).
6. If lag does not recover within 15 minutes after restart, escalate to Raj Iyer or Aisha Patel.

### 9.3 Backpressure Events

StreamAPI's backpressure mechanism (TECH-34, Fatima Al-Hassan) will throttle slow consumers automatically. If backpressure is observed in Grafana:
1. Identify the affected consumer group via the Consumer Lag dashboard.
2. Check if the consumer is experiencing high processing latency (database contention, downstream API slowness).
3. Do not disable backpressure — it exists to protect broker stability.
4. If the consumer cannot recover, coordinate with the relevant Engineering team lead to either scale consumers or reduce topic partition load.

---

## 10. Airflow & Pipeline Operations

### 10.1 Monitoring Pipeline Health

The DataLake Pro pipeline health dashboard in Grafana (Omar Shaikh) shows real-time DAG run status, task success rates, and latency vs. SLA. PagerDuty alerts for Airflow task failures in Tier 3/4 pipelines are configured per TECH-60 (Raj Iyer).

### 10.2 Investigating a Failed Pipeline

1. Navigate to the Airflow UI and locate the failed DAG run.
2. Click the failed task to view the task log.
3. Common failure causes and resolutions:
   - **Source connection timeout:** Check source system availability; retry the task from the Airflow UI.
   - **Great Expectations validation failure:** Data quarantined in `raw.quarantine` schema. Notify the Data Steward — do not retry without steward review.
   - **Snowflake permission error:** Check Snowflake role bindings via Raj Iyer. Likely a recently changed policy (TECH-59).
   - **S3 access denied:** Check S3 bucket policies and IAM role assignments. Hannah Brooks owns S3 lifecycle configs.
4. If the failure is in a Tier 3/4 pipeline and cannot be resolved within 30 minutes, trigger a P2 incident per **OPS-INC-001**.

### 10.3 Schema Registry Operations

Confluent-compatible schema registry operations (TECH-26) are deployed via the CI/CD pipeline maintained by Hannah Brooks (TECH-39). Manual schema registration is not permitted in production. All schema changes must go through PR review, with the schema change validated in staging before promotion.

---

## 11. Disaster Recovery Procedures

Full DR procedures are documented in the DR Playbook maintained by Aisha Patel. This section summarizes the activation criteria and initial response steps.

### 11.1 DR Activation Criteria

Initiate DR procedures when:
- A production AWS region (`us-east-1`) is experiencing a broad service disruption affecting 2+ infrastructure components.
- RTO or RPO thresholds are at risk of being breached (RTO: 4 hours, RPO: 1 hour for transactional stores).
- A security incident requires isolation of the production environment.

### 11.2 Initial DR Response Steps

1. Declare a P1 incident in PagerDuty and notify the `#incidents` channel.
2. Page Aisha Patel (DevOps Lead) and James Okafor (CTO) directly via PagerDuty.
3. Assess the scope: which products and which infrastructure components are affected?
4. Initiate read-only mode for affected products to prevent data corruption during the outage.
5. Begin failover procedure for the affected component per the relevant section of the DR Playbook.
6. Assign a dedicated communications owner to provide status updates every 30 minutes to the `#incidents` channel and the status page.

Cross-region S3 replication (us-east-1 → us-west-2) is active for all critical data buckets. Cross-region DataLake Pro dataset replication is pending (TECH-51, Nadia Kowalski).

---

## 12. Security Operations

Security-related operational procedures are detailed in **SEC-ACCESS-001**. Key operational touchpoints for the DevOps team:

- **mTLS enforcement (TECH-40):** Mutual TLS between all StreamAPI broker-to-consumer paths is being implemented by Lucia Ferreira. Until complete, ensure no broker-to-consumer traffic traverses public subnets.
- **Snowflake network policies (TECH-59):** IP allowlist policies enforced via Terraform. Any new IP requiring Snowflake access must be added via a Terraform PR, not via the Snowflake UI.
- **Certificate rotation:** TLS certificates are managed via AWS Certificate Manager with auto-renewal. Grafana alerts on certificates expiring within 14 days. Raj Iyer owns the certificate rotation runbook.
- **Security penetration test (TECH-72):** Scheduled for Q2 2025. Aisha Patel is coordinating with the external vendor. DevOps team is responsible for providing network topology and access for the testing period.

---

## 13. Runbook Change Process

All changes to this runbook must follow this process to ensure accuracy and peer validation:

1. Engineer identifies a missing, incorrect, or outdated procedure.
2. A PR is opened against the `xyz-knowledge-base` repository targeting the `devops/DEVOPS-RUN-001.md` file.
3. PR requires review and approval from at least one other DevOps team member.
4. For significant structural changes (new sections, deprecated procedures), Aisha Patel must review.
5. On merge, the `last_updated` metadata field and version number must be bumped.
6. The change is announced in `#devops-team` Slack channel with a brief summary.

---

## 14. Revision History

| Version | Date       | Author          | Summary                                              |
|---------|------------|-----------------|------------------------------------------------------|
| 1.0     | 2023-05-01 | Aisha Patel     | Initial runbook                                      |
| 1.2     | 2023-11-14 | Raj Iyer        | Added Snowflake and Kafka sections                   |
| 1.3     | 2024-03-08 | Hannah Brooks   | Terraform state migration (TECH-58) procedures       |
| 1.4     | 2024-07-22 | Omar Shaikh     | Airflow DAG deployment and pipeline ops added        |
| 1.5     | 2024-12-01 | Lucia Ferreira  | Observability stack, HPA standards, SLO definitions  |
| 1.6     | 2025-03-10 | Aisha Patel     | TECH-60 PagerDuty integration, DR activation updated |
