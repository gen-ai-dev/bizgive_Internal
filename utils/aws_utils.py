import  os
import sys

## Settings to allow imports from another folder or packages
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.join(current_dir, '..')
sys.path.append(root_dir)
import boto3
import tempfile
from utils.common_utils import read_json_file
from fastapi import HTTPException
from dotenv import load_dotenv
load_dotenv()

def get_s3_resources():
    s3_resource = boto3.resource(
        service_name="s3",
        region_name=os.getenv("AWS_DEFAULT_REGION"),
        aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_session_token = os.getenv("AWS_SESSION_TOKEN")
    )
    return s3_resource

def get_s3_client():
    s3_client = boto3.client(
        service_name="s3",
        region_name=os.getenv("AWS_DEFAULT_REGION"),
        aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_session_token = os.getenv("AWS_SESSION_TOKEN")
    )
    return s3_client


def get_project_config(project_id):
    config_bucket_name = os.getenv("CONFIG_BUCKET_NAME")
    if config_bucket_name is None:
        raise HTTPException(status_code=500, detail="Config Bucket name not found in Environment Variables")
    s3_client = get_s3_client()
    s3_resource = get_s3_resources()
    config_bucket = s3_resource.Bucket(config_bucket_name)
    
    for obj in config_bucket.objects.filter():
        if obj.key.startswith(project_id+"_"):
            config = {}
            with tempfile.TemporaryDirectory() as temp_dir:
                file_path = f"{temp_dir}/{obj.key}"
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                s3_client.download_file(config_bucket_name, obj.key, file_path)
                config = read_json_file(file_path)
                print(config)
            return config
    raise HTTPException(status_code=404, detail=f"Config file for project ID '{project_id}' not found in bucket '{config_bucket_name}'")
