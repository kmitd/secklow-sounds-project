from gcloud import storage

# env_variables: GCLOUD_PROJECT: your-project-id , CLOUD_STORAGE_BUCKET: your-bucket-name

def upload_to_GCloud(raw_file,confs):

    # Create a Cloud Storage client.
    gcs = storage.Client()

    # Get the bucket that the file will be uploaded to.
    bucket = gcs.get_bucket(confs['cloud_storage_bucket'])

    # Create a new blob and upload the file's content.
    
    blob = bucket.blob("data/raws/"+raw_file.split("/")[1]+"/"+raw_file.split("/")[-1])
    blob.upload_from_string(open(raw_file,"r").read())

    # The public URL can be used to directly access the uploaded file via HTTP.
    return blob.public_url