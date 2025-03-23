import  os
import sys
## Settings to allow imports from another folder or packages
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.join(current_dir, '..')
sys.path.append(root_dir)
import urllib.parse
from sqlalchemy import create_engine
import psycopg2
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from fastapi import HTTPException
from dotenv import load_dotenv
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_NAME = os.getenv("DB_NAME")
PORT = os.getenv("PORT")
REGION = os.getenv("REGION")

# IAM Role or Credentials
def generate_iam_auth_token():
    """Generate IAM auth token using boto3 for PostgreSQL Aurora"""
    try:
        client = boto3.client('rds', region_name=REGION)
        print("Generating token")
        token = client.generate_db_auth_token(
            DBHostname=DB_HOST, Port=PORT, DBUsername=DB_USER, Region=REGION
        )
        print("Generated token: ", token)
        return token
    except (NoCredentialsError, PartialCredentialsError) as e:
        print("AWS credentials not found. Please configure your AWS credentials.")
        raise HTTPException(status_code=500, detail=f"{str(e)}")


## Connection to the structured database
def connect_to_postgres_db():
    """Connect to PostgreSQL Aurora with IAM authentication for structured data"""
    conn = None
    try:
        token = "admin123"
        print(token)
        conn = psycopg2.connect(
            host=DB_HOST,
            user=DB_USER,
            password=token,
            dbname=DB_NAME,
            port=PORT,
            # sslmode='require',
        )
        print("Structured database connection successful")
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error: {error}")
    return conn


## Connection to the vector database for embeddings
def connect_to_postgres_vector_db():
    """Connect to the PostgreSQL vector database (pgvector)"""
    try:
        token = "admin123"
        encoded_token = urllib.parse.quote(token)
        db_url = f"postgresql://{DB_USER}:{encoded_token}@{DB_HOST}:{PORT}/{DB_NAME}"
        
        print(db_url)
        

        engine = create_engine(db_url)
        print("Vector database connection successful")
        return engine
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
connect_to_postgres_db()