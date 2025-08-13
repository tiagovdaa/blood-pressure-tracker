import json
import os
import uuid
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)

def handler(event, context):
    """
    Handles POST requests to store a new blood pressure reading.
    """
    try:
        body = json.loads(event['body'])
        
        # --- Input Validation ---
        required_fields = ['reading_datetime', 'systole', 'dystole']
        if not all(field in body for field in required_fields):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required fields'})
            }

        reading_datetime_str = body['reading_datetime']
        systole = body['systole']
        dystole = body['dystole']

        # Validate datetime format
        try:
            datetime.strptime(reading_datetime_str, '%d-%m-%Y %H:%M')
        except ValueError:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': "Invalid datetime format. Use 'DD-MM-YYYY HH:MM'"})
            }

        # Validate numeric types
        if not isinstance(systole, int) or not isinstance(dystole, int):
             return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Systole and dystole must be integers'})
            }

        # --- Store in DynamoDB ---
        reading_id = str(uuid.uuid4())
        
        table.put_item(
            Item={
                'reading_id': reading_id,
                'reading_datetime': reading_datetime_str,
                'systole': systole,
                'dystole': dystole,
                'timestamp': datetime.utcnow().isoformat()
            }
        )

        return {
            'statusCode': 201,
            'body': json.dumps({'message': 'Reading stored successfully', 'reading_id': reading_id})
        }

    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid JSON in request body'})
        }
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
