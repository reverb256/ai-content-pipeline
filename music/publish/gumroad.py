import requests
import os
import logging
from typing import Optional, Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class GumroadAdapter:
    """
    Adapter for Gumroad publishing using the Official API.
    References: https://gumroad.com/api
    """
    BASE_URL = "https://api.gumroad.com"

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def _request(self, method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        url = f"{self.BASE_URL}{endpoint}"
        try:
            response = requests.request(method, url, json=data, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"Gumroad API error: {e.response.text}")
            raise RuntimeError(f"Gumroad API Error: {e.response.status_code} - {e.response.text}") from e
        except Exception as e:
            logger.error(f"Unexpected error connecting to Gumroad: {e}")
            raise RuntimeError(f"Connection error: {e}") from e

    def create_product(self, 
                      name: str, 
                      description: str, 
                      price: float = 0.0, 
                      thumbnail_url: Optional[str] = None, 
                      native_type: str = "digital",
                      private: bool = True) -> Dict[str, Any]:
        """
        Creates a digital product on Gumroad.
        
        :param private: If True, sets the product to private/draft.
        """
        # POST /v2/products
        payload = {
            "product_name": name,
            "description": description,
            "price": price,
            "native_type": native_type,
            "published": not private # published=false means draft/private
        }
        if thumbnail_url:
            payload["thumbnail"] = thumbnail_url
            
        logger.info(f"Creating product: {name}...")
        result = self._request("POST", "/v2/products", data=payload)
        
        # Gumroad API v2 returns the product object
        logger.info(f"Product created successfully. ID: {result.get('product_id')}")
        return result

    def upload_file(self, product_id: str, file_path: str) -> Dict[str, Any]:
        """
        Uploads a file to a specific product.
        Sequence: 1. Presign -> 2. Upload.
        """
        # 1. Request presigned URL
        # POST /files/presign
        presign_payload = {
            "product_id": product_id,
            "filename": os.path.basename(file_path)
        }
        presign_res = self._request("POST", "/files/presign", data=presign_payload)
        
        upload_url = presign_res.get("upload_url")
        if not upload_url:
            raise RuntimeError("Failed to obtain presigned upload URL from Gumroad.")

        # 2. Upload the file
        logger.info(f"Uploading {file_path} to Gumroad...")
        with open(file_path, 'rb') as f:
            # Gumroad presigned uploads are typically PUT requests with binary body
            upload_res = requests.put(upload_url, data=f)
            upload_res.raise_for_status()

        logger.info(f"File {os.path.basename(file_path)} uploaded successfully.")
        return {"status": "success", "file": os.path.basename(file_path)}

    def publish_bundle(self, 
                       bundle_name: str, 
                       description: str, 
                       files: list[str], 
                       price: float = 0.0, 
                       thumbnail_url: Optional[str] = None, 
                       private: bool = True) -> Dict[str, Any]:
        """
        Full flow: Create product -> Upload all files.
        """
        # Create product
        product = self.create_product(
            name=bundle_name, 
            description=description, 
            price=price, 
            thumbnail_url=thumbnail_url, 
            private=private
        )
        product_id = product.get("product_id")
        
        # Upload all files
        upload_results = []
        for file_path in files:
            upload_results.append(self.upload_file(product_id, file_path))
            
        return {
            "product_id": product_id,
            "url": product.get("url"),
            "uploads": upload_results
        }

if __name__ == "__main__":
    # Dry-run / Example usage
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python gumroad.py <token> <bundle_name>")
        sys.exit(1)
        
    token, name = sys.argv[1:3]
    
    adapter = GumroadAdapter(access_token=token)
    try:
        # Mock files for dry run
        with open("test_file.wav", "w") as f: f.write("dummy data")
        
        res = adapter.publish_bundle(
            bundle_name=name,
            description="AI Generated Music Bundle",
            files=["test_file.wav"],
            private=True
        )
        print(res)
        os.remove("test_file.wav")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
