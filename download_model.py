import os
import urllib.request
import zipfile
import sys

def download_vosk_model():
    # Create models directory if it doesn't exist
    model_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(model_dir, "vosk-model-small-en-us-0.15")
    zip_path = os.path.join(model_dir, "vosk-model-small-en-us-0.15.zip")
    
    if not os.path.exists(model_path):
        print("Downloading Vosk model (30-50MB, this may take a few minutes)...")
        url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
        
        try:
            # Download the file
            urllib.request.urlretrieve(url, zip_path)
            
            # Extract the zip file
            print("Extracting model...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(model_dir)
            
            # Clean up
            os.remove(zip_path)
            print(f"Model downloaded and extracted to: {model_path}")
            return True
            
        except Exception as e:
            print(f"Error downloading model: {e}")
            if os.path.exists(zip_path):
                os.remove(zip_path)
            return False
    else:
        print("Model already exists at:", model_path)
        return True

if __name__ == "__main__":
    success = download_vosk_model()
    if success:
        print("\nModel setup complete! You can now run voice_control.py")
    else:
        print("\nFailed to download model. Please check your internet connection and try again.")
        print("You can also manually download the model from:")
        print("https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip")
        print("Extract it to the project directory and rename the folder to 'vosk-model-small-en-us-0.15'")
        sys.exit(1)
