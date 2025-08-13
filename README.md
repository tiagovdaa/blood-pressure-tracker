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

### Prerequisites

* An AWS Account and configured AWS CLI credentials.
* Python 3.8+ and pip.
* Node.js and npm.
* AWS CDK CLI: `npm install -g aws-cdk`
* Git.

### Deployment Steps

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```

2.  **Set up a Python virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```

3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Bootstrap your AWS environment (if you haven't already):**
    This command provisions the initial resources needed by the CDK to deploy stacks.
    ```bash
    cdk bootstrap aws://ACCOUNT-ID/REGION
    ```
    Replace `ACCOUNT-ID` and `REGION` with your AWS Account ID and preferred region.

5.  **Deploy the CDK Stack:**
    ```bash
    cdk deploy
    ```
    The CDK will synthesize a CloudFormation template and deploy the resources. After deployment, it will output the API Gateway endpoint URLs.

### GitHub Actions Deployment (CI/CD)

This repository includes a GitHub Actions workflow (`.github/workflows/deploy.yml`) for automated deployments. To use it, you need to configure an OIDC provider in your AWS account to allow GitHub Actions to assume an IAM role.

1.  **Create an IAM OIDC Provider in AWS** for GitHub.
2.  **Create an IAM Role** that the GitHub Actions workflow can assume. This role needs permissions to deploy CloudFormation stacks and manage the resources defined in this project (Lambda, API Gateway, DynamoDB, S3).
3.  **Add the IAM Role ARN as a secret** in your GitHub repository with the name `AWS_ROLE_ARN`.
4.  **Add the AWS Region as a secret** with the name `AWS_REGION`.

With this configuration, any push to the `main` branch will trigger the workflow and deploy the application.

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

### Weekly Reports

The weekly report is generated automatically every Monday at 2 AM UTC. The report will be named `weekly_summary_<date>.txt` and will contain the count of readings from the previous week.

## Code Explanation

### `stack/blood_pressure_stack.py`

This file contains the core CDK code that defines all the AWS resources.
* It creates a **DynamoDB Table** with a primary key `reading_id` (a UUID).
* It creates an **S3 Bucket** to store reports.
* It defines three **Lambda Functions**:
    * `post_reading_lambda`: Receives data from the API Gateway, validates it, and stores it in DynamoDB.
    * `on_demand_report_lambda`: Fetches all records from DynamoDB, creates a summary, and uploads it to S3.
    * `weekly_report_lambda`: Fetches records from the last 7 days, creates a summary, and uploads it to S3.
* It sets up an **API Gateway** with two routes (`/readings` and `/report`) that integrate with the corresponding Lambda functions.
* It creates an **EventBridge Rule** to trigger the `weekly_report_lambda` on a schedule (`cron(0 2 ? * MON *)`).
* It grants the necessary **IAM Permissions** for the Lambda functions to access the DynamoDB table and the S3 bucket.

### `lambda/post_reading/post_reading.py`

This function handles the logic for storing a new reading.
1.  It receives the request body from API Gateway.
2.  It validates the presence and format of `reading_datetime`, `systole`, and `dystole`.
3.  It generates a unique `reading_id` using `uuid.uuid4()`.
4.  It uses the `boto3` library to put the item into the DynamoDB table.
5.  It returns a success or error response to the client.

### `lambda/on_demand_report/on_demand_report.py`

This function generates a report of all readings.
1.  It scans the entire DynamoDB table to get all readings.
2.  It calculates the total number of readings.
3.  It formats the summary into a string.
4.  It uploads this summary as a text file to the S3 bucket. The filename includes a timestamp to ensure uniqueness.

### `lambda/weekly_report/weekly_report.py`

This function generates a weekly summary.
1.  It calculates the date range for the last 7 days.
2.  It scans the DynamoDB table for readings within that date range.
3.  It counts the number of readings found.
4.  It formats the summary and uploads it to the S3 bucket with a filename indicating the week.
