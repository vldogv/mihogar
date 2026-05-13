import json
import boto3
import time
import os
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'mihogar-sensor-events')
table = dynamodb.Table(TABLE_NAME)

TTL_DAYS = 90


def handler(event, context):
    """
    Triggered by IoT Core Rule on topics:
      mihogar/{casa_id}/telemetry
      mihogar/{casa_id}/telemetry/batch

    Event format:
    {
      "casa_id": "b0000001-...",
      "timestamp": "2026-03-26T14:30:00Z",
      "lecturas": [
        {
          "zona_id": "d0000001-...",
          "luz_ambiente": 35,
          "movimiento": true,
          "temperatura": 24.5,
          "consumo_watts": 45.2,
          "estado_luz": "encendida"
        }
      ]
    }
    """
    casa_id = event.get('casa_id')
    timestamp = event.get('timestamp')
    lecturas = event.get('lecturas', [])

    if not casa_id or not timestamp:
        return {'statusCode': 400, 'error': 'Missing casa_id or timestamp'}

    ttl = int(time.time()) + (TTL_DAYS * 24 * 3600)
    written = 0

    with table.batch_writer() as batch:
        for lectura in lecturas:
            zona_id = lectura.get('zona_id')
            if not zona_id:
                continue

            sort_key = f"{timestamp}#{zona_id}"

            item = {
                'casa_id': casa_id,
                'timestamp#zona_id': sort_key,
                'zona_id': zona_id,
                'timestamp': timestamp,
                'ttl': ttl,
            }

            for field in ('luz_ambiente', 'temperatura', 'consumo_watts'):
                if field in lectura and lectura[field] is not None:
                    item[field] = Decimal(str(lectura[field]))

            if 'movimiento' in lectura:
                item['movimiento'] = lectura['movimiento']

            if 'estado_luz' in lectura:
                item['estado_luz'] = lectura['estado_luz']

            batch.put_item(Item=item)
            written += 1

    print(f"[iot_to_dynamodb] casa={casa_id} written={written}")
    return {'statusCode': 200, 'processed': written}
