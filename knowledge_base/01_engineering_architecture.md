---
document_id: ENG-ARCH-001
department: Engineering
owner: Daniel Cruz
reviewer: James Okafor
last_updated: 2025-03-15
version: 2.1
related_tickets: [TECH-08, TECH-22, TECH-66]
related_products: [InsightDash, StreamAPI, DataLake Pro]
related_docs: [SEC-ACCESS-001]
---

# XYZ Analytics — Engineering Architecture Document

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Product Architecture Breakdown](#product-architecture-breakdown)
4. [Cross-Product Infrastructure](#cross-product-infrastructure)
5. [Engineering Standards & Conventions](#engineering-standards--conventions)
6. [Dependency Management](#dependency-management)
7. [Performance & Scalability Guidelines](#performance--scalability-guidelines)
8. [Disaster Recovery & Resilience](#disaster-recovery--resilience)
9. [Team Ownership Map](#team-ownership-map)
10. [Open Architecture Decisions](#open-architecture-decisions)

---

## 1. Overview

This document defines the system architecture, technical standards, and infrastructure conventions governing all software products at XYZ Analytics. It is the canonical reference for architectural decisions made across the Engineering, DevOps, and Data teams, and is intended to be read in conjunction with the **Security & Access Control Policy (SEC-ACCESS-001)**.

**Document Owner:** Daniel Cruz, VP of Engineering
**Technical Reviewer:** James Okafor, CTO
**Last Architecture Review:** March 2025

XYZ Analytics operates three primary SaaS products — **InsightDash**, **StreamAPI**, and **DataLake Pro** — all of which share a common cloud substrate on AWS and a unified set of platform services. Each product is independently deployable but shares platform-level concerns including authentication, observability, and data governance.

The architecture follows a **microservices-first** philosophy, with individual services owning their data stores and exposing well-defined API contracts. Service communication within a product boundary is handled via internal REST or gRPC; cross-product communication flows through a shared internal event bus (Apache Kafka).

This document supersedes ENG-ARCH-000 (v1.8, authored by Tom Nguyen) and reflects the architectural decisions made during the Q1 2025 platform consolidation initiative led by Fatima Al-Hassan and Arjun Mehta.

---

## 2. System Architecture

### 2.1 High-Level Topology

XYZ Analytics infrastructure is hosted entirely on **Amazon Web Services (AWS)**, with primary deployment in `us-east-1` and disaster recovery replication in `us-west-2`. All production workloads run inside isolated Virtual Private Clouds (VPCs) per product, peered through a centralized Transit Gateway managed by the DevOps team under Aisha Patel's oversight.

The overall topology can be summarized as follows:

- **Ingress Layer:** AWS Application Load Balancer (ALB) with AWS WAF, managed via Terraform by Hannah Brooks and Omar Shaikh.
- **Compute Layer:** Amazon EKS (Kubernetes) clusters per product, with Horizontal Pod Autoscalers (HPA) configured per service. As noted in ticket **TECH-22**, the StreamAPI broker pods experienced Websocket connection instability at >5,000 concurrent clients — this was traced to misconfigured connection pool limits in the EKS node groups and has been resolved in v2.1 of this architecture.
- **Data Layer:** Amazon RDS (PostgreSQL) for transactional stores, Amazon S3 for object storage, and Snowflake for analytical workloads.
- **Messaging Layer:** Apache Kafka (MSK) for event streaming between products and between internal microservices.
- **CDN Layer:** Amazon CloudFront for static asset delivery across all three product frontends.

### 2.2 Network Segmentation

All environments (development, staging, production) are isolated in separate AWS accounts under the XYZ Analytics AWS Organization. Cross-account access is permitted only via assume-role patterns with MFA enforcement — detailed in **SEC-ACCESS-001**. No direct peering exists between production and development VPCs.

Production subnets are divided into:
- **Public subnets:** Load balancers and NAT gateways only. No application workloads.
- **Private application subnets:** All microservice pods, internal APIs, and worker processes.
- **Private data subnets:** RDS instances, ElastiCache clusters, and MSK brokers. Accessible only from application subnets.

---

## 3. Product Architecture Breakdown

### 3.1 InsightDash

InsightDash is the company's flagship Business Intelligence dashboard product. It is a full-stack web application with a React 18 frontend (migrated in **TECH-08** from React 17 by Arjun Mehta) and a Python/FastAPI backend.

**Frontend Architecture:**
The InsightDash frontend is built on React 18 using the concurrent rendering model. Webpack 5 handles bundling, with code splitting configured per-route to minimize initial bundle size. The component library is proprietary, built and maintained by Elena Romero and Zoe Hartman. All widget state is managed via Zustand; server state is managed via TanStack Query (React Query v5). A Redis-backed query cache layer (implemented in response to TECH-13) serves repeated dashboard queries within a 5-minute window, reducing database load by approximately 62% in load tests.

The frontend communicates exclusively with the InsightDash BFF (Backend for Frontend) layer — a lightweight FastAPI service that aggregates and transforms responses from downstream microservices before delivering them to the UI.

**Backend Microservices:**
The InsightDash backend is decomposed into the following services:

- `auth-service` — Handles session management, JWT issuance, and Okta SAML 2.0 SSO (implemented by Fatima Al-Hassan per TECH-10). Now being consolidated into the unified auth microservice tracked in **TECH-66**.
- `dashboard-service` — Manages dashboard CRUD, widget configuration, and sharing settings. Implements RBAC per TECH-04.
- `query-engine` — Routes and executes user-initiated queries against the semantic layer. Integrates with dbt models via the metric catalog (TECH-19).
- `export-service` — Handles CSV, PDF, and image export of dashboards. Known issue with pivot table CSV exports documented in TECH-03 (resolved in v2.1.1, verified by Tyler Moss).
- `notification-service` — Manages alert threshold notifications (TECH-12) via email and Slack webhook delivery.

**Data Store:**
InsightDash uses PostgreSQL 15 (Amazon RDS Multi-AZ) for its operational data (dashboard configs, user preferences, sharing policies). The metrics data powering charts and widgets is sourced entirely from DataLake Pro's Snowflake instance via the semantic layer.

### 3.2 StreamAPI

StreamAPI is XYZ Analytics' real-time event streaming API platform. It supports REST, WebSocket, and gRPC (in development, tracked under TECH-23) transport layers, enabling customers to subscribe to real-time event feeds with sub-second latency.

**Broker Layer:**
StreamAPI's core is built on Apache Kafka (AWS MSK). Each customer tenant is assigned a dedicated Kafka topic namespace. Topic management, schema validation, and consumer group configuration are handled by the `broker-service` — owned by Kevin Zhao and Ryan Park.

The Schema Registry (Confluent-compatible) enforces Avro and Protobuf schemas on all ingest paths (TECH-26). A dead letter queue (DLQ) has been implemented per TECH-25 to capture and replay failed event deliveries without data loss.

**Consumer Gateway:**
Customer-facing event subscriptions flow through the `consumer-gateway` service, which manages:
- WebSocket session lifecycle and connection pooling
- JWT refresh without re-authentication (TECH-24)
- Per-API-key rate limiting (TECH-28) with 429 response headers
- HMAC-SHA256 signature validation on all outbound webhook deliveries (TECH-35)

**Delivery Guarantees:**
StreamAPI offers at-least-once delivery by default, with exactly-once semantics available for enterprise-tier customers via idempotent producer configuration. Backpressure handling (TECH-34) ensures slow consumers do not overwhelm the broker — this is considered a critical architectural requirement given StreamAPI's multi-tenant design.

### 3.3 DataLake Pro

DataLake Pro is XYZ Analytics' managed data warehouse product, enabling customers to ingest, transform, and query large volumes of structured and semi-structured data. The platform is built on Apache Airflow for orchestration, Snowflake for the analytical storage layer, and Delta Lake for mutable staging tables (migrated per TECH-48 by Mei Lin).

The ingestion layer supports connectors for Salesforce (TECH-43), PostgreSQL, MySQL, S3, and a growing library of SaaS source connectors, each implemented as a modular Airflow operator. All pipelines are validated against Great Expectations suites (TECH-47, owned by Samuel Osei) before data lands in the curated layer.

---

## 4. Cross-Product Infrastructure

Several platform services are shared across all three products. These are owned by the Platform Engineering sub-team, comprising Tom Nguyen, Arjun Mehta, and Fatima Al-Hassan.

### 4.1 Unified Authentication Service (TECH-66)

As of Q1 2025, a project is underway (led by Fatima Al-Hassan) to consolidate per-product auth services into a single OAuth 2.0 + OIDC microservice. All three products will delegate token issuance and validation to this service. The Feature Flag Service (TECH-71) and the Security Penetration Test (TECH-72) are blocked on this work completing.

### 4.2 Observability Stack

A unified Grafana + Prometheus deployment (TECH-67) is maintained by Lucia Ferreira. All microservices across InsightDash, StreamAPI, and DataLake Pro emit metrics via the Prometheus client library. Alerting rules follow the runbook defined in **DevOps Runbook (DEVOPS-RUN-001)**. Centralized log aggregation into OpenSearch (TECH-68) is currently in review, owned by Omar Shaikh.

### 4.3 Feature Flag Service

LaunchDarkly is the designated feature flag platform (TECH-71). Rollout is pending completion of TECH-66 (unified auth), as feature flag evaluation requires a stable user identity context.

---

## 5. Engineering Standards & Conventions

The following standards apply to all engineering teams at XYZ Analytics. These are enforced via automated linting, CI checks, and quarterly architecture reviews chaired by Daniel Cruz.

### 5.1 API Design

- All public-facing APIs must conform to **OpenAPI 3.1** specifications. Auto-generation from code annotations is enforced for StreamAPI (TECH-30) and is being rolled out to InsightDash and DataLake Pro.
- Breaking API changes require a minimum 90-day deprecation notice and a versioned migration guide. The deprecation of StreamAPI v1 REST endpoints (TECH-33) serves as the current reference example.
- APIs must implement standard rate limiting, returning `429 Too Many Requests` with `Retry-After` headers.

### 5.2 Code Quality

- **Minimum unit test coverage: 80%.** Current InsightDash coverage is at 54% and being remediated by Tyler Moss per TECH-09.
- All code must pass lint checks (ESLint for TypeScript/React, Ruff for Python) before merging.
- Pull requests require a minimum of two approvals — at least one from a senior engineer and one from the relevant team lead.

### 5.3 Dependency Management

- All dependency upgrades must be proposed via a dedicated PR with updated test results.
- Node.js dependencies are managed via `npm` with lockfiles committed. Python dependencies use `pip-tools` for deterministic resolution.
- Security vulnerability scanning runs on every PR via Snyk. Critical CVEs block merge.

### 5.4 Secret Management

All secrets are stored in AWS Secrets Manager. No secrets in environment variables, configuration files, or source code. Rotation schedules are defined per secret type in SEC-ACCESS-001.

---

## 6. Performance & Scalability Guidelines

InsightDash dashboards must render within **3 seconds** at P95 for datasets up to 500,000 rows. For larger datasets, pagination and lazy loading are mandatory (TECH-01). The query cache (TECH-13) is the primary mechanism for meeting this SLA for repeated queries.

StreamAPI targets **<200ms P99 event delivery latency** for WebSocket subscribers under normal load. Under sustained peak load (>10,000 concurrent connections), the backpressure mechanism (TECH-34) is the primary protection against broker saturation.

A cross-product end-to-end latency audit (TECH-69) is currently in progress, led by Mei Lin, targeting <10 seconds P99 for the full Kafka → Snowflake → InsightDash pipeline.

---

## 7. Disaster Recovery & Resilience

All production databases use Multi-AZ RDS configurations with automated daily snapshots retained for 30 days. Snowflake Time Travel is enabled with a 14-day retention window for DataLake Pro tables. Cross-region replication of critical DataLake Pro datasets is planned per TECH-51, pending completion of the PII column-level encryption work (TECH-44).

Recovery Time Objective (RTO): **4 hours** for all production systems.
Recovery Point Objective (RPO): **1 hour** for transactional databases; **15 minutes** for Kafka topics (via MSK replication).

---

## 8. Team Ownership Map

| Product / Service         | Engineering Owner     | DevOps Owner       |
|---------------------------|-----------------------|--------------------|
| InsightDash Frontend      | Elena Romero          | Lucia Ferreira     |
| InsightDash Backend       | Arjun Mehta           | Lucia Ferreira     |
| StreamAPI Broker          | Kevin Zhao            | Aisha Patel        |
| StreamAPI Consumer GW     | Ryan Park             | Omar Shaikh        |
| DataLake Pro Ingestion    | Ryan Park             | Hannah Brooks      |
| DataLake Pro Transform    | (Data Team — Mei Lin) | Raj Iyer           |
| Unified Auth Service      | Fatima Al-Hassan      | Aisha Patel        |
| Observability Stack       | Tom Nguyen            | Lucia Ferreira     |

---

## 9. Open Architecture Decisions

The following decisions are currently under active discussion and have not yet been finalized:

- **ADR-014:** Whether to adopt Apache Iceberg (TECH-54) as the open table format for DataLake Pro alongside or in replacement of Delta Lake. Decision owner: Simone Dupont. Target decision date: April 2025.
- **ADR-015:** gRPC adoption scope for StreamAPI (TECH-23). Currently limited to StreamAPI — proposal to extend to internal microservice communication is under review by James Okafor.
- **ADR-016:** Multi-region active-active vs. active-passive for StreamAPI (TECH-27). Cost modelling underway by Raj Iyer and Aisha Patel.

---

## 10. Revision History

| Version | Date       | Author         | Summary                                  |
|---------|------------|----------------|------------------------------------------|
| 1.0     | 2023-06-01 | Tom Nguyen     | Initial architecture document            |
| 1.8     | 2024-09-12 | Tom Nguyen     | Added StreamAPI gRPC section (draft)     |
| 2.0     | 2025-01-20 | Daniel Cruz    | Platform consolidation — unified auth    |
| 2.1     | 2025-03-15 | Arjun Mehta    | React 18 migration, backpressure updates |
