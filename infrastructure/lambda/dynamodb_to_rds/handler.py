import json
import boto3
import psycopg2
import os
from datetime import datetime, timedelta
from decimal import Decimal

DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'mihogar-sensor-events')
RDS_HOST = os.environ['RDS_HOST']
RDS_DB = os.environ.get('RDS_DB', 'mihogar')
RDS_USER = os.environ.get('RDS_USER', 'mihogar_admin')
RDS_PASSWORD = os.environ['RDS_PASSWORD']


def handler(event, context):
    """
    Cron cada hora (EventBridge rule).
    Lee los últimos 60 min de DynamoDB y actualiza consumo_diario en RDS.
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(DYNAMODB_TABLE)

    conn = psycopg2.connect(
        host=RDS_HOST,
        dbname=RDS_DB,
        user=RDS_USER,
        password=RDS_PASSWORD,
    )

    now = datetime.utcnow()
    one_hour_ago = (now - timedelta(hours=1)).isoformat() + 'Z'
    today = now.strftime('%Y-%m-%d')

    cur = conn.cursor()

    # Get all active casas
    cur.execute("SELECT id FROM casas WHERE activa = true")
    casas = [str(row[0]) for row in cur.fetchall()]

    total_processed = 0

    for casa_id in casas:
        # Query DynamoDB for last hour
        try:
            response = table.query(
                KeyConditionExpression='casa_id = :cid AND #sk >= :since',
                ExpressionAttributeNames={'#sk': 'timestamp#zona_id'},
                ExpressionAttributeValues={
                    ':cid': casa_id,
                    ':since': one_hour_ago,
                }
            )
        except Exception as e:
            print(f"[dynamodb_to_rds] Error querying casa {casa_id}: {e}")
            continue

        # Group consumption by zona
        zona_data = {}
        for item in response.get('Items', []):
            zona_id = item['zona_id']
            watts = float(item.get('consumo_watts', 0))
            encendida = item.get('estado_luz') == 'encendida'

            if zona_id not in zona_data:
                zona_data[zona_id] = {'total_watts': 0, 'readings': 0, 'on_readings': 0}

            zona_data[zona_id]['total_watts'] += watts
            zona_data[zona_id]['readings'] += 1
            if encendida:
                zona_data[zona_id]['on_readings'] += 1

        # Upsert in consumo_diario
        for zona_id, data in zona_data.items():
            if data['readings'] == 0:
                continue

            avg_watts = data['total_watts'] / data['readings']
            kwh_increment = avg_watts / 1000  # 1 hour period
            hours_on = data['on_readings'] / max(data['readings'], 1)

            cur.execute("""
                INSERT INTO consumo_diario (zona_id, casa_id, fecha, kwh_total, horas_encendido)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (zona_id, fecha)
                DO UPDATE SET
                    kwh_total = consumo_diario.kwh_total + EXCLUDED.kwh_total,
                    horas_encendido = consumo_diario.horas_encendido + EXCLUDED.horas_encendido
            """, (zona_id, casa_id, today, kwh_increment, hours_on))

            total_processed += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"[dynamodb_to_rds] casas={len(casas)} zonas_updated={total_processed}")
    return {'statusCode': 200, 'casas': len(casas), 'zonas_updated': total_processed}
