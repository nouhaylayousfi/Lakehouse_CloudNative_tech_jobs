import os 
import boto3
from botocore.client import Config 


def get_minio_client():
    return boto3.client(
        "s3",
        endpoint_url= os.getenv("MINIO_ENDPOINT"),
        aws_access_key_id=os.getenv("MINIO_ROOT_USER"),
        aws_secret_access_key=os.getenv("MINIO_ROOT_PASSWORD"),
        config=Config(signature_version="s3v4"),
    )