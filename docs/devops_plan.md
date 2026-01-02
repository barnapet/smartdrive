# DevOps & Infrastructure Plan (IaC)

**Version:** 1.3
**Date:** Jan 2026
**Project:** SmartDrive OBD-II Data Platform & Ecosystem
**Focus:** CI/CD Pipelines, Infrastructure Strategy, and Cloud Observability
**Author:** Peter Barna
**Status:** Validated for v1.3 Battery Logic (11.5V / 10Hz)

---

## 1. CI/CD Pipeline (Continuous Integration & Delivery)
The primary objective is to automate the software lifecycle, ensuring that every code change is validated through rigorous testing before reaching the production environment.

### 1.1 Pipeline Workflow (GitHub Actions)


1.  **Code Push:** A developer pushes a new feature or fix to the `main` branch.
2.  **Linting & Static Analysis:** The system automatically checks for code quality and security vulnerabilities (e.g., using Flake8 for Python or SonarQube).
3.  **Unit & Logic Testing:** **(v1.3 Update)** Automated execution of test cases validating the **11.5V Vampire Drain cut-off** and the **Ignition-priority sampling trigger**.
4.  **Infrastructure Validation:** The CI environment runs a "Plan" phase to preview changes to the cloud resources.
5.  **Automated Deployment:** Once all tests pass, the system updates the AWS Lambda functions and synchronizes the cloud environment.

---

## 2. Infrastructure as Code (IaC) Strategy
Instead of manual configuration, the entire infrastructure is managed through code. This ensures that the environment is **reproducible, version-controlled, and consistent**.



### 2.1 Key Infrastructure Modules
* **Network Layer:** Management of VPCs, subnets, and security groups to isolate the database from the public internet.
* **Storage Layer:** Provisioning S3 buckets for the Medallion architecture (Bronze, Silver, and Gold data lakes).
* **Compute Layer:** Configuration of Serverless AWS Lambda functions, including memory allocation, execution timeouts, and environment variables.
* **Security & IAM:** Definition of Identity and Access Management (IAM) roles, ensuring each component operates under the **"Principle of Least Privilege."**

### 2.2 Terraform Code Example (S3 Bucket)
```hcl
resource "aws_s3_bucket" "data_lake_bronze" {
  bucket = "smartdrive-telemetry-bronze"
  
  tags = {
    Project     = "SmartDrive"
    Environment = "Production"
    Layer       = "Bronze"
  }
}
```

---

## 3. Observability & Monitoring
To maintain a 99.9% availability target, the system implements deep observability across all cloud layers.



### 3.1 Monitoring Pillars (AWS CloudWatch)
* **Logging:** Centralized storage of execution logs for all Lambda functions and MQTT message ingestion events.
* **Real-time Metrics:**
    * **Throughput:** Monitoring the number of telemetry packets processed per second.
    * **Latency:** Tracking the response time of the REST API (Target: $p95 < 2s$).
    * **Success Rate:** Monitoring the ratio of successful vs. failed data processing events.
* **Smart Alerting:** Automatic notifications (via Slack or Email) are triggered if the system detects an error rate exceeding 1% or if a database reaches critical capacity.

---

## 4. DevSecOps & Security
Security is treated as a continuous process integrated directly into the infrastructure management.

* **Secrets Management:** Sensitive information, such as database credentials and third-party API keys, is stored exclusively in **AWS Secrets Manager**, never in the source code.
* **Encryption Standards:**
    * **At Rest:** Mandatory AES-256 encryption for all data stored in S3 buckets and PostgreSQL databases.
    * **In Transit:** Secure communication between the mobile app and the cloud via **TLS 1.3** and encrypted MQTT channels.
* **Identity Management:** All user access is governed by JSON Web Tokens (JWT) with mandatory expiration and refresh logic.

---
