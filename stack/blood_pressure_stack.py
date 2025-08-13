from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_s3 as s3,
    aws_events as events,
    aws_events_targets as targets,
    RemovalPolicy,
    Duration
)
from constructs import Construct

class BloodPressureStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB Table for Blood Pressure Readings
        readings_table = dynamodb.Table(
            self, "BloodPressureReadings",
            partition_key=dynamodb.Attribute(
                name="reading_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY # NOT recommended for production
        )

        # S3 Bucket for Reports
        reports_bucket = s3.Bucket(
            self, "BloodPressureReports",
            removal_policy=RemovalPolicy.DESTROY, # NOT recommended for production
            auto_delete_objects=True
        )

        # Lambda Layer for Boto3 (if needed, often included in Lambda runtime)
        # For this example, we assume boto3 is available in the Python 3.8+ runtime.

        # Lambda Function to Post Readings
        post_reading_lambda = _lambda.Function(
            self, "PostReadingHandler",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda/post_reading"),
            handler="post_reading.handler",
            environment={
                "TABLE_NAME": readings_table.table_name
            }
        )

        # Grant Lambda permissions to write to DynamoDB
        readings_table.grant_write_data(post_reading_lambda)

        # Lambda Function for On-Demand Reports
        on_demand_report_lambda = _lambda.Function(
            self, "OnDemandReportHandler",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda/on_demand"), # <-- CORRECTED PATH
            handler="on_demand_report.handler",
            environment={
                "TABLE_NAME": readings_table.table_name,
                "BUCKET_NAME": reports_bucket.bucket_name
            },
            timeout=Duration.seconds(30)
        )

        # Grant Lambda permissions to read from DynamoDB and write to S3
        readings_table.grant_read_data(on_demand_report_lambda)
        reports_bucket.grant_write(on_demand_report_lambda)

        # Lambda Function for Weekly Reports
        weekly_report_lambda = _lambda.Function(
            self, "WeeklyReportHandler",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda/weekly_report"),
            handler="weekly_report.handler",
            environment={
                "TABLE_NAME": readings_table.table_name,
                "BUCKET_NAME": reports_bucket.bucket_name
            },
            timeout=Duration.seconds(60)
        )

        # Grant Lambda permissions to read from DynamoDB and write to S3
        readings_table.grant_read_data(weekly_report_lambda)
        reports_bucket.grant_write(weekly_report_lambda)

        # API Gateway
        api = apigw.LambdaRestApi(
            self, "BloodPressureApi",
            handler=post_reading_lambda, # Default handler
            proxy=False
        )

        # API Gateway resource for readings
        readings_resource = api.root.add_resource("readings")
        readings_resource.add_method("POST", apigw.LambdaIntegration(post_reading_lambda))

        # API Gateway resource for on-demand reports
        report_resource = api.root.add_resource("report")
        report_resource.add_method("POST", apigw.LambdaIntegration(on_demand_report_lambda))

        # EventBridge (CloudWatch Events) Rule for Weekly Report
        # Runs every Monday at 2:00 AM UTC
        rule = events.Rule(
            self, "WeeklyReportRule",
            schedule=events.Schedule.cron(minute='0', hour='2', week_day='MON'),
        )
        rule.add_target(targets.LambdaFunction(weekly_report_lambda))