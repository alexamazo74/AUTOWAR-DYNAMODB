"""
Report Storage S3 Operations
Provides helper functions for uploading reports and generating signed URLs
"""

import os
import boto3
from datetime import datetime, timedelta
from typing import Optional

# Initialize S3 client
s3_client = boto3.client('s3')
BUCKET_NAME = os.environ.get('REPORTS_BUCKET', '')


def upload_report(
    account_id: str,
    evaluation_timestamp: str,
    report_type: str,
    file_content: bytes,
    file_extension: str
) -> str:
    """
    Upload a report to S3
    
    Args:
        account_id: AWS account ID
        evaluation_timestamp: Evaluation timestamp (ISO 8601)
        report_type: "executive" or "technical"
        file_content: Report file content as bytes
        file_extension: File extension (e.g., "docx", "xlsx")
    
    Returns:
        str: S3 key of uploaded report
    
    Requirements: 6.7, 9.3
    """
    # Generate S3 key with structured pattern
    generation_timestamp = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
    s3_key = f"reports/{account_id}/{evaluation_timestamp}/{report_type}-{generation_timestamp}.{file_extension}"
    
    # Upload to S3
    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key=s3_key,
        Body=file_content,
        ContentType=_get_content_type(file_extension)
    )
    
    return s3_key


def generate_signed_url(s3_key: str, expiration_seconds: int = 3600) -> str:
    """
    Generate a signed URL for downloading a report
    
    Args:
        s3_key: S3 key of the report
        expiration_seconds: URL expiration time in seconds (default: 1 hour)
    
    Returns:
        str: Signed URL for downloading the report
    
    Requirements: 6.8, 6.9, 9.4
    """
    signed_url = s3_client.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': BUCKET_NAME,
            'Key': s3_key
        },
        ExpiresIn=expiration_seconds
    )
    
    return signed_url


def _get_content_type(file_extension: str) -> str:
    """Get content type based on file extension"""
    content_types = {
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'pdf': 'application/pdf',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    }
    return content_types.get(file_extension, 'application/octet-stream')
