import json
import boto3
import os
from datetime import datetime, timedelta

s3 = boto3.client('s3')
sagemaker = boto3.client('sagemaker')
dynamodb = boto3.resource('dynamodb')

BUCKET = os.environ.get('ML_BUCKET', 'mihogar-ml-data')
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'mihogar-sensor-events')
PIPELINE_NAME = os.environ.get('PIPELINE_NAME', 'mihogar-lighting-optimization')


def handler(event, context):
    """
    Cron mensual (EventBridge rule, día 1 de cada mes).

    1. Exporta últimos 30 días de DynamoDB a S3 (formato Parquet/JSON)
    2. Dispara pipeline de SageMaker

    El pipeline:
      - Limpia los datos (Processing Job)
      - Entrena modelo de patrones de uso (Training Job)
      - Genera perfiles por casa/zona (Batch Transform)
      - Escribe resultados en S3
      - Otra Lambda lee los resultados y los mete en perfiles_sagemaker (RDS)
    """
    now = datetime.utcnow()
    month_key = now.strftime('%Y-%m')
    prefix = f"training-data/{month_key}/"

    table = dynamodb.Table(TABLE_NAME)
    thirty_days_ago = (now - timedelta(days=30)).isoformat() + 'Z'

    # Export data from DynamoDB to S3
    # In production, use DynamoDB Export to S3 (native feature) for large datasets
    # Here we do a simplified scan for demo purposes
    exported = 0

    try:
        # For production: use boto3 dynamodb export_table_to_point_in_time
        # For now: scan + write JSON Lines to S3
        response = table.scan(
            FilterExpression='#ts >= :since',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={':since': thirty_days_ago},
        )

        items = response.get('Items', [])
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression='#ts >= :since',
                ExpressionAttributeNames={'#ts': 'timestamp'},
                ExpressionAttributeValues={':since': thirty_days_ago},
                ExclusiveStartKey=response['LastEvaluatedKey'],
            )
            items.extend(response.get('Items', []))

        if items:
            # Convert Decimal to float for JSON serialization
            def decimal_default(obj):
                if isinstance(obj, type(items[0].get('consumo_watts', 0))):
                    return float(obj)
                raise TypeError

            # Write as JSON Lines
            body = '\n'.join(json.dumps(item, default=decimal_default) for item in items)
            s3.put_object(
                Bucket=BUCKET,
                Key=f"{prefix}sensor_events.jsonl",
                Body=body.encode('utf-8'),
                ContentType='application/jsonlines',
            )
            exported = len(items)

    except Exception as e:
        print(f"[sagemaker_trigger] Export error: {e}")
        return {'statusCode': 500, 'error': str(e)}

    if exported == 0:
        print("[sagemaker_trigger] No data to export, skipping pipeline")
        return {'statusCode': 200, 'exported': 0, 'pipeline': 'skipped'}

    # Trigger SageMaker Pipeline
    try:
        response = sagemaker.start_pipeline_execution(
            PipelineName=PIPELINE_NAME,
            PipelineParameters=[
                {'Name': 'InputDataUri', 'Value': f's3://{BUCKET}/{prefix}'},
                {'Name': 'TrainingMonth', 'Value': month_key},
                {'Name': 'OutputUri', 'Value': f's3://{BUCKET}/ml-results/{month_key}/'},
            ],
            PipelineExecutionDescription=f"Monthly training run for {month_key}",
        )
        pipeline_arn = response['PipelineExecutionArn']
        print(f"[sagemaker_trigger] Pipeline started: {pipeline_arn}")

    except Exception as e:
        print(f"[sagemaker_trigger] Pipeline error: {e}")
        return {'statusCode': 500, 'exported': exported, 'error': str(e)}

    return {
        'statusCode': 200,
        'exported': exported,
        'pipeline_execution': pipeline_arn,
    }
