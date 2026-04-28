---
document_id: OPS-INC-001
department: Engineering
owner: Aisha Patel
reviewer: Daniel Cruz
last_updated: 2025-02-05
version: 1.5
related_tickets: [TECH-22, TECH-34, TECH-67, TECH-68]
related_products: [InsightDash, StreamAPI, DataLake Pro]
related_docs: [DEVOPS-RUN-001, SEC-ACCESS-001, ENG-ARCH-001]
---

# XYZ Analytics — Incident Management SOP

## Table of Contents

1. [Purpose & Scope](#purpose--scope)
2. [Incident Classification](#incident-classification)
3. [Incident Roles & Responsibilities](#incident-roles--responsibilities)
4. [Incident Detection & Declaration](#incident-detection--declaration)
5. [Incident Response Lifecycle](#incident-response-lifecycle)
6. [Communication Standards](#communication-standards)
7. [Escalation Procedures](#escalation-procedures)
8. [Product-Specific Runbooks](#product-specific-runbooks)
9. [Post-Incident Review Process](#post-incident-review-process)
10. [Incident Metrics & Reporting](#incident-metrics--reporting)
11. [Runbook Integration](#runbook-integration)
12. [SOP Review & Maintenance](#sop-review--maintenance)

---

## 1. Purpose & Scope

This Standard Operating Procedure (SOP) defines XYZ Analytics' end-to-end process for detecting, declaring, managing, communicating, resolving, and learning from production incidents across all three core products: **InsightDash**, **StreamAPI**, and **DataLake Pro**.

**SOP Owner:** Aisha Patel, DevOps Lead
**Engineering Sponsor:** Daniel Cruz, VP of Engineering
**Last Major Review:** February 2025

An **incident** is any unplanned event that causes or risks causing a degradation in the availability, correctness, performance, or security of a production service. Incidents range from minor degradations noticed only in monitoring to complete outages affecting all customers. This SOP governs the response to all of them with a consistent, repeatable process.

This SOP is operationalized through the **DevOps Runbook (DEVOPS-RUN-001)**, which contains the specific technical commands and procedures referenced in this document. Security incidents follow the additional procedures defined in **SEC-ACCESS-001 Section 12**. Architectural context for the systems covered here is found in **ENG-ARCH-001**.

Every person at XYZ Analytics who works with production systems — in Engineering, DevOps, or Data — is expected to know and follow this SOP. Familiarity with this document is a requirement of onboarding to any of these teams.

---

## 2. Incident Classification

All incidents are classified into one of four severity levels at declaration time. Severity determines response timelines, communication requirements, and required escalation paths. Misclassifying a high-severity incident as lower severity to avoid escalation is a serious violation of this policy.

### P1 — Critical

A P1 incident represents a severe impact to production systems with immediate customer-facing consequences.

**Criteria — any of the following:**
- Complete unavailability of InsightDash, StreamAPI, or DataLake Pro for any customer segment.
- Data loss or confirmed corruption in any Tier 3 or Tier 4 data store.
- Security breach: unauthorized access to production systems or customer data.
- StreamAPI P99 event delivery latency sustained above 2,000ms for >5 minutes (4x SLO breach).
- SLO error budget exhausted (burn rate alert fires in Grafana) for any product.
- AWS root account usage (auto-escalates to P1 per SEC-ACCESS-001).

**Response SLA:** On-call engineer acknowledged within **15 minutes**. Incident Commander assigned within **20 minutes**. Customer communication within **30 minutes**.

### P2 — High

A P2 incident represents significant degradation affecting a meaningful portion of customers or a critical internal workflow.

**Criteria — any of the following:**
- Partial unavailability of a product feature used by >20% of active users.
- InsightDash dashboard load P95 exceeding 10 seconds sustained for >10 minutes.
- StreamAPI Kafka consumer lag above critical threshold (TECH-38 alert firing) for >10 minutes.
- DataLake Pro Tier 3/4 pipeline SLA breach (data late by >2 hours, per TECH-50).
- Airflow task failures in Tier 3/4 pipelines not auto-recovering after one retry.
- Authentication service (TECH-66) degradation affecting >10% of login attempts.

**Response SLA:** On-call engineer acknowledged within **15 minutes**. Incident Commander assigned within **30 minutes**. Customer communication within **1 hour** (if customer-visible).

### P3 — Medium

A P3 incident represents limited degradation with workarounds available, or an issue affecting internal systems only.

**Criteria — any of the following:**
- Non-critical feature degradation affecting <20% of users.
- Performance degradation not breaching SLO thresholds.
- Internal tooling (Grafana, Airflow UI, ArgoCD) unavailability.
- DataLake Pro Tier 1/2 pipeline delays.
- Elevated error rates on non-critical API endpoints.

**Response SLA:** Acknowledged within **1 hour**. Resolution target within **8 business hours**.

### P4 — Low

A P4 incident represents a minor issue with negligible customer impact.

**Criteria — any of the following:**
- Cosmetic UI bugs in production.
- Single-customer issues with available workarounds.
- Non-urgent monitoring or alerting configuration issues.
- Minor documentation or configuration drift.

**Response SLA:** Acknowledged within **4 hours**. Tracked as a Jira ticket and resolved in the next sprint.

---

## 3. Incident Roles & Responsibilities

Every P1 and P2 incident must have the following roles explicitly assigned within the first 20 minutes of declaration. One person cannot hold more than one role simultaneously during an active incident.

### Incident Commander (IC)

The IC owns the overall incident response. They are not necessarily the most senior engineer on the call — they are the person most effective at coordinating a multi-person response under pressure. For P1 incidents, the IC is always the DevOps on-call engineer or Aisha Patel if she is available.

**IC Responsibilities:**
- Declare the incident in PagerDuty and open the incident Slack channel.
- Assign and track all roles (Tech Lead, Comms Lead, Scribe).
- Make the final call on escalation decisions and resolution declarations.
- Keep the incident moving: drive timebox decisions, prevent rabbit holes, and enforce focus.
- Declare incident resolved and hand off to post-incident process.

### Technical Lead

The engineer (or engineers) actively diagnosing and fixing the problem. For InsightDash incidents, this is typically Tom Nguyen, Arjun Mehta, or Elena Romero. For StreamAPI incidents, Fatima Al-Hassan or Kevin Zhao. For DataLake Pro incidents, Mei Lin or Nadia Kowalski, with DevOps support from Omar Shaikh.

**Tech Lead Responsibilities:**
- Investigate root cause using runbook procedures (DEVOPS-RUN-001) and available observability tooling.
- Propose and implement mitigations and fixes.
- Provide technical status updates to the IC every 15 minutes during active P1/P2 incidents.
- Document all actions taken in the incident Slack channel thread (not DMs).

### Communications Lead (Comms Lead)

The Comms Lead manages all external and internal communications during the incident. For P1 incidents, the Comms Lead is typically Ingrid Svensson (Product) or Ben Adeyemi (Product), as they are best positioned to translate technical status into customer-appropriate language.

**Comms Lead Responsibilities:**
- Post and maintain the public status page (status.xyzanalytics.com) throughout the incident.
- Draft and send customer notification emails for P1 incidents within 30 minutes of declaration.
- Respond to customer-facing Slack Connect channels and support tickets during the incident.
- Coordinate with Priya Nair or Sarah Mitchell for escalated customer communications.
- Prepare the final incident resolution notification.

### Scribe

The Scribe maintains a real-time written record of the incident: timeline of events, actions taken, hypotheses tested, decisions made, and personnel involved. This record becomes the foundation of the post-incident review.

**Scribe Responsibilities:**
- Post a running timeline update in the incident Slack channel every 10–15 minutes.
- Log all commands run in production during the incident (who ran what, when, and why).
- Capture all key decisions and their rationale.
- Export the complete incident log to Notion at incident close for the post-incident review.

---

## 4. Incident Detection & Declaration

### 4.1 Detection Sources

Incidents at XYZ Analytics are detected through several channels:

- **Automated alerting:** PagerDuty pages fired by Prometheus/Grafana alerting rules (TECH-67, Lucia Ferreira). This is the primary detection mechanism for infrastructure and performance issues.
- **Customer reports:** Support tickets, Slack Connect messages, or direct reports from Customer Success. Ingrid Svensson or Ben Adeyemi routes these to the DevOps on-call.
- **Internal detection:** An engineer notices something anomalous during normal work. Any employee who suspects a production issue should report it immediately to `#incidents` — do not wait for certainty.
- **Security monitoring:** Automated SIEM alerts from OpenSearch (TECH-68, Omar Shaikh) or CrowdStrike EDR detections.
- **Synthetic monitoring:** Uptime checks run every 60 seconds against all three product endpoints from multiple regions. Failures trigger PagerDuty directly.

### 4.2 Declaration Procedure

Anyone can and should declare an incident. It is always better to declare a P3 that turns out to be a P4 than to delay declaring a P1.

**Steps to declare an incident:**

1. Post in `#incidents` Slack channel: `"INCIDENT DECLARED — [Product] — [Brief description] — [Initial severity]"`
2. Trigger a PagerDuty incident manually if it has not already been auto-triggered: use the `/pd trigger` Slack command with the appropriate service and severity.
3. The PagerDuty alert pages the on-call engineer. If no acknowledgement within 15 minutes, PagerDuty auto-escalates to the secondary.
4. On-call engineer joins the `#incidents` channel and assumes the IC role (or assigns IC if they are the Tech Lead).
5. IC creates a dedicated incident channel: `#inc-YYYYMMDD-[product]-[short-description]` (e.g., `#inc-20250310-streamapi-kafka-lag`).
6. All incident communication moves to the dedicated channel. `#incidents` is used only for declaration and resolution announcements.
7. IC posts the initial incident status message in the dedicated channel using the template in Section 6.2.

---

## 5. Incident Response Lifecycle

### Phase 1: Triage (0–20 minutes)

The goal of triage is to understand the scope and impact of the incident as quickly as possible, not to find the root cause.

1. IC confirms severity classification based on Section 2 criteria. Adjust up or down based on evidence — do not anchor to the initial classification if evidence contradicts it.
2. Tech Lead checks the four key observability signals: Grafana dashboards, application logs in OpenSearch, Kafka consumer lag dashboard, and recent deployments in ArgoCD.
3. IC asks: "Is there a mitigation available right now that reduces customer impact, even if it doesn't solve the root cause?" Common mitigations: feature flag off (via LaunchDarkly), rolling back the most recent deployment, scaling up replicas, redirecting traffic.
4. If a mitigation is available, apply it immediately. Document the action in the incident channel. Do not wait for root cause analysis before applying safe mitigations.
5. IC assigns all roles (Tech Lead, Comms Lead, Scribe) and confirms everyone knows their responsibilities.
6. Comms Lead posts the first status page update within 30 minutes of P1 declaration (15 minutes for outright unavailability).

### Phase 2: Diagnosis (20 minutes – resolution)

The goal of diagnosis is to find the root cause and implement a durable fix or mitigation.

1. Tech Lead forms hypotheses based on observability data. Document each hypothesis in the incident channel before testing.
2. Test one hypothesis at a time. If a change is made in production to test a hypothesis, it must be announced in the incident channel before execution with the expected outcome.
3. IC enforces a **20-minute timebox** on hypothesis investigation. If a hypothesis cannot be confirmed or eliminated within 20 minutes, move to the next hypothesis and loop back.
4. If the Tech Lead is stuck for more than 30 minutes, IC escalates additional engineers or external expertise per Section 7.
5. All commands run in production must be logged in the incident channel thread in real time by the Scribe.

### Phase 3: Resolution

An incident is resolved when the service has returned to its normal operating state and the IC is confident that the issue is not likely to recur immediately.

**Resolution checklist:**
- [ ] SLO metrics have returned to within normal bounds in Grafana.
- [ ] No new error spikes in OpenSearch logs in the 10 minutes prior to resolution call.
- [ ] Synthetic monitoring checks are passing from all regions.
- [ ] Any temporary mitigations (feature flags, manual scaling) are either confirmed as permanent or have a tracked follow-up to revert them.
- [ ] Comms Lead has drafted the resolution notification.

IC formally declares the incident resolved by posting in `#incidents`: `"RESOLVED — #inc-[channel-name] — [Brief resolution description] — Duration: [HH:MM]"`

### Phase 4: Post-Incident (within 5 business days)

Every P1 and P2 incident requires a written post-incident review (PIR). P3 incidents require a PIR if they recurred within 30 days or if the Tech Lead believes the root cause warrants documentation. See Section 9 for the full PIR process.

---

## 6. Communication Standards

### 6.1 Internal Communication Norms

- All incident-related communication must happen in the dedicated incident Slack channel. No critical incident information in DMs.
- Status updates in the incident channel every **15 minutes** during active P1 incidents, every **30 minutes** during P2.
- Use plain language. Avoid jargon when the Comms Lead needs to translate for external communications.
- Do not speculate about root cause in customer-facing communications until confirmed.
- If you need to run a command or make a change in production, announce it in the channel *before* you run it.

### 6.2 Incident Status Message Template

Post this template at incident declaration and update it in-place throughout the incident:

```
🚨 INCIDENT STATUS
Severity: [P1 / P2 / P3]
Product(s) affected: [InsightDash / StreamAPI / DataLake Pro / Internal]
Customer impact: [Description of visible impact]
Status: [Investigating / Identified / Mitigated / Monitoring / Resolved]
IC: [Name]
Tech Lead: [Name(s)]
Comms Lead: [Name]
Scribe: [Name]
Started: [HH:MM UTC]
Last updated: [HH:MM UTC]
Next update: [HH:MM UTC]
Current hypothesis: [One sentence]
Actions taken: [Bullet list of actions with timestamps]
```

### 6.3 Customer Communication Templates

**Initial notification (P1, within 30 minutes):**

> We are currently investigating an issue affecting [Product]. Some customers may be experiencing [brief description of symptoms]. Our engineering team is actively working to resolve this. We will provide an update within 60 minutes. We apologize for the inconvenience and will share a full post-incident report once the issue is resolved.

**Resolution notification:**

> The issue affecting [Product] has been resolved as of [HH:MM UTC]. [One sentence describing what was affected and how it was resolved.] We are conducting a full post-incident review and will share a summary with affected customers within 3 business days. We apologize for the disruption.

All customer communications are reviewed by the Comms Lead and, for P1 incidents, approved by Priya Nair before sending.

### 6.4 Status Page

The public status page at `status.xyzanalytics.com` is managed via Statuspage.io. The Comms Lead has access to post updates. Status must be updated:
- Within **30 minutes** of a P1 declaration.
- Every **60 minutes** during an active P1 incident.
- Immediately upon resolution.
- P2 incidents: update status page only if the incident is customer-visible.

---

## 7. Escalation Procedures

### 7.1 When to Escalate

Escalate to the next level when:
- The incident has not been mitigated within the resolution SLA for its severity.
- The root cause is unknown after 45 minutes of diagnosis on a P1.
- The fix requires resources, permissions, or expertise not available in the current response team.
- The incident involves a security breach (always escalate to Aisha Patel and James Okafor immediately).
- The incident involves potential data loss (always escalate to Laura Hensley and James Okafor).

### 7.2 Escalation Path

| Level | Contact            | When to Escalate                              | How                         |
|-------|--------------------|-----------------------------------------------|-----------------------------|
| L1    | DevOps On-Call     | Initial response (auto-paged by PagerDuty)    | PagerDuty auto-page         |
| L2    | Aisha Patel        | P1 unmitigated >20 min, security incidents    | PagerDuty + direct Slack    |
| L3    | Daniel Cruz        | P1 unmitigated >45 min, infrastructure crisis | PagerDuty + direct call     |
| L4    | James Okafor (CTO) | P1 unmitigated >1 hour, data breach, major outage | Direct call (any hour)  |
| L5    | Sarah Mitchell     | Customer-impacting P1 >2 hours, media/PR risk | James Okafor notifies       |

---

## 8. Product-Specific Runbooks

### 8.1 InsightDash Incident Quick Reference

**Common P2 triggers and first actions:**
- **Dashboard load timeout:** Check Redis cache hit rate in Grafana → Check query-engine pod health → Check RDS connection pool → See DEVOPS-RUN-001 Section 6.1.
- **Export service failures:** Check export-service pods for OOM events → Review S3 write permissions → Check recent deployment in ArgoCD.
- **Authentication failures (post-TECH-66 migration):** Check unified auth service health → Check Okta API status → Fallback: coordinate with Fatima Al-Hassan for emergency SAML bypass.

**Key engineers:** Tom Nguyen, Arjun Mehta, Elena Romero (Engineering); Lucia Ferreira (DevOps).

### 8.2 StreamAPI Incident Quick Reference

**Common P1/P2 triggers and first actions:**
- **Kafka consumer lag spike:** Check consumer pod health → Check broker metrics → Review DLQ backlog (TECH-25) → See DEVOPS-RUN-001 Section 9.2. Historical reference: the WebSocket instability incident (TECH-22) which caused mass connection drops at >5,000 concurrent clients — documented in post-incident report INC-2024-047.
- **Backpressure event:** Do not disable backpressure (TECH-34) — see DEVOPS-RUN-001 Section 9.3. Identify slow consumer group and coordinate with customer engineering team.
- **Event delivery latency spike:** Check consumer gateway pods → Review JWT refresh service (TECH-24) → Check downstream API response times.

**Key engineers:** Fatima Al-Hassan, Kevin Zhao, Ryan Park (Engineering); Raj Iyer, Aisha Patel (DevOps).

### 8.3 DataLake Pro Incident Quick Reference

**Common P2 triggers and first actions:**
- **Pipeline SLA breach:** Navigate to Airflow UI → Check failed tasks → Review Great Expectations suite output → Notify Data Steward before retrying Tier 3/4 pipelines. See DEVOPS-RUN-001 Section 10.2.
- **Snowflake connectivity failure:** Check Snowflake status page → Check VPN connectivity → Check IP allowlist via Terraform state (TECH-59) → Contact Raj Iyer.
- **Data quality validation failure:** Data is quarantined — do not force-merge. Notify Nadia Kowalski or Samuel Osei for steward review before any retry.

**Key engineers:** Mei Lin, Nadia Kowalski, Samuel Osei (Data); Omar Shaikh, Hannah Brooks (DevOps).

---

## 9. Post-Incident Review Process

The Post-Incident Review (PIR) is the most important part of the incident management process. It is where XYZ Analytics learns from failure and prevents recurrence. It is always blameless — the goal is to understand the system, not to assign fault to individuals.

### 9.1 PIR Timeline

| Activity                          | Timeline                         | Owner            |
|-----------------------------------|----------------------------------|------------------|
| Scribe exports incident log       | Within 2 hours of resolution     | Scribe           |
| PIR document drafted              | Within 2 business days           | IC               |
| PIR review meeting scheduled      | Within 5 business days           | IC               |
| PIR review meeting held           | Within 5 business days           | IC + full team   |
| Action items logged in Jira       | Same day as PIR meeting          | IC               |
| PIR published to internal wiki    | Within 1 business day of meeting | IC               |

### 9.2 PIR Document Structure

Every PIR must address the following sections:

1. **Incident summary:** Severity, duration, products affected, customer impact (number of customers, revenue impact if known).
2. **Timeline:** Minute-by-minute account from first detection to resolution, drawn from the Scribe's log.
3. **Root cause analysis:** The actual technical cause of the incident. Use the "5 Whys" technique to trace surface symptoms back to the underlying failure mode.
4. **Contributing factors:** System design decisions, process gaps, tooling limitations, or external factors that contributed to the incident or made it harder to resolve.
5. **What went well:** Aspects of the detection, response, or communication that worked effectively. These are worth preserving.
6. **What went poorly:** Aspects of the response that slowed resolution, created confusion, or caused unnecessary customer impact.
7. **Action items:** Concrete, assigned, Jira-tracked improvements to prevent recurrence or improve future response. Each action item must have an owner and a due date.

### 9.3 PIR Meeting Norms

- PIR meeting is attended by the full incident response team plus relevant Engineering and Data leads.
- Meeting is facilitated by the IC, with Daniel Cruz or Aisha Patel as a neutral observer for P1 incidents.
- The Scribe presents the timeline. The IC leads the root cause discussion.
- Action items are agreed upon before the meeting ends. Vague action items ("investigate X") are not acceptable — each item must be a specific, implementable change.
- Meeting notes and action items are logged in Notion under `Engineering > Post-Incident Reviews > [Year]`.

### 9.4 Blameless Culture

XYZ Analytics is committed to a blameless incident culture. This means:

- Individuals are not blamed for incidents. Systems fail, processes fail, and designs fail. People operate in the context of those systems.
- It is safe to escalate early, declare incidents conservatively, and ask for help without fear of criticism.
- Engineers who raise concerns about system reliability are celebrated, not questioned.
- Post-mortems focus on fixing systems and processes. If the conclusion of a PIR is that "the engineer should have known better," the PIR is incomplete.

---

## 10. Incident Metrics & Reporting

The following metrics are tracked for all incidents and reviewed monthly by Aisha Patel and Daniel Cruz, and quarterly by the executive team:

- **Mean Time to Detect (MTTD):** Average time from incident start to detection (alert firing or customer report). Target: <5 minutes for P1 (automated alerting).
- **Mean Time to Acknowledge (MTTA):** Average time from PagerDuty page to engineer acknowledgement. Target: <15 minutes (P1/P2).
- **Mean Time to Mitigate (MTTM):** Average time from detection to customer impact being mitigated (not necessarily root cause resolved). Target: <30 minutes (P1).
- **Mean Time to Resolve (MTTR):** Average time from detection to full resolution. Target: <2 hours (P1), <8 hours (P2).
- **Incident recurrence rate:** Percentage of incidents that recur within 30 days due to the same root cause. Target: <10%.
- **PIR completion rate:** Percentage of P1/P2 incidents with a published PIR within 5 business days. Target: 100%.

Monthly incident reports are prepared by Raj Iyer using InsightDash and distributed to the engineering leadership team. The report includes incident count by severity and product, MTTD/MTTA/MTTM/MTTR trends, top recurring root causes, and action item completion rates from prior PIRs.

---

## 11. Runbook Integration

This SOP governs the *process* of incident management. For the specific *commands and technical procedures* used during incident response, engineers refer to the **DevOps Runbook (DEVOPS-RUN-001)**. Key runbook sections relevant to incident response:

- Section 6 — Common runbook procedures (pod restarts, rollbacks, scaling).
- Section 9 — Kafka & Streaming operations (consumer lag, backpressure).
- Section 10 — Airflow & Pipeline operations (stuck DAG investigation).
- Section 11 — Disaster recovery procedures (DR activation criteria and initial steps).

If a procedure is needed during an incident and does not exist in DEVOPS-RUN-001, the Tech Lead should document it in the incident channel. The IC is responsible for ensuring it is added to DEVOPS-RUN-001 as a post-incident action item.

---

## 12. SOP Review & Maintenance

This SOP is reviewed after every P1 incident and formally revised quarterly. Proposed changes are submitted as PRs against the `xyz-knowledge-base` repository by any team member. Changes require approval from Aisha Patel and Daniel Cruz.

The following reviews are mandatory triggers for SOP revision:
- Any P1 incident where this SOP was not followed and the deviation contributed to delayed resolution.
- Any change to on-call tooling (PagerDuty, Grafana, Slack) that affects the procedures herein.
- Any organizational change that affects incident roles (e.g., team structure changes, new product launches).

---

## 13. Revision History

| Version | Date       | Author          | Summary                                              |
|---------|------------|-----------------|------------------------------------------------------|
| 1.0     | 2023-06-15 | Daniel Cruz     | Initial incident management SOP                      |
| 1.1     | 2023-10-22 | Aisha Patel     | Added P1/P2 customer communication templates         |
| 1.2     | 2024-02-11 | Raj Iyer        | Incident metrics section, PIR timeline formalized    |
| 1.3     | 2024-06-30 | Lucia Ferreira  | StreamAPI quick reference updated post TECH-22       |
| 1.4     | 2024-10-18 | Omar Shaikh     | DataLake Pro runbook, OpenSearch SIEM integration    |
| 1.5     | 2025-02-05 | Aisha Patel     | Blameless culture section, TECH-66 auth failover added |
