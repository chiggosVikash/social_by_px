import boto3
from botocore.config import Config
from src.core.config import get_settings

settings = get_settings()

def get_s3_client():
    if not settings.CLOUDFLARE_R2_ACCESS_KEY_ID:
        return None
        
    return boto3.client(
        's3',
        endpoint_url=settings.CLOUDFLARE_R2_ENDPOINT_URL,
        aws_access_key_id=settings.CLOUDFLARE_R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.CLOUDFLARE_R2_SECRET_ACCESS_KEY,
        config=Config(signature_version='s3v4'),
        region_name='auto'
    )

def upload_file(file_data: bytes, file_name: str, content_type: str = "image/png") -> str:
    """Uploads a file to Cloudflare R2 and returns the public URL."""
    client = get_s3_client()
    if not client:
        # For local development without R2 configured
        return f"http://localhost:8000/static/{file_name}"
        
    bucket = settings.CLOUDFLARE_R2_BUCKET_NAME
    client.put_object(
        Bucket=bucket,
        Key=file_name,
        Body=file_data,
        ContentType=content_type
    )
    
    # Returning a generic URL structure; actual custom domain can be appended
    return f"{settings.CLOUDFLARE_R2_ENDPOINT_URL}/{bucket}/{file_name}"
