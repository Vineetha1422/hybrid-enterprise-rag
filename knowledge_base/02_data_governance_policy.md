---
document_id: DATA-GOV-001
department: Data
owner: Laura Hensley
reviewer: James Okafor
last_updated: 2025-02-28
version: 1.4
related_tickets: [TECH-42, TECH-44, TECH-52]
related_products: [DataLake Pro, InsightDash]
related_docs: [SEC-ACCESS-001, ENG-ARCH-001]
---

# XYZ Analytics — Data Governance Policy

## Table of Contents

1. [Purpose & Scope](#purpose--scope)
2. [Governance Principles](#governance-principles)
3. [Data Classification Framework](#data-classification-framework)
4. [Data Ownership & Stewardship](#data-ownership--stewardship)
5. [Data Retention & Deletion](#data-retention--deletion)
6. [PII Handling & Privacy Compliance](#pii-handling--privacy-compliance)
7. [Data Quality Standards](#data-quality-standards)
8. [Access Control for Data Assets](#access-control-for-data-assets)
9. [Audit & Compliance](#audit--compliance)
10. [Incident Response for Data Breaches](#incident-response-for-data-breaches)
11. [Policy Exceptions](#policy-exceptions)

---

## 1. Purpose & Scope

This Data Governance Policy defines the standards, responsibilities, and processes governing how XYZ Analytics collects, stores, transforms, accesses, and deletes data across all of its products and internal systems. It applies to all employees, contractors, and third-party vendors who interact with XYZ Analytics data assets in any capacity.

**Policy Owner:** Laura Hensley, Head of Data
**Legal & Compliance Reviewer:** Marcus Webb, HR Director (acting Compliance Lead)
**Technical Reviewer:** James Okafor, CTO

This policy is a companion document to the **Security & Access Control Policy (SEC-ACCESS-001)** and the **Engineering Architecture Document (ENG-ARCH-001)**. Where this policy defines *what* must be done with data, ENG-ARCH-001 defines *how* the systems implementing that policy are built, and SEC-ACCESS-001 governs *who* may access which data assets.

This policy applies to data processed, stored, or transmitted by:
- **DataLake Pro** — XYZ Analytics' managed data warehouse product
- **InsightDash** — BI dashboard product, which surfaces data derived from DataLake Pro
- **StreamAPI** — Real-time event streaming platform, whose event payloads may contain customer or end-user data
- All internal data infrastructure, including the analytics data warehouse used by XYZ Analytics' own Data and Product teams

---

## 2. Governance Principles

XYZ Analytics' approach to data governance is grounded in five core principles, adopted by the Data team under Laura Hensley's leadership and ratified by the executive team in January 2025:

1. **Data as a Shared Asset:** Data is a company-wide resource. Teams are stewards of the data they produce or consume — not owners in the sense of exclusivity. All data assets must be documented, cataloged, and made discoverable to authorized users.

2. **Privacy by Design:** Privacy protections are built into data systems from inception, not retrofitted. Every new data pipeline, schema, or product feature must include a data privacy impact assessment before being shipped to production.

3. **Least Privilege Access:** No individual or system should have broader access to data than is strictly necessary for their role or function. Access grants are time-limited where feasible and reviewed quarterly. See Section 8 for specifics.

4. **Data Quality as a First-Class Concern:** Inaccurate or stale data that is surfaced via InsightDash or consumed via DataLake Pro is a product defect. The Data team maintains quality standards and automated checks (see Section 7) with the same rigor applied to software bugs.

5. **Regulatory Compliance as a Baseline:** XYZ Analytics operates under GDPR (for EU customers), CCPA (for California residents), and SOC 2 Type II requirements. Compliance with these frameworks is a non-negotiable baseline, not an optional enhancement.

---

## 3. Data Classification Framework

All data at XYZ Analytics is classified into one of four tiers. Classification determines storage requirements, access controls, retention periods, and handling procedures.

### Tier 1 — Public

Data that is intentionally made available to the public or to all authenticated users without restriction.

**Examples:** Product documentation, public API schemas, anonymized benchmark datasets used in marketing.

**Requirements:** No special handling. May be stored in any system.

### Tier 2 — Internal

Data intended for use by XYZ Analytics employees but not for external distribution.

**Examples:** Internal dashboards, aggregated usage metrics, non-PII customer analytics, Jira tickets, Slack messages, this policy document.

**Requirements:** Must be stored in company-managed systems. Must not be shared externally without management approval. Accessible to all employees by default.

### Tier 3 — Confidential

Sensitive business data and non-anonymized customer data. Requires explicit access grants.

**Examples:** Customer usage data, contract terms, revenue figures, employee performance reviews, DataLake Pro pipeline configurations containing customer schema details.

**Requirements:**
- Access requires role-based authorization (see Section 8).
- Must be stored in encrypted storage (AES-256 at rest).
- Must not be stored on personal devices or transmitted via personal email.
- Audit logging must be enabled on all systems storing Tier 3 data.

### Tier 4 — Restricted (PII / Sensitive)

Personally Identifiable Information (PII) and other highly sensitive data subject to regulatory protection. This is the most sensitive classification tier.

**Examples:** Customer names, email addresses, phone numbers, physical addresses, social security numbers, payment card data, IP addresses linked to individuals, employee HR records.

**Requirements:**
- Column-level AES-256 encryption at rest in all storage systems, as implemented in **TECH-44** (owned by Nadia Kowalski). This ticket represents a critical compliance deliverable and is being tracked by Laura Hensley as a P0 item.
- Access is restricted to named individuals with a documented business justification, approved by the data steward and the Head of Data.
- Data cannot leave the production environment without undergoing anonymization or pseudonymization first.
- Retention and deletion are governed by the policies in Section 5.
- GDPR right-to-erasure requests must be fulfilled within 30 days via the automated pipeline described in **TECH-52** (owned by Samuel Osei).

---

## 4. Data Ownership & Stewardship

### 4.1 Data Domain Owners

Each major data domain at XYZ Analytics has a designated **Data Domain Owner** — a senior individual in the relevant business function responsible for defining business rules, approving access requests, and ensuring the domain's data is fit for purpose.

| Data Domain              | Domain Owner        | Data Steward (Technical) |
|--------------------------|---------------------|--------------------------|
| Customer Usage Data      | Priya Nair          | Mei Lin                  |
| Product Events (Stream)  | Ben Adeyemi         | Carlos Vega              |
| Financial & Revenue      | Sarah Mitchell      | Simone Dupont            |
| Employee / HR Data       | Marcus Webb         | Yuki Tanaka              |
| Pipeline Metadata        | Laura Hensley       | Nadia Kowalski           |
| Marketing & CRM Data     | Ingrid Svensson     | Samuel Osei              |

### 4.2 Data Steward Responsibilities

Data Stewards are technical members of the Data team responsible for the day-to-day governance of their assigned domain. Steward responsibilities include:

- Maintaining accurate metadata and documentation in the data catalog (Apache Atlas, per TECH-46 owned by Simone Dupont).
- Reviewing and approving access requests submitted via the self-serve portal (TECH-49).
- Monitoring data quality dashboards and triaging quality failures within 24 hours of detection.
- Ensuring classification tags are accurate and up to date for all tables in their domain.
- Coordinating with the DevOps team (under Aisha Patel) when pipeline changes affect data availability SLAs.

### 4.3 The Data Governance Council

The Data Governance Council meets bi-weekly and consists of: Laura Hensley (chair), one representative from each of Product, Engineering, and HR, and an invited member from the relevant business team when domain-specific issues are on the agenda. Council decisions are documented and published to the internal wiki within five business days of each meeting.

---

## 5. Data Retention & Deletion

### 5.1 Retention Schedule

All data assets in DataLake Pro are subject to the following default retention schedule, which is enforced via automated policies implemented in **TECH-42** (owned by Nadia Kowalski, currently in review as of March 2025):

| Data Tier  | Raw Layer Retention | Curated Layer Retention | Archive Layer |
|------------|--------------------|-----------------------|---------------|
| Tier 1     | 5 years            | Indefinite            | N/A           |
| Tier 2     | 3 years            | 5 years               | Optional      |
| Tier 3     | 2 years            | 3 years               | Encrypted     |
| Tier 4 (PII)| 13 months         | 13 months             | Not permitted |

Exceptions to the above schedule require written approval from the Head of Data and must be documented in the data catalog with a business justification and an expiry date for the exception.

### 5.2 GDPR Right-to-Erasure (Right to Be Forgotten)

XYZ Analytics is obligated under GDPR Article 17 to erase a data subject's personal data upon request within 30 calendar days. The automated GDPR deletion pipeline (TECH-52), led by Samuel Osei and reviewed by Marcus Webb, handles:

1. Receiving deletion requests via the customer support portal.
2. Identifying all table and column locations containing the subject's PII, based on classification metadata in Apache Atlas.
3. Executing deletion scripts against all affected tables across DataLake Pro, InsightDash operational stores, and StreamAPI event archives.
4. Generating a deletion certificate for the requesting subject, logged for audit purposes.

TECH-52 is currently blocked on TECH-42 (retention policy tooling) being fully deployed. Until TECH-52 is in production, deletion requests are handled manually by Nadia Kowalski and Samuel Osei, with a documented SLA of 25 days (5-day buffer before the regulatory deadline).

### 5.3 Data Deletion Verification

Following any deletion operation — automated or manual — the relevant Data Steward must verify deletion completeness within 48 hours by querying the classification catalog and confirming zero matching records. Verification results are logged in the audit trail (see Section 9).

---

## 6. PII Handling & Privacy Compliance

### 6.1 PII Identification

All fields in DataLake Pro schemas that contain or may contain PII must be tagged with the `pii: true` classification attribute in Apache Atlas. Automated PII detection using pattern matching (email regex, phone number patterns, SSN patterns) runs on all new ingestion sources during onboarding, with results reviewed by the relevant Data Steward.

### 6.2 Encryption Requirements

PII fields must be encrypted using AES-256 at rest in all DataLake Pro tables. This is implemented at the column level using Snowflake's column-level security features, as tracked in **TECH-44**. The following fields are always classified as PII and must always be encrypted:

- `email`, `email_address`
- `phone`, `phone_number`
- `ssn`, `social_security_number`
- `dob`, `date_of_birth`
- `ip_address` (when linked to a specific individual)
- `full_name`, `first_name` + `last_name` when combined with any other identifier

### 6.3 Cross-Border Data Transfers

Customer data from EU data subjects must not be transferred to or stored in regions outside the EU/EEA without either:
- An adequacy decision from the European Commission, or
- Standard Contractual Clauses (SCCs) in place with the receiving entity.

All DataLake Pro deployments serving EU customers run in AWS `eu-west-1` (Ireland). Data replication across regions for DR purposes (TECH-51) must comply with these transfer restrictions — Nadia Kowalski is responsible for ensuring the cross-region replication configuration excludes EU-origin data from replication to `us-west-2`.

---

## 7. Data Quality Standards

XYZ Analytics uses **Great Expectations** as its data quality validation framework, as implemented by Samuel Osei in **TECH-47**. Every ingestion pipeline in DataLake Pro must have a corresponding Great Expectations suite that runs at ingestion time.

### 7.1 Mandatory Quality Checks

The following checks are mandatory for all pipelines delivering data to the curated layer:

- **Null checks:** Columns designated as non-nullable must have zero null values.
- **Uniqueness checks:** Primary key columns must have no duplicates.
- **Range checks:** Numeric columns must fall within documented expected ranges.
- **Referential integrity:** Foreign key columns must reference valid records in the parent table.
- **Freshness checks:** All curated tables must have been updated within the defined SLA window. Pipeline SLA breaches (>2 hours) trigger PagerDuty alerts per TECH-50 (owned by Simone Dupont).

### 7.2 Quality Failure Handling

If a Great Expectations suite fails during ingestion:
1. The pipeline halts and does not write to the curated layer.
2. Data is quarantined in the `raw.quarantine` schema for manual review.
3. A PagerDuty alert is triggered and assigned to the pipeline's on-call Data Engineer.
4. The Data Steward for the relevant domain is notified within 15 minutes.
5. Root cause analysis must be completed within 4 hours for Tier 3/4 data pipelines and within 24 hours for Tier 1/2 pipelines.
6. A post-mortem is required for any quality failure that persists for more than 2 hours in a Tier 3/4 pipeline.

---

## 8. Access Control for Data Assets

Data access at XYZ Analytics follows a role-based access control model implemented within Snowflake, governed by policies defined in **SEC-ACCESS-001**. Row-level security policies (TECH-74) are currently being implemented by Mei Lin to enforce tenant isolation at the data layer.

Access requests for Tier 3 and Tier 4 data must be submitted via the self-serve access request portal (TECH-49, in development by Carlos Vega), which routes requests to the appropriate Data Domain Owner for approval. Approved grants are time-limited to 90 days and must be renewed with re-justification.

Direct SQL access to production Snowflake tables is restricted to the Data Engineering team. Analysts access curated data via approved BI tools (InsightDash) or via dedicated read-only Snowflake roles with row-level security applied.

---

## 9. Audit & Compliance

All access to Tier 3 and Tier 4 data assets generates an audit log entry in the centralized audit trail, stored in OpenSearch (TECH-68). Audit logs are retained for a minimum of 3 years and are immutable once written.

SOC 2 Type II compliance reviews are conducted annually, with the most recent review completed in November 2024. Evidence collection for the next review is coordinated by Laura Hensley and Chloe Brennan (HR Business Partner acting as SOC 2 coordinator).

The Data team provides quarterly compliance reports to the executive team summarizing: access grant counts, PII exposure events, deletion request completion rates, and data quality SLA adherence.

---

## 10. Policy Exceptions

Exceptions to any provision of this policy must be:

1. Submitted in writing to the Head of Data (Laura Hensley).
2. Reviewed by the Data Governance Council within 10 business days.
3. Approved by both the Head of Data and the CTO (James Okafor) for Tier 3/4 exceptions.
4. Documented in the policy exceptions register with a defined expiry date and compensating controls.

---

## 11. Revision History

| Version | Date       | Author           | Summary                                       |
|---------|------------|------------------|-----------------------------------------------|
| 1.0     | 2023-08-01 | Laura Hensley    | Initial policy                                |
| 1.1     | 2024-02-14 | Nadia Kowalski   | Added GDPR deletion SLA, retention schedule   |
| 1.2     | 2024-07-30 | Mei Lin          | Added PII column encryption requirements      |
| 1.3     | 2024-11-18 | Samuel Osei      | Great Expectations standards added            |
| 1.4     | 2025-02-28 | Laura Hensley    | Apache Atlas integration, TECH-52 procedures  |
