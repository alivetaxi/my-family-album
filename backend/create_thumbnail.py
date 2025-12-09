
import os
from google.cloud import storage
from PIL import Image

storage_client = storage.Client()

def create_thumbnail(event, context):
    """
    Cloud Function to be triggered by Cloud Storage when a new object is created.
    """
    bucket_name = event['bucket']
    file_name = event['name']
    
    # Check if the uploaded file is an image.
    if not file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
        print(f"File {file_name} is not an image, skipping thumbnail generation.")
        return

    # Avoid infinite loops.
    if file_name.startswith('thumbnails/'):
        print(f"File {file_name} is already a thumbnail, skipping.")
        return

    print(f"Processing file: {file_name}.")

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    
    # Download the image into a temporary file
    tmp_image_path = f"/tmp/{file_name}"
    blob.download_to_filename(tmp_image_path)
    
    # Create a thumbnail
    thumbnail_size = (128, 128)
    thumbnail_path = f"/tmp/thumbnail/{file_name}"
    
    with Image.open(tmp_image_path) as img:
        img.thumbnail(thumbnail_size)
        img.save(thumbnail_path)
        
    # Upload the thumbnail
    thumbnail_blob_name = f"thumbnails/{file_name}"
    thumbnail_blob = bucket.blob(thumbnail_blob_name)
    thumbnail_blob.upload_from_filename(thumbnail_path)
    print(f"Thumbnail uploaded to: {thumbnail_blob_name}")
    
    # Clean up temporary files
    os.remove(tmp_image_path)
    os.remove(thumbnail_path)
