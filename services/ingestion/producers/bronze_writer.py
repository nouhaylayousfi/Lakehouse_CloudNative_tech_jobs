import json
import os
from datetime import datetime, timezone

from services.ingestion.producers.minio_client import get_minio_client

def write_to_bronze(data: dict | list , source: str) -> str:
    bucket = os.getenv("MINIO_BUCKET")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    key = f"bronze/{source}/{source}_{timestamp}.json"

    client = get_minio_client()
    client.put_object(
        Bucket= bucket,
        Key=key,
        Body=json.dumps(data , ensure_ascii=False , indent=2).encode('utf-8'),
        ContentType="application/json",
    )

    return key