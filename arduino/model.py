import os
import urllib.request
import zipfile

# Create models directory if it doesn't exist
os.makedirs("models", exist_ok=True)

# Download the model
url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
zip_path = "models/vosk-model-small-en-us-0.15.zip"
model_path = "vosk-model-small-en-us-0.15"

if not os.path.exists(model_path):
    print("Downloading model...")
    urllib.request.urlretrieve(url, zip_path)
    
    # Extract the zip file
    print("Extracting model...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(".")
    
    # Clean up
    os.remove(zip_path)
    print("Model downloaded and extracted successfully!")
else:
    print("Model already exists!")