from google.cloud import storage

# Set the path to your service account key JSON file
SERVICE_ACCOUNT_JSON = "key.json" # include full path if not in same folder
DATASET_PATH = "full/path/dataset-file" # ex. "output.csv"
UPLOAD_PATH = "your-dataset-name/file-name" # ex. "nea-arts-basic/output.csv"


# Initialize the GCS client
client = storage.Client.from_service_account_json(SERVICE_ACCOUNT_JSON)

# Specify your bucket name
bucket_name = "save_the_data"

# Get the bucket
bucket = client.bucket(bucket_name)

blob = bucket.blob(UPLOAD_PATH)
blob.upload_from_filename(DATASET_PATH)
print(f"Uploaded {DATASET_PATH} to {UPLOAD_PATH}")
