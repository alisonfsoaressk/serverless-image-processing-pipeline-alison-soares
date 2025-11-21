import boto3
import os
from io import BytesIO
from PIL import Image

s3 = boto3.client("s3")

def lambda_handler(event, context):
    """
    Event expected format:
    {
        "source_bucket": "alison-original-images-xxx",
        "destination_bucket": "alison-resized-images-xxx",
        "object_key": "folder/image.jpg",
        "width": 128,
        "height": 128
    }
    """
    try:
        source_bucket = event.get("source_bucket")
        destination_bucket = event.get("destination_bucket")
        object_key = event.get("object_key")
        width = int(event.get("width", 128))
        height = int(event.get("height", 128))

        if not source_bucket or not destination_bucket or not object_key:
            raise ValueError("Missing source_bucket, destination_bucket or object_key")

        # Download original image from S3
        original_obj = s3.get_object(Bucket=source_bucket, Key=object_key)
        original_body = original_obj["Body"].read()

        image = Image.open(BytesIO(original_body))

        # Create thumbnail
        image.thumbnail((width, height))

        # Save resized image in memory
        buffer = BytesIO()
        # Preserve original format when possible
        image_format = image.format if image.format else "JPEG"
        image.save(buffer, format=image_format)
        buffer.seek(0)

        # Build new key for thumbnail
        base_key = object_key.rsplit("/", 1)[-1]
        thumb_key = f"thumbnails/{width}x{height}_{base_key}"

        # Upload thumbnail to destination bucket
        s3.put_object(
            Bucket=destination_bucket,
            Key=thumb_key,
            Body=buffer,
            ContentType=original_obj.get("ContentType", "image/jpeg")
        )

        return {
            "status": "SUCCESS",
            "source_bucket": source_bucket,
            "destination_bucket": destination_bucket,
            "object_key": object_key,
            "thumbnail_key": thumb_key,
            "thumbnail_size": [width, height]
        }

    except Exception as e:
        return {
            "status": "FAILED",
            "error_message": str(e),
            "input_event": event
        }
