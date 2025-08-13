import json
import os
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
table_name = os.environ['TABLE_NAME']
bucket_name = os.environ['BUCKET_NAME']
table = dynamodb.Table(table_name)

def handler(event, context):
    """
    Generates an on-demand report of all blood pressure readings.
    """
    try:
        # --- Scan DynamoDB Table ---
        response = table.scan()
        items = response.get('Items', [])
        
        # Handle pagination if the table is large
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))

        total_readings = len(items)

        # --- Generate Report Content ---
        report_content = f"On-Demand Blood Pressure Summary Report\n"
        report_content += f"Generated on: {datetime.utcnow().isoformat()}\n"
        report_content += f"-----------------------------------------\n"
        report_content += f"Total number of readings collected: {total_readings}\n"

        # --- Upload Report to S3 ---
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        report_key = f"on_demand_report_{timestamp}.txt"

        s3.put_object(
            Bucket=bucket_name,
            Key=report_key,
            Body=report_content.encode('utf-8')
        )

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'On-demand report generated successfully',
                's3_bucket': bucket_name,
                's3_key': report_key
            })
        }

    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
