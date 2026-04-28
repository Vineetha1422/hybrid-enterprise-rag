---
document_id: PROD-METRICS-001
department: Product
owner: Priya Nair
reviewer: Laura Hensley
last_updated: 2025-03-01
version: 1.3
related_tickets: [TECH-16, TECH-19, TECH-47, TECH-50, TECH-55]
related_products: [InsightDash, StreamAPI, DataLake Pro]
related_docs: [PROD-ROAD-001, DATA-GOV-001, ENG-ARCH-001]
---

# XYZ Analytics — Analytics Metrics Definition Guide

## Table of Contents

1. [Purpose & Scope](#purpose--scope)
2. [Metrics Governance](#metrics-governance)
3. [Metric Taxonomy](#metric-taxonomy)
4. [InsightDash Metrics](#insightdash-metrics)
5. [StreamAPI Metrics](#streamapi-metrics)
6. [DataLake Pro Metrics](#datalake-pro-metrics)
7. [Cross-Product & Business Metrics](#cross-product--business-metrics)
8. [Engineering & Reliability Metrics](#engineering--reliability-metrics)
9. [Data Lineage & Pipeline Metrics](#data-lineage--pipeline-metrics)
10. [Metric Implementation Standards](#metric-implementation-standards)
11. [Glossary](#glossary)

---

## 1. Purpose & Scope

This Metrics Definition Guide is the single source of truth for how XYZ Analytics defines, calculates, and governs every metric surfaced in InsightDash, reported to customers, used in internal OKR tracking, or referenced in investor or board communications.

**Guide Owner:** Priya Nair, VP of Product
**Technical Owner:** Mei Lin, Senior Data Engineer
**Data Quality Owner:** Samuel Osei, Data Scientist
**Reviewer:** Laura Hensley, Head of Data

Metrics are a shared language. When the Product team says "Monthly Active Users" and the Data team calculates "Monthly Active Users" differently, the resulting confusion undermines trust in data and leads to poor decisions. This guide prevents that by establishing unambiguous definitions that every team works from.

This document is a companion to the **Product Roadmap (PROD-ROAD-001)**, which references these metrics as OKR targets. The data pipelines that produce these metrics are governed by **DATA-GOV-001** and implemented per the standards described in **ENG-ARCH-001**. Metric calculation logic is implemented via the semantic layer described in TECH-16 (Mei Lin) and surfaced via dbt model integration in TECH-19.

All metrics in this guide are versioned. When a metric definition changes, the prior definition is preserved in the revision history and the new definition is tagged with an effective date. Historical data is not retroactively recalculated unless explicitly noted.

---

## 2. Metrics Governance

### 2.1 Metric Ownership

Every metric in XYZ Analytics has three designated owners:

- **Business Owner:** The Product Manager or business stakeholder responsible for defining what the metric should measure and how it informs decisions. Approves definition changes.
- **Data Owner:** The Data Engineer or Scientist responsible for implementing the calculation in the semantic layer and ensuring data quality. Currently distributed across Mei Lin, Samuel Osei, Simone Dupont, and Carlos Vega.
- **Consumer:** The team or individual that primarily uses the metric for decision-making. Consulted on definition changes.

### 2.2 Metric Change Process

Changing a metric definition — even a minor clarification — has downstream consequences for dashboards, OKR tracking, and customer-facing reports. All changes follow this process:

1. Business Owner documents the proposed change and rationale in a Metrics Change Request (MCR), submitted to Priya Nair.
2. Data Owner assesses the implementation impact: which dbt models, pipelines, and dashboards are affected.
3. If the change alters historical comparability, a backfill plan must be included.
4. Changes affecting customer-facing metrics (e.g., metrics included in customer usage reports) require review by Laura Hensley and Priya Nair.
5. Approved changes are logged in the Metric Changelog (Section 11.3 of this document) with an effective date.
6. InsightDash dashboards displaying the metric are updated by Zoe Hartman (Product Design) to reflect any definition change with a visible note for users.

### 2.3 Metric Quality Standards

All metrics must meet the following quality standards, validated as part of the Great Expectations pipeline (TECH-47, Samuel Osei):

- **Completeness:** The metric must have a value for every defined time period. Null values are not acceptable in reported metrics — missing data must be explicitly modeled (e.g., `0` for activity metrics, `NULL` with a documented reason for ratio metrics with no denominator).
- **Timeliness:** Business metrics must refresh within 4 hours of the end of the reporting period. Real-time operational metrics (StreamAPI event delivery) must reflect data within 60 seconds. SLA breach alerts per TECH-50 (Simone Dupont) enforce this.
- **Accuracy:** Metrics are validated against expected ranges and statistical baselines. Anomalies outside 3 standard deviations from the 30-day rolling mean trigger a data quality alert and suppress the metric from customer-facing dashboards until reviewed.
- **Consistency:** The same metric must return the same value whether queried from InsightDash, the DataLake Pro API, or directly from Snowflake (subject to cache refresh timing).

---

## 3. Metric Taxonomy

XYZ Analytics organizes metrics into the following categories:

**Product Metrics** — Measure user behavior, engagement, and adoption within each product. Subdivided into Acquisition, Activation, Retention, Expansion, and Referral (AARRR framework).

**Operational Metrics** — Measure the technical performance, reliability, and health of each product's infrastructure. Used by Engineering and DevOps. Directly correspond to SLO targets.

**Business Metrics** — Aggregate across products to measure XYZ Analytics' overall health: revenue, churn, Net Revenue Retention (NRR), and customer count.

**Pipeline Metrics** — Measure the health, latency, and quality of DataLake Pro's data ingestion and transformation pipelines. Used primarily by the Data team.

**Leading Indicators** — Metrics that have been shown (through internal data analysis) to predict future outcomes such as expansion or churn. These are tracked closely by the Product team and Customer Success.

---

## 4. InsightDash Metrics

### 4.1 Engagement Metrics

#### Monthly Active Dashboards (MAD)

**Definition:** The count of distinct dashboard IDs that had at least one "view" event recorded in the InsightDash event log within a rolling 28-day window, where a "view" event is defined as a user loading a dashboard that rendered at least one widget with data.

**What it is not:** MAD does not count dashboards that were opened but failed to load (render errors), dashboards that were auto-refreshed by a scheduled job (no human-initiated session), or duplicate views within the same user session (within 30 seconds of the prior view event).

**Calculation:**
```sql
SELECT
  DATE_TRUNC('month', event_date) AS month,
  COUNT(DISTINCT dashboard_id) AS monthly_active_dashboards
FROM insightdash.events.dashboard_views
WHERE
  event_type = 'dashboard_view'
  AND render_success = TRUE
  AND session_type = 'human'
  AND event_date >= DATEADD('day', -28, CURRENT_DATE())
GROUP BY 1
```

**Owner:** Ingrid Svensson (Business), Mei Lin (Data)
**Refresh cadence:** Daily, as of 06:00 UTC
**2025 OKR Target:** 40% YoY growth

#### Dashboard P95 Load Time

**Definition:** The 95th percentile of dashboard total render time, measured from the timestamp of the first API request to the `dashboard-service` to the timestamp when the last widget in the dashboard fires a `widget_render_complete` event in the client. Measured in milliseconds.

**Exclusions:** Dashboards in embedded mode (Embed API, TECH-05) are tracked separately as "Embed P95 Load Time" and are not included in this metric. Dashboards loaded during scheduled export jobs are excluded.

**Data source:** InsightDash frontend performance events, shipped to the events pipeline via the StreamAPI real-time ingestion path and landed in DataLake Pro.

**Owner:** Ingrid Svensson (Business), Arjun Mehta (Engineering), Mei Lin (Data)
**Refresh cadence:** Real-time (60-second lag via StreamAPI → DataLake Pro pipeline)
**2025 OKR Target:** P95 ≤ 3,000ms
**Alert threshold:** P95 > 5,000ms sustained 10+ minutes triggers PagerDuty P2

#### Daily Active Users (DAU) — InsightDash

**Definition:** Count of distinct `user_id` values that initiated at least one human session in InsightDash within a calendar day (UTC). A session is initiated when a user loads the InsightDash application with a valid authentication token.

**Note on user identity:** `user_id` maps to the authenticated user in the InsightDash auth system. For SSO users (Okta, TECH-10), the `user_id` is the Okta subject identifier. For non-SSO users, it is the InsightDash-native user UUID. These are unified via the identity resolution table maintained by Mei Lin.

**Owner:** Ingrid Svensson (Business), Samuel Osei (Data)
**Refresh cadence:** Daily
**Derived metrics:** DAU/MAU ratio (stickiness), DAU 7-day rolling average

#### Dashboard Share Rate

**Definition:** The percentage of dashboards created in a given month that had at least one "share" event (any permission level: viewer or editor) within 30 days of creation.

**Formula:** `(dashboards_with_share_event / dashboards_created) × 100`

**Owner:** Ben Adeyemi (Business), Carlos Vega (Data)
**Refresh cadence:** Monthly
**Strategic use:** A leading indicator for team adoption and virality within accounts.

### 4.2 Retention Metrics

#### InsightDash Monthly Retention Rate

**Definition:** For a cohort of users who were active in month M, the percentage who were also active in month M+1. "Active" is defined using the DAU definition above (at least one human session).

**Formula:** `(users_active_in_M_and_M+1 / users_active_in_M) × 100`

**Cohort granularity:** This metric is tracked at both the user level and the account (company) level. Account-level retention is the primary business health indicator. User-level retention informs product engagement depth.

**Owner:** Priya Nair (Business), Simone Dupont (Data)
**Refresh cadence:** Monthly (published on the 3rd business day of each month)

#### Feature Adoption Rate

**Definition:** For a given feature, the percentage of InsightDash accounts (paying customers with ≥1 active user) that used the feature at least once in a given calendar month.

**Feature adoption is tracked separately for:**
- Drill-down filters (TECH-02)
- Embed API (TECH-05)
- Alert thresholds (TECH-12)
- Dashboard sharing (TECH-04)
- SSO-authenticated sessions (TECH-10)

**Owner:** Ingrid Svensson or Ben Adeyemi per feature (Business), Samuel Osei (Data)
**Refresh cadence:** Monthly

---

## 5. StreamAPI Metrics

### 5.1 Developer Activation Metrics

#### Time to First Event (TTFE)

**Definition:** The elapsed time in minutes from an account's first successful API key creation to that account's first successful event received via any StreamAPI subscription (WebSocket, REST, or webhook). Measured per account cohort.

**Why this matters:** TTFE is the primary activation metric for StreamAPI. A low TTFE indicates that the developer onboarding experience (documentation, SDK, sandbox — TECH-64 initiative) is effective. It is the #1 metric Ben Adeyemi tracks for the StreamAPI developer portal revamp.

**Formula:** `TIMESTAMPDIFF('minute', first_api_key_created_at, first_event_received_at)`

**Exclusions:** Test events generated via the sandbox environment do not count as "first event received" — the metric requires a production event delivery.

**Owner:** Ben Adeyemi (Business), Carlos Vega (Data)
**Refresh cadence:** Daily (7-day and 30-day rolling averages reported)
**2025 OKR Target:** TTFE ≤ 15 minutes (median for new accounts)

#### SDK Adoption Rate

**Definition:** The percentage of active StreamAPI accounts (at least one event delivered in the past 30 days) whose API calls originate from a recognized XYZ Analytics SDK user agent string (Python SDK, Go SDK — TECH-73), as opposed to raw HTTP calls.

**Owner:** Ben Adeyemi (Business), Carlos Vega (Data)
**Refresh cadence:** Monthly
**Strategic use:** Tracks the impact of the SDK publishing initiative. Higher SDK adoption correlates with lower support ticket volume and higher retention.

### 5.2 Operational Metrics

#### P99 Event Delivery Latency

**Definition:** The 99th percentile of end-to-end event delivery latency for WebSocket subscribers. Latency is measured from the timestamp of the event being committed to the Kafka topic by the producer to the timestamp of the acknowledgement sent by the subscriber client.

**Measurement:** Instrumented at the `consumer-gateway` service and shipped to Prometheus. Visualized in the StreamAPI Grafana dashboard (Raj Iyer).

**Exclusions:** Events delivered via the Replay API (TECH-29) are excluded — replay latency is tracked separately. Events routed to the Dead Letter Queue (TECH-25) are excluded from the primary latency metric and tracked under "DLQ rate."

**Owner:** Ben Adeyemi (Business), Raj Iyer (Engineering/DevOps)
**Refresh cadence:** Real-time (10-second Grafana refresh)
**2025 OKR Target:** P99 ≤ 200ms
**Incident trigger:** P99 > 2,000ms sustained >5 minutes → P1 incident (OPS-INC-001)

#### Events Delivered per Day

**Definition:** Total count of events successfully delivered (ACKed by subscriber) across all topics and all delivery methods (WebSocket, webhook, REST polling) in a calendar day (UTC).

**Owner:** Ben Adeyemi (Business), Mei Lin (Data)
**Refresh cadence:** Daily
**Strategic use:** Volume growth metric used in investor reporting and capacity planning.

#### Dead Letter Queue (DLQ) Rate

**Definition:** The percentage of attempted event deliveries in a given hour that were routed to the Dead Letter Queue (TECH-25) due to delivery failure (subscriber unreachable, schema validation failure, or max retry exceeded).

**Formula:** `(events_routed_to_dlq / total_delivery_attempts) × 100`

**Alert threshold:** DLQ rate > 1% sustained for >15 minutes triggers a P2 incident.

**Owner:** Ben Adeyemi (Business), Ryan Park (Engineering)
**Refresh cadence:** Hourly

---

## 6. DataLake Pro Metrics

### 6.1 Customer Metrics

#### Pipeline SLA Adherence Rate

**Definition:** The percentage of scheduled DataLake Pro ingestion pipeline runs that completed successfully and delivered data to the curated layer within the customer-contracted SLA window. The standard SLA window is 2 hours from the scheduled run time unless a customer contract specifies otherwise.

**Formula:** `(pipeline_runs_within_SLA / total_scheduled_pipeline_runs) × 100`

**Exclusions:** Runs that failed due to a documented source-system outage (external to XYZ Analytics) are classified as "excused failures" and excluded from the denominator. Excused failure classification requires approval from the relevant Data Steward (Nadia Kowalski or Mei Lin) and is logged in the pipeline audit trail.

**Alert integration:** SLA breaches trigger PagerDuty per TECH-50 (Simone Dupont). The pipeline health dashboard (TECH-55, Samuel Osei) displays real-time adherence.

**Owner:** Priya Nair (Business), Simone Dupont (Data)
**Refresh cadence:** Real-time (per pipeline run)
**2025 OKR Target:** ≥ 99.5%

#### Data Freshness Score

**Definition:** For a given customer's curated dataset, the percentage of tables whose most recent data timestamp is within the expected freshness window (as defined in the customer's pipeline configuration). Expressed as a percentage per customer account.

**Why this matters:** This is a leading indicator for customer satisfaction and renewal risk. Accounts with consistently low freshness scores are significantly more likely to churn.

**Owner:** Ingrid Svensson (Business), Samuel Osei (Data)
**Refresh cadence:** Hourly
**Customer-facing:** Yes — surfaced in the DataLake Pro customer dashboard.

#### Connector Success Rate

**Definition:** Per ingestion connector type (Salesforce, PostgreSQL, S3, etc.), the percentage of sync attempts that completed without error in a rolling 7-day window.

**Owner:** Carlos Vega (Business/Data), Nadia Kowalski (Data Engineering)
**Refresh cadence:** Daily

### 6.2 Data Quality Metrics

#### Great Expectations Pass Rate

**Definition:** The percentage of individual Great Expectations validation checks (expectations) that passed across all pipeline runs in a given day. Tracked at the suite level (per pipeline) and at the individual expectation level.

**Implementation:** Tracked via the Great Expectations results store in S3, aggregated by Samuel Osei's dbt model. Integrated into the pipeline health dashboard (TECH-55).

**Owner:** Samuel Osei (Data), Laura Hensley (Business)
**Refresh cadence:** Daily
**Alert threshold:** Suite-level pass rate < 95% in any Tier 3/4 pipeline triggers a P2 alert to the Data on-call.

#### Data Quarantine Rate

**Definition:** The percentage of daily pipeline runs that resulted in data being quarantined in the `raw.quarantine` schema due to quality validation failure.

**Formula:** `(pipeline_runs_with_quarantine / total_pipeline_runs) × 100`

**Owner:** Nadia Kowalski (Data)
**Refresh cadence:** Daily
**Use:** Tracks the effectiveness of upstream data quality improvements at source systems.

---

## 7. Cross-Product & Business Metrics

### 7.1 Revenue Metrics

#### Monthly Recurring Revenue (MRR)

**Definition:** The sum of the normalized monthly contract value of all active, paying customer subscriptions as of the last day of the reporting month. "Active" means the subscription is within its contracted term and has not been formally cancelled or suspended.

**Normalization rule:** Annual contracts are divided by 12. Multi-year contracts are divided by the total contracted months. Month-to-month contracts are counted as-is. One-time professional services fees are excluded from MRR.

**Owner:** Sarah Mitchell (Business), Simone Dupont (Data)
**Refresh cadence:** Monthly (published on the 1st business day of each month)
**Classification:** Tier 3 — Confidential. Not accessible to individual contributors outside Finance and Executive team without VP approval.

#### Net Revenue Retention (NRR)

**Definition:** The percentage of MRR retained from a cohort of customers 12 months later, including expansions (upgrades, additional seats, new products added) and reductions (downgrades, seat reductions, churned accounts).

**Formula:**
```
NRR = (MRR at end of period from customers present at start of period) /
      (MRR at start of period from same customers) × 100
```

**An NRR > 100% means expansion revenue from existing customers exceeds churn and contraction.**

**Owner:** Priya Nair (Business), Simone Dupont (Data)
**Refresh cadence:** Monthly
**2025 target:** NRR ≥ 115% (not disclosed externally)

### 7.2 Customer Health Score

**Definition:** A composite score (0–100) calculated per customer account, weighted across the following signals:

| Signal                         | Weight | Source Metric                        |
|-------------------------------|--------|--------------------------------------|
| Product engagement (primary)  | 30%    | DAU/MAU or TTFE (product-specific)   |
| Feature adoption breadth      | 20%    | Feature Adoption Rate                |
| Pipeline SLA adherence        | 20%    | Pipeline SLA Adherence Rate          |
| Support ticket volume         | 15%    | Inverse of support ticket count      |
| Data freshness score          | 15%    | Data Freshness Score                 |

**Score bands:**
- 80–100: Healthy (green)
- 60–79: At Risk (yellow) — triggers Customer Success outreach
- 0–59: Critical (red) — triggers escalation to account Executive

**Owner:** Priya Nair (Business), Simone Dupont (Data)
**Refresh cadence:** Weekly (Sundays, 06:00 UTC)
**Planned availability:** Q3 2025, dependent on cross-product usage pipeline (TECH-70)

---

## 8. Engineering & Reliability Metrics

### 8.1 SLO Compliance

**Definition:** For each product SLO defined in DEVOPS-RUN-001 Section 5.3, the percentage of time within the measurement window (rolling 30 days) during which the SLO target was met.

**Metric names:**
- `insightdash.availability.slo_compliance` — target 99.9%
- `insightdash.p95_load_time.slo_compliance` — target P95 ≤ 3s
- `streamapi.availability.slo_compliance` — target 99.95%
- `streamapi.p99_latency.slo_compliance` — target P99 ≤ 200ms
- `datalakepro.pipeline_sla.slo_compliance` — target 99.5%

**Owner:** Raj Iyer (Engineering/DevOps)
**Refresh cadence:** Real-time (Prometheus)

### 8.2 Error Budget

**Definition:** For each SLO, the error budget is the maximum allowable downtime or degradation within the measurement window. Expressed as a percentage and as absolute time/count.

**Formula:** `Error Budget = (1 - SLO target) × measurement window`

**Example:** StreamAPI availability SLO target is 99.95% over 30 days. Error budget = 0.05% × 30 days × 24 hours = 21.6 minutes per month.

**Error budget burn rate** is tracked in Grafana (Lucia Ferreira). A burn rate of >5x for >1 hour triggers a PagerDuty alert for the relevant SRE on-call.

**Owner:** Raj Iyer (Engineering/DevOps), Aisha Patel (oversight)

---

## 9. Data Lineage & Pipeline Metrics

These metrics support the DataLake Pro operations team (Laura Hensley, Mei Lin, Nadia Kowalski) and are surfaced in the pipeline health dashboard (TECH-55, Samuel Osei).

### Pipeline Run Duration (P95)

**Definition:** The 95th percentile of wall-clock runtime for a given pipeline DAG, calculated over the most recent 30 executions. Measured per DAG ID.

**Use:** Identifying pipelines with increasing runtime trends that may breach SLAs before they actually do. A >20% increase in P95 runtime week-over-week triggers a Data Engineering review.

### Data Volume Processed

**Definition:** Total bytes ingested from source systems and written to the DataLake Pro raw layer in a calendar day, per connector type.

**Use:** Capacity planning, cost attribution (Snowflake cost optimization context from TECH-41), and identifying unexpected volume spikes that may indicate source system issues.

### Ingestion Lag

**Definition:** The elapsed time between the most recent record timestamp in the source system and the most recent record timestamp in the DataLake Pro curated layer for a given connector, at the time of measurement. Expressed in minutes.

**Distinct from Pipeline SLA Adherence Rate:** SLA adherence is a binary pass/fail per run. Ingestion lag is a continuous measure of data freshness at any point in time.

**Owner:** Mei Lin (Data Engineering)
**Refresh cadence:** Hourly

---

## 10. Metric Implementation Standards

### 10.1 Semantic Layer

All metrics are defined as reusable calculated metrics in the semantic layer (TECH-16, Mei Lin), expressed in YAML and compiled to dbt metrics. This ensures a single source of truth: any dashboard, report, or API query referencing a metric uses the same underlying calculation.

The semantic layer is accessed by InsightDash via the metric catalog, integrated per TECH-19. External access via the DataLake Pro API uses the same compiled metric definitions.

### 10.2 Naming Conventions

All metric names follow the pattern: `{product}.{domain}.{metric_name}` in snake_case.

Examples:
- `insightdash.engagement.monthly_active_dashboards`
- `streamapi.operations.p99_event_delivery_latency_ms`
- `datalakepro.quality.great_expectations_pass_rate`
- `business.revenue.monthly_recurring_revenue_usd`

### 10.3 Metric Versioning

When a metric definition changes:
- The metric name is preserved but the definition is versioned: `{metric_name}_v2`.
- The prior version (`_v1`) remains queryable for historical comparison.
- The current version is set as the default in InsightDash.
- A migration note is added to the metric's documentation in the data catalog (Apache Atlas, TECH-46).

### 10.4 Null & Zero Handling

- **Activity metrics** (counts of events or users): Use `0` for periods with no activity. Nulls indicate a data pipeline failure, not zero activity.
- **Ratio metrics** (percentages, rates): Use `NULL` when the denominator is zero, rather than `0` or `infinity`. Dashboards display `N/A` for null ratio metrics.
- **Latency metrics** (P95, P99): Use `NULL` for periods with no requests. Do not impute 0 — zero latency is physically impossible and would distort percentile calculations.

---

## 11. Glossary

**Account:** A paying or trial customer organization in XYZ Analytics. A single account may have many users.

**Active:** Having performed at least one qualifying event within the defined measurement window. The qualifying event varies by metric — always specified in the metric definition.

**Cohort:** A group of accounts or users who shared a common experience at the same time (e.g., all accounts that signed up in January 2025).

**DAU:** Daily Active Users. Unique users with at least one human session in a calendar day.

**DLQ:** Dead Letter Queue. A Kafka topic holding events that failed delivery and are awaiting replay or manual review.

**dbt:** Data Build Tool. XYZ Analytics' SQL transformation framework, used to build and document all curated data models in Snowflake.

**Error Budget:** The allowable amount of SLO violation within a measurement window. See Section 8.2.

**Great Expectations:** Open-source data quality validation framework. See TECH-47.

**MAD:** Monthly Active Dashboards. Distinct dashboards with at least one successful human-initiated render in a rolling 28-day window.

**MRR:** Monthly Recurring Revenue. Normalized monthly value of all active subscriptions.

**NRR:** Net Revenue Retention. MRR retained from an existing customer cohort 12 months later, including expansions and contractions.

**P95 / P99:** The 95th / 99th percentile of a distribution. For latency metrics, the value below which 95% / 99% of observations fall.

**Semantic Layer:** The centralized repository of metric definitions (TECH-16) that ensures consistent metric calculations across all consuming systems.

**SLO:** Service Level Objective. A target for a specific reliability or performance metric, used to manage error budgets. See DEVOPS-RUN-001 Section 5.3.

**TTFE:** Time to First Event. The elapsed time for a new StreamAPI account to receive their first production event. Primary StreamAPI activation metric.

---

## 12. Revision History

| Version | Date       | Author          | Summary                                                  |
|---------|------------|-----------------|----------------------------------------------------------|
| 1.0     | 2024-07-01 | Priya Nair      | Initial metrics guide — InsightDash and StreamAPI        |
| 1.1     | 2024-10-14 | Mei Lin         | Semantic layer integration, dbt metric definitions       |
| 1.2     | 2024-12-20 | Samuel Osei     | DataLake Pro metrics, Great Expectations pass rate added |
| 1.3     | 2025-03-01 | Simone Dupont   | Customer Health Score, NRR, cross-product metrics added  |
