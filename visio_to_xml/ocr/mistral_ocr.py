"""mistral OCR integration for image text extraction."""

import base64
import io
from typing import Optional, Dict, Any
import requests
from PIL import Image

from ..core.config import Config


class MistralOCR:
    """OCR client using mistral API for text extraction from images."""
    
    def __init__(self, config: Config):
        self.config = config
        self.api_key = config.mistral_api_key
        self.api_url = config.mistral_api_url
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
    
    def extract_text(self, image_data: bytes) -> Optional[str]:
        """extract text from image using mistral OCR."""
        try:
            # prepare image for OCR
            processed_image = self._preprocess_image(image_data)
            if not processed_image:
                return None
            
            # encode image to base64
            image_b64 = self._encode_image_base64(processed_image)
            
            # call mistral API
            response = self._call_mistral_ocr(image_b64)
            
            if response and 'text' in response:
                extracted_text = response['text'].strip()
                
                # check confidence if available
                confidence = response.get('confidence', 1.0)
                if confidence < self.config.ocr_confidence_threshold:
                    print(f"warning: OCR confidence {confidence} below threshold {self.config.ocr_confidence_threshold}")
                
                return extracted_text if extracted_text else None
                
        except Exception as e:
            print(f"error during OCR processing: {e}")
            
        return None
    
    def _preprocess_image(self, image_data: bytes) -> Optional[bytes]:
        """preprocess image for optimal OCR results."""
        try:
            # open image
            image = Image.open(io.BytesIO(image_data))
            
            # convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # resize if too large
            max_size = self.config.max_image_size
            if max(image.size) > max_size:
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # enhance contrast for better OCR
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)
            
            # save processed image
            output = io.BytesIO()
            image.save(output, format='PNG', optimize=True)
            return output.getvalue()
            
        except Exception as e:
            print(f"error preprocessing image: {e}")
            return None
    
    def _encode_image_base64(self, image_data: bytes) -> str:
        """encode image data as base64 string."""
        return base64.b64encode(image_data).decode('utf-8')
    
    def _call_mistral_ocr(self, image_b64: str) -> Optional[Dict[str, Any]]:
        """call mistral API for OCR processing."""
        try:
            # prepare request payload
            payload = {
                "model": "pixtral-12b-2409",  # mistral's vision model
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "extract all text from this image. return only the text content, no descriptions or explanations."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_b64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.1
            }
            
            # make API call
            response = self.session.post(
                f"{self.api_url}/chat/completions",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content']
                    return {
                        'text': content,
                        'confidence': 0.9  # mistral doesn't provide confidence, assume high
                    }
            else:
                print(f"mistral API error: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"network error calling mistral API: {e}")
        except Exception as e:
            print(f"unexpected error calling mistral API: {e}")
            
        return None
    
    def is_available(self) -> bool:
        """check if mistral OCR service is available."""
        if not self.api_key:
            return False
            
        try:
            # simple health check
            response = self.session.get(f"{self.api_url}/models", timeout=10)
            return response.status_code == 200
        except Exception:
            return False
