---
document_id: SEC-ACCESS-001
department: Engineering
owner: Aisha Patel
reviewer: James Okafor
last_updated: 2025-02-20
version: 2.3
related_tickets: [TECH-40, TECH-44, TECH-59, TECH-66, TECH-72]
related_products: [InsightDash, StreamAPI, DataLake Pro]
related_docs: [ENG-ARCH-001, DATA-GOV-001, DEVOPS-RUN-001, OPS-INC-001]
---

# XYZ Analytics — Security & Access Control Policy

## Table of Contents

1. [Purpose & Scope](#purpose--scope)
2. [Security Principles](#security-principles)
3. [Identity & Access Management](#identity--access-management)
4. [Authentication Standards](#authentication-standards)
5. [Network Security](#network-security)
6. [Data Security & Encryption](#data-security--encryption)
7. [Endpoint & Device Security](#endpoint--device-security)
8. [Application Security](#application-security)
9. [Third-Party & Vendor Access](#third-party--vendor-access)
10. [Security Monitoring & Threat Detection](#security-monitoring--threat-detection)
11. [Vulnerability Management](#vulnerability-management)
12. [Security Incident Response](#security-incident-response)
13. [Employee Security Training](#employee-security-training)
14. [SOC 2 Compliance Controls](#soc-2-compliance-controls)
15. [Policy Exceptions](#policy-exceptions)

---

## 1. Purpose & Scope

This Security & Access Control Policy defines the security standards, controls, and responsibilities that protect XYZ Analytics' systems, data, employees, and customers from unauthorized access, data breaches, and other security threats. It is the master security reference for all departments and applies without exception to every employee, contractor, vendor, and system operating within or connecting to XYZ Analytics infrastructure.

**Policy Owner:** Aisha Patel, DevOps Lead (acting CISO)
**Executive Sponsor:** James Okafor, CTO
**Compliance Coordinator:** Chloe Brennan, HR Business Partner

This policy works in concert with several companion documents. The **Engineering Architecture Document (ENG-ARCH-001)** describes the infrastructure this policy secures. The **Data Governance Policy (DATA-GOV-001)** governs data classification and PII handling controls that this policy enforces at the infrastructure layer. The **DevOps Runbook (DEVOPS-RUN-001)** contains the operational procedures for implementing these controls day-to-day. The **Incident Management SOP (OPS-INC-001)** governs response when security controls fail.

XYZ Analytics is pursuing and maintaining **SOC 2 Type II certification**. All controls in this policy map to SOC 2 Trust Service Criteria. Section 14 provides explicit control mappings.

> **Classification of this document:** Tier 3 — Confidential. Do not share externally. Access is restricted to XYZ Analytics employees and auditors under NDA.

---

## 2. Security Principles

XYZ Analytics' security posture is built on the following foundational principles, adopted by the engineering leadership team under James Okafor and operationalized by Aisha Patel:

**Zero Trust Architecture.** No network location is inherently trusted. Every request — whether from inside the corporate VPN, from a cloud service, or from an authenticated employee — must be verified before access is granted. Trust is never assumed; it is established through authentication, authorization, and continuous verification.

**Least Privilege by Default.** Every person, service, and system is granted only the minimum access required to perform their defined function. Broad access grants are a security liability. Permissions must be explicitly justified and regularly reviewed.

**Defense in Depth.** Security controls are layered. The failure of any single control — a misconfigured firewall, a compromised credential, or an unpatched vulnerability — should not result in an uncontrolled breach. Multiple independent controls provide resilience.

**Shift Left on Security.** Security is not a gate at the end of the development process — it is embedded throughout. Engineers are responsible for writing secure code. Security scanning runs in CI/CD. Architectural security reviews happen before design decisions are locked.

**Transparency and Accountability.** All access to sensitive systems is logged. All security incidents are documented and learned from. Security posture is reviewed and reported to executive leadership quarterly.

---

## 3. Identity & Access Management

### 3.1 Identity Provider

XYZ Analytics uses **Okta** as the company-wide Identity Provider (IdP) for all employee and application identity. All SaaS tools, internal applications, and cloud consoles must authenticate via Okta where technically feasible. Direct username/password authentication to any production system is prohibited.

The unified authentication microservice (TECH-66), currently in development under Fatima Al-Hassan, will extend Okta-based OAuth 2.0 + OIDC authentication to all three XYZ Analytics products — InsightDash, StreamAPI, and DataLake Pro — through a single shared auth layer.

### 3.2 Access Request & Approval Process

All access requests to production systems, data stores, and sensitive tooling must follow this process:

1. Employee submits an access request via the IT/Security request portal (or, for data assets, the Data Access Portal — TECH-49).
2. Request routes to the system owner for approval. For AWS production accounts, the approver is Aisha Patel. For Snowflake, the approver is Mei Lin (Data Engineering).
3. Access is provisioned with a default expiry of **90 days**. Permanent access grants require VP-level approval and are reviewed quarterly.
4. Access provisioning is logged in the access control audit trail within 24 hours.
5. Access is revoked automatically on expiry unless renewed. Renewal requires re-justification via the same request process.

### 3.3 Joiner / Mover / Leaver Process

**Joiner (new hire):** Aisha Patel's team provisions standard role-based access on the employee's start date, based on their role and team profile. Onboarding access provisioning is triggered automatically from the HRIS when Yuki Tanaka confirms the start date.

**Mover (role change / team transfer):** The employee's manager submits a role-change access request within 5 business days of the effective date. Excess permissions from the previous role must be revoked at the same time new permissions are granted.

**Leaver (offboarding):** HR (coordinated by Derek Fountaine) notifies IT Security at minimum 24 hours before the employee's last day. All access — Okta account, AWS, Snowflake, GitHub, and all SaaS tools — must be revoked within **1 hour** of the employee's official separation time. Revocation is verified and logged by Aisha Patel's team.

### 3.4 Privileged Access Management

Access to production infrastructure (AWS production accounts, production Kubernetes clusters, production databases) is classified as **privileged access** and subject to enhanced controls:

- Privileged access is granted only to members of the DevOps team and named Engineering leads (currently: Fatima Al-Hassan, Tom Nguyen, Arjun Mehta).
- Privileged sessions are recorded via AWS CloudTrail and reviewed in weekly security reviews chaired by Aisha Patel.
- Just-in-time (JIT) access via AWS IAM Identity Center is used for production account access — persistent admin roles are not permitted.
- Any privileged action that modifies production infrastructure outside the CI/CD pipeline must be accompanied by a change record posted to `#devops-prod-ops`.

### 3.5 Service Account Management

Service accounts used by applications to access databases, APIs, or cloud services must:

- Be non-human accounts with no interactive login capability.
- Credentials stored exclusively in AWS Secrets Manager — never in environment variables, config files, or source code.
- Rotated on a minimum 90-day cycle (30-day cycle for accounts with write access to Tier 4 data stores).
- Granted the minimum necessary permissions and scoped to a single service.

Hannah Brooks maintains the service account inventory in the infrastructure repository. Raj Iyer owns the rotation schedule enforcement via automated Lambda functions.

---

## 4. Authentication Standards

### 4.1 Multi-Factor Authentication

MFA is **mandatory** for all user accounts at XYZ Analytics. There are no exceptions.

- **For employees:** Okta Verify (TOTP or push notification) is the required MFA method. Hardware security keys (YubiKey) are required for privileged access accounts (DevOps team and senior engineering leads).
- **For customer accounts:** InsightDash and DataLake Pro enforce MFA for all users at the enterprise tier. MFA is strongly recommended and defaulted on for all other tiers. StreamAPI uses API keys + HMAC signatures (TECH-35) as the primary customer authentication mechanism.
- FIDO2/WebAuthn is the preferred MFA standard for new implementations. TOTP is acceptable. SMS-based MFA is not permitted for any XYZ Analytics employee account.

### 4.2 Password Policy

Where passwords are used (increasingly rare given Okta SSO), the following standards apply:

- Minimum length: **16 characters**.
- Must include at least one uppercase letter, one lowercase letter, one number, and one special character.
- Password reuse: last 12 passwords cannot be reused.
- Maximum age: 365 days (annual rotation required).
- Passwords must never be shared, written down, or stored in plain text.
- All employee passwords must be managed via the company-approved password manager (1Password for Business).

### 4.3 Session Management

- Production web application sessions (InsightDash) expire after **8 hours** of inactivity.
- API sessions (StreamAPI) use short-lived JWT tokens (15-minute TTL) with silent refresh (TECH-24, Tom Nguyen). Refresh tokens expire after 7 days of inactivity.
- Administrative console sessions (AWS, Snowflake) expire after **1 hour**.
- Concurrent sessions from different geographic locations trigger a security alert and require re-authentication.

### 4.4 API Key Management

StreamAPI customers authenticate using per-application API keys. API key security requirements:

- Keys are generated with 256-bit entropy and displayed only once at creation. XYZ Analytics does not store the plaintext key after generation — only a bcrypt hash.
- Keys can be scoped to specific topics, event types, and IP ranges.
- Key rotation is supported without service interruption via dual-key grace periods.
- Compromised or suspected-compromised keys must be rotated immediately. The customer is notified via email and the security event is logged.

---

## 5. Network Security

### 5.1 VPN Policy

All access to XYZ Analytics internal systems — including production infrastructure, internal dashboards, data stores, and development environments — requires an active VPN connection using the company-provisioned **WireGuard VPN** client.

VPN is required for:
- Access to any AWS private subnet resource (RDS, MSK, EKS internal endpoints, Snowflake via private link).
- Access to internal tooling (Grafana, Airflow, ArgoCD, Jenkins).
- Access to any Tier 3 or Tier 4 data, including via InsightDash or DataLake Pro admin interfaces.

Split-tunnel VPN is configured so that only traffic destined for internal IP ranges flows through the VPN. General internet traffic does not traverse the VPN. This reduces latency for remote workers while maintaining security for internal access.

### 5.2 Network Segmentation

Production network architecture follows the segmentation model described in ENG-ARCH-001. Key security principles implemented at the network layer:

- All production application workloads run in private subnets with no direct inbound internet access.
- Internet-facing traffic is routed exclusively through the ALB/WAF layer.
- AWS Security Groups follow a default-deny model — all inbound traffic is blocked unless an explicit allow rule exists.
- Internal service-to-service communication follows mTLS where implemented (TECH-40 for StreamAPI, Lucia Ferreira) and TLS 1.2+ everywhere else. TLS 1.0 and 1.1 are disabled on all endpoints.
- The `0.0.0.0/0` CIDR is never permitted in production security group inbound rules.

### 5.3 WAF Configuration

AWS WAF is deployed in front of all public-facing ALBs and CloudFront distributions. Active rule sets include:

- AWS Managed Rules (Core Rule Set + Known Bad Inputs)
- Rate limiting: 1,000 requests per 5-minute window per source IP before soft block; 5,000 requests triggers hard block.
- SQL injection and XSS detection rules.
- Geo-blocking is not enforced by default but can be activated per-product in response to threat intelligence.

WAF logs are shipped to OpenSearch (TECH-68) and reviewed weekly by Aisha Patel. Anomalous patterns trigger Slack alerts to `#security-alerts`.

### 5.4 Snowflake Network Policies

Snowflake production access is restricted to known IP ranges via network policies managed in Terraform (TECH-59, Lucia Ferreira). The allowlist includes the VPN egress IPs, the production EKS NAT gateway IPs, and the AWS MWAA (Airflow) NAT gateway IPs. No other IP ranges are permitted.

All Snowflake network policy changes must be made via Terraform PR, reviewed by Raj Iyer, and approved by Aisha Patel. Manual changes via the Snowflake UI are prohibited and will be overwritten on the next Terraform apply.

---

## 6. Data Security & Encryption

### 6.1 Encryption at Rest

All data stores at XYZ Analytics apply encryption at rest:

- **Amazon RDS:** AES-256 encryption enabled on all instances via AWS KMS.
- **Amazon S3:** Default bucket encryption with AES-256 (SSE-S3). Sensitive buckets use SSE-KMS with customer-managed keys.
- **Amazon MSK (Kafka):** Broker storage encrypted with AES-256 via AWS KMS.
- **Snowflake:** Platform-level AES-256 encryption for all data. PII columns additionally encrypted at the column level (TECH-44, Nadia Kowalski) using Snowflake Dynamic Data Masking policies.
- **Developer laptops:** Full disk encryption (FileVault on macOS) is enforced via MDM. Non-compliant devices cannot connect to company Wi-Fi or VPN.

### 6.2 Encryption in Transit

All data in transit is encrypted using **TLS 1.2 or higher**. Specifically:

- All external API traffic (InsightDash, StreamAPI, DataLake Pro) uses TLS 1.3 where supported by clients, falling back to TLS 1.2.
- Internal service-to-service communication within EKS uses TLS 1.2 minimum, enforced via service mesh policies.
- mTLS is enforced for StreamAPI broker-to-consumer paths (TECH-40) and is being rolled out to all internal microservice communication.
- Database connections from application pods to RDS use SSL with certificate verification (no `sslmode=disable` permitted in production).

### 6.3 Key Management

Encryption keys are managed via **AWS KMS** (for AWS-resident data) and **Snowflake Key Management** (for Snowflake data). Key rotation policies:

- AWS KMS Customer Managed Keys: Annual automatic rotation.
- RDS instance encryption keys: Annual rotation coordinated by Raj Iyer.
- Snowflake Tri-Secret Secure keys: Annual rotation, requires coordination between Aisha Patel and Snowflake support.

Key access is logged via AWS CloudTrail. Any unexpected key usage generates an alert in `#security-alerts`.

---

## 7. Endpoint & Device Security

### 7.1 Device Management

All company-issued devices are enrolled in **Jamf Pro** (MDM) within 24 hours of provisioning. MDM enforces:

- FileVault full-disk encryption (confirmed before network access granted).
- Automatic screen lock at 5 minutes of inactivity.
- macOS automatic security updates enabled.
- Firewall enabled.
- Unapproved software installation blocked for non-admin users.

Personal devices (BYOD) are not permitted to access production systems, internal tools, or Tier 3/4 data under any circumstances. There are no exceptions to this rule.

### 7.2 Endpoint Detection & Response

All company laptops run **CrowdStrike Falcon** for endpoint detection and response (EDR). Falcon is configured with prevention policies enabled — detected threats are automatically contained, not just alerted. Security events from Falcon are reviewed weekly by Aisha Patel.

### 7.3 Mobile Devices

Company mobile phones are not currently issued. Employees may use personal phones for MFA authentication (Okta Verify app). No other company data should be stored on personal mobile devices.

---

## 8. Application Security

### 8.1 Secure Development Lifecycle

All XYZ Analytics products follow a Secure Development Lifecycle (SDL) with the following mandatory gates:

- **Design phase:** Threat model required for any new service, feature, or significant architectural change. Threat models are reviewed by Fatima Al-Hassan (Engineering) and Aisha Patel (Security).
- **Development phase:** Static Application Security Testing (SAST) via Semgrep runs in CI on every PR. Dependency vulnerability scanning via Snyk runs on every PR and blocks merge on Critical CVEs.
- **Pre-release phase:** Dynamic Application Security Testing (DAST) via OWASP ZAP runs against staging environments before major releases.
- **Post-release phase:** Annual external penetration test covering all three products (TECH-72, coordinated by Aisha Patel). Most recent pen test was conducted in Q4 2024.

### 8.2 Security Headers

All XYZ Analytics web applications (InsightDash, DataLake Pro admin UI) must implement the following security headers:

- `Content-Security-Policy` — restricts content sources to explicitly allowlisted origins
- `Strict-Transport-Security` with `max-age=31536000; includeSubDomains; preload`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy` — disables unused browser features (camera, microphone, geolocation)

Compliance with these headers is verified by Tyler Moss (QA) as part of release checklists. Any regression in security headers blocks release.

### 8.3 Input Validation & Injection Prevention

All user-supplied input must be validated and sanitized before use in queries, commands, or API calls:

- SQL queries must use parameterized queries or ORM abstractions — raw string concatenation in SQL is prohibited.
- API inputs are validated against OpenAPI schemas before processing.
- File uploads (InsightDash export imports, DataLake Pro connector configurations) are scanned with ClamAV before being written to storage.
- JSONPath filter expressions (StreamAPI — TECH-31) are validated against an allowlist grammar before evaluation.

---

## 9. Third-Party & Vendor Access

Any third-party vendor, contractor, or integration partner requiring access to XYZ Analytics systems must:

1. Sign a Data Processing Agreement (DPA) and NDA before access is provisioned. Contracts are managed by Marcus Webb (HR/Legal).
2. Be assessed against the XYZ Analytics Vendor Security Questionnaire, reviewed by Aisha Patel.
3. Be granted access via dedicated, named service accounts — shared credentials with internal staff are prohibited.
4. Have their access reviewed quarterly and revoked when the engagement ends.
5. Not store XYZ Analytics customer data in their own systems without explicit DPA coverage for that storage.

A register of all third-party vendors with system access is maintained by Yuki Tanaka and reviewed by Aisha Patel quarterly. Current vendor count with production system access: 12 (as of February 2025).

---

## 10. Security Monitoring & Threat Detection

### 10.1 Security Information & Event Management

Security events from across the XYZ Analytics environment are aggregated into the OpenSearch SIEM (TECH-68, Omar Shaikh). Sources include:

- AWS CloudTrail (all API activity across all accounts)
- VPC Flow Logs (all network traffic)
- AWS WAF logs
- Okta authentication logs
- Snowflake access logs
- Application security headers and auth failure logs

### 10.2 Automated Threat Detection

The following automated detection rules are active and trigger alerts to `#security-alerts` and PagerDuty (P2 or above):

- Successful login from a new geographic location.
- More than 5 failed MFA attempts for a single user within 10 minutes.
- AWS root account usage (any action by the root account triggers a P1 page).
- IAM policy change outside of the CI/CD pipeline.
- Snowflake data export volume exceeding 10GB in a single session.
- Unusual time-of-day access for any privileged user account.
- Any access to Tier 4 data by a non-approved user (based on Data Access Portal records).

### 10.3 Security Review Cadence

- **Weekly:** Aisha Patel reviews CloudTrail anomalies, WAF alerts, and CrowdStrike EDR events.
- **Monthly:** Security team reviews access grant inventory, identifies over-provisioned accounts, and reviews vendor access.
- **Quarterly:** Executive security report presented by Aisha Patel to James Okafor and Sarah Mitchell. Covers: incident count, SLA adherence, vulnerability status, SOC 2 control health.
- **Annually:** External penetration test (TECH-72) and SOC 2 Type II audit.

---

## 11. Vulnerability Management

### 11.1 Vulnerability Scanning

- **Container images:** All Docker images are scanned via Snyk on every CI build. Critical CVEs block merge; High CVEs trigger a Slack alert to the engineering team and must be remediated within 7 days.
- **Infrastructure:** AWS Inspector scans all EC2 instances and EKS node groups weekly. Findings are triaged by Hannah Brooks.
- **Dependencies:** Snyk monitors all application dependencies in production continuously, not just at CI time. Newly disclosed vulnerabilities generate alerts within 4 hours of public disclosure.

### 11.2 Patching SLA

| Severity  | Patch SLA             | Owner             |
|-----------|-----------------------|-------------------|
| Critical  | 24 hours              | Aisha Patel       |
| High      | 7 days                | Relevant Eng Lead |
| Medium    | 30 days               | Hannah Brooks     |
| Low       | Next sprint cycle     | Team discretion   |

OS and Kubernetes node patches are applied via a rolling update process managed by Lucia Ferreira. Applications that cannot be patched within SLA require a documented compensating control approved by Aisha Patel.

---

## 12. Security Incident Response

Security incidents are handled per the **Incident Management SOP (OPS-INC-001)**. Security-specific additions to that process:

- Any suspected or confirmed data breach involving Tier 3 or Tier 4 data triggers mandatory notification to Aisha Patel and James Okafor within **1 hour** of detection.
- GDPR breach notification requirements (72-hour deadline to supervisory authority) are activated for any confirmed breach of EU resident data. Marcus Webb coordinates external communications.
- All security incidents are documented in a Security Incident Register maintained by Aisha Patel, retained for a minimum of 3 years.
- Post-incident, a blameless post-mortem is conducted within 5 business days, with findings shared in the `#security-postmortems` channel and incorporated into future controls.

---

## 13. Employee Security Training

All XYZ Analytics employees complete the following mandatory security training:

- **Annual Security Awareness Training:** Covers phishing recognition, password hygiene, data handling, and incident reporting. Completion is tracked by Yuki Tanaka and reported to Marcus Webb. Non-completion after the 30-day window triggers an HR escalation.
- **Phishing Simulations:** Quarterly simulated phishing campaigns run by Aisha Patel's team. Employees who click on simulated phishing links are enrolled in targeted remediation training.
- **Role-Specific Training:** Engineers complete secure coding training (OWASP Top 10) annually. DevOps engineers complete cloud security training (AWS Security Specialty content) annually.
- **New Hire Security Orientation:** Completed in the first week of employment as part of the onboarding checklist (TECH-61, automated via Slack bot by Chloe Brennan).

---

## 14. SOC 2 Compliance Controls

XYZ Analytics maintains SOC 2 Type II certification covering the Security and Availability Trust Service Criteria. The following table maps key policy controls to SOC 2 criteria:

| SOC 2 Criteria | Control Description                              | Policy Section | Evidence Owner    |
|----------------|--------------------------------------------------|----------------|-------------------|
| CC6.1          | Logical access controls / IAM                   | Section 3      | Aisha Patel       |
| CC6.2          | Access provisioning & deprovisioning             | Section 3.3    | Yuki Tanaka       |
| CC6.3          | Role-based access, least privilege               | Section 3.2    | Aisha Patel       |
| CC6.6          | Encryption at rest & in transit                 | Section 6      | Raj Iyer          |
| CC6.7          | Data transmission security (TLS, mTLS)          | Section 6.2    | Lucia Ferreira    |
| CC7.1          | Vulnerability detection & monitoring            | Section 10     | Hannah Brooks     |
| CC7.2          | Security monitoring & anomaly detection         | Section 10.2   | Omar Shaikh       |
| CC7.3          | Security incident evaluation & response         | Section 12     | Aisha Patel       |
| CC8.1          | Change management & deployment controls         | DEVOPS-RUN-001 | Hannah Brooks     |
| A1.1           | Availability — capacity management              | ENG-ARCH-001   | Lucia Ferreira    |
| A1.2           | Availability — monitoring & recovery            | DEVOPS-RUN-001 | Raj Iyer          |

The next SOC 2 Type II audit window is **October–November 2025**. Evidence collection begins August 2025, coordinated by Chloe Brennan with technical evidence provided by Aisha Patel's team.

---

## 15. Policy Exceptions

Security policy exceptions require the highest level of scrutiny at XYZ Analytics. The following process applies:

1. Exception request submitted in writing to Aisha Patel, including: the specific control to be excepted, the business justification, the proposed duration, and the compensating control.
2. Aisha Patel reviews and may approve exceptions for Low/Medium risk controls.
3. Exceptions involving High or Critical risk controls require approval from James Okafor.
4. All exceptions are logged in the Security Exception Register with a maximum duration of 90 days. Re-approval is required for renewal.
5. Exceptions are reviewed as part of the quarterly SOC 2 evidence review.

---

## 16. Revision History

| Version | Date       | Author           | Summary                                              |
|---------|------------|------------------|------------------------------------------------------|
| 1.0     | 2023-04-01 | James Okafor     | Initial security policy                              |
| 1.5     | 2023-10-12 | Aisha Patel      | Added network segmentation, WAF config               |
| 2.0     | 2024-04-08 | Aisha Patel      | Zero trust principles, SIEM integration              |
| 2.1     | 2024-08-19 | Fatima Al-Hassan | SDL section added, SAST/DAST tooling defined         |
| 2.2     | 2024-11-30 | Raj Iyer         | Snowflake network policies (TECH-59), KMS rotation   |
| 2.3     | 2025-02-20 | Aisha Patel      | SOC 2 control mapping, mTLS (TECH-40) added          |
