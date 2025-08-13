import json
import os
import boto3
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
table_name = os.environ['TABLE_NAME']
bucket_name = os.environ['BUCKET_NAME']
table = dynamodb.Table(table_name)

def handler(event, context):
    """
    Generates a weekly summary report of blood pressure readings.
    """
    try:
        # --- Calculate Date Range for the Past Week ---
        today = datetime.utcnow()
        one_week_ago = today - timedelta(days=7)
        
        # Scan can be inefficient. For production, consider a GSI on the date.
        # However, for this project, a scan is acceptable.
        response = table.scan()
        all_items = response.get('Items', [])

        # Filter items for the last week
        weekly_readings = []
        for item in all_items:
            # Assuming 'reading_datetime' is a string in 'DD-MM-YYYY HH:MM' format
            reading_date = datetime.strptime(item['reading_datetime'], '%d-%m-%Y %H:%M')
            if one_week_ago <= reading_date <= today:
                weekly_readings.append(item)

        total_weekly_readings = len(weekly_readings)

        # --- Generate Report Content ---
        report_date = today.strftime('%Y-%m-%d')
        report_content = f"Weekly Blood Pressure Summary Report\n"
        report_content += f"Report for week ending: {report_date}\n"
        report_content += f"-----------------------------------------\n"
        report_content += f"Total readings in the past 7 days: {total_weekly_readings}\n"

        # --- Upload Report to S3 ---
        report_key = f"weekly_summary_{report_date}.txt"

        s3.put_object(
            Bucket=bucket_name,
            Key=report_key,
            Body=report_content.encode('utf-8')
        )

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Weekly report generated successfully',
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
