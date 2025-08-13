# Serverless Blood Pressure Tracker

This project provides a serverless application to track blood pressure readings. It features an API to submit readings, a DynamoDB table to store them, an S3 bucket for reports, and Lambda functions for processing and generating weekly and on-demand summary reports. The entire infrastructure is defined using the AWS Cloud Development Kit (CDK) and is designed to be deployed via GitHub Actions.

## Architecture Diagram

Here is a high-level overview of the application's architecture:

* **API Gateway**: Provides two RESTful endpoints:
    * `POST /readings`: To submit a new blood pressure reading.
    * `POST /report`: To trigger an on-demand report generation.
* **AWS Lambda**: Three Python functions handle the application logic:
    * `post_reading_lambda`: Validates and stores new blood pressure readings in DynamoDB.
    * `on_demand_report_lambda`: Generates a summary report of all readings and saves it to S3.
    * `weekly_report_lambda`: Triggered by an Amazon EventBridge (CloudWatch Events) rule to run weekly, generating a report of the last 7 days' readings and saving it to S3.
* **Amazon DynamoDB**: A NoSQL database used to store the blood pressure readings.
* **Amazon S3**: An object storage service used to store the generated reports.
* **Amazon EventBridge**: A serverless event bus that triggers the weekly report generation.
* **GitHub Actions**: For CI/CD to deploy the AWS CDK stack.

## Detailed Setup Guide

Deploying this project involves a one-time setup in AWS to establish a trust relationship with GitHub Actions, followed by the deployment itself.

### Prerequisites

* An AWS Account.
* An IAM User in your AWS account with `AdministratorAccess` permissions for the initial setup.
* Python 3.8+ and pip.
* Node.js and npm.
* AWS CDK CLI: `npm install -g aws-cdk`
* Git.

---

### **Part 1: One-Time AWS Environment Setup**

This part creates the foundational resources and permissions needed for the pipeline to run securely.

#### **Step 1: Bootstrap the AWS Environment**

The CDK requires a set of resources (an S3 bucket, IAM roles) to manage deployments. This is a **one-time action per AWS account/region combination**.

1.  Configure your local machine with the credentials of an IAM user that has `AdministratorAccess`.
    ```bash
    aws configure
    ```
2.  From the project's root directory, run the bootstrap command:
    ```bash
    cdk bootstrap
    ```
    This creates a CloudFormation stack named `CDKToolkit` in your account.

#### **Step 2: Create the IAM OIDC Provider for GitHub**

This tells your AWS account to trust authentication tokens from GitHub Actions.

1.  In the AWS Console, navigate to the **IAM** service.
2.  Go to **Identity providers** and click **Add provider**.
3.  Select **OpenID Connect**.
4.  For **Provider URL**, enter `https://token.actions.githubusercontent.com`.
5.  Click **Get thumbprint**.
6.  For **Audience**, enter `sts.amazonaws.com`.
7.  Click **Add provider**.

#### **Step 3: Create the IAM Role for the Pipeline**

This role will be assumed by GitHub Actions to get temporary, secure credentials for deployment.

1.  In IAM, go to **Roles** and click **Create role**.
2.  For **Trusted entity type**, select **Web identity**.
3.  Choose the **Identity provider** you just created (`token.actions.githubusercontent.com`).
4.  For **Audience**, select `sts.amazonaws.com`.
5.  Under "GitHub organization," specify your repository to restrict which workflows can use this role (e.g., `your-github-username/blood-pressure-tracker`).
6.  Click **Next**.

#### **Step 4: Attach Permissions to the Role**

1.  On the "Add permissions" screen, click **Create policy**. This will open a new tab.
2.  In the policy editor, switch to the **JSON** tab and paste the following policy. **Remember to replace `YOUR_ACCOUNT_ID` with your actual AWS Account ID.**

    ```json
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "sts:AssumeRole",
                "Resource": "arn:aws:iam::YOUR_ACCOUNT_ID:role/cdk-*-*"
            },
            {
                "Effect": "Allow",
                "Action": "ssm:GetParameter",
                "Resource": "arn:aws:ssm:*:YOUR_ACCOUNT_ID:parameter/cdk-bootstrap/*"
            },
            {
                "Effect": "Allow",
                "Action": "cloudformation:DescribeStacks",
                "Resource": "*"
            }
        ]
    }
    ```
3.  Click **Next: Tags**, then **Next: Review**.
4.  Give the policy a name (e.g., `GitHubActions-CDK-Pipeline-Policy`) and click **Create policy**.
5.  Go back to the "Create role" browser tab. Refresh the list of policies and attach the policy you just created.
6.  **IMPORTANT:** Also attach the `AWSCloudFormationFullAccess` managed policy. This gives the role the necessary permissions to deploy the application's resources.
7.  Click **Next**.
8.  Give the role a name (e.g., `GitHubActions-Deploy-Role`), review the details, and click **Create role**.
9.  Click on the newly created role and copy its **ARN**. You will need this for the next step.

---

### **Part 2: GitHub Repository Setup**

#### **Step 1: Add Secrets to GitHub**

1.  In your GitHub repository, go to **Settings** > **Secrets and variables** > **Actions**.
2.  Click **New repository secret** and add the following:
    * **Name:** `AWS_ROLE_ARN`
        **Value:** The ARN of the IAM role you created in the previous step.
    * **Name:** `AWS_REGION`
        **Value:** Your AWS region (e.g., `eu-west-1`).

#### **Step 2: Deploy the Application**

1.  Clone the repository:
    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```
2.  Push your code to the `main` branch. The GitHub Actions workflow defined in `.github/workflows/deploy.yml` will automatically trigger, assume the IAM role, and deploy your CDK stack.

## Usage Instructions

### Submitting a Blood Pressure Reading

Send a `POST` request to the `/readings` endpoint URL provided in the CDK deployment output.

**Endpoint:** `https://<api-id>.execute-api.<region>.amazonaws.com/prod/readings`

**Method:** `POST`

**Body (JSON):**
```json
{
  "reading_datetime": "12-08-2025 14:45",
  "systole": 130,
  "dystole": 90
}
```

### Triggering an On-Demand Report

Send a `POST` request to the `/report` endpoint URL.

**Endpoint:** `https://<api-id>.execute-api.<region>.amazonaws.com/prod/report`

**Method:** `POST`

**Body:** (Empty)

This will generate a report named `on_demand_report_<timestamp>.txt` in your S3 bucket.

---

*created by Tiago Almeida @ Debian Linux 13*