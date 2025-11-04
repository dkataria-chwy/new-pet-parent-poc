"""
Image generation service for pet portraits.

This module handles AI-powered pet image generation using OpenAI's DALL-E API.
Provides a clean interface for generating photorealistic pet portraits with
consistent styling and quality.
"""

import os
import httpx
from pydantic import BaseModel
from typing import Optional
from fastapi import HTTPException


class GenerateImageRequest(BaseModel):
    """Request model for pet image generation."""
    name: str
    species: str
    breed: Optional[str] = None
    ageMonths: Optional[int] = None
    appearance: Optional[str] = None


class ImageGenerationService:
    """Service for generating AI pet portraits."""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.image_generation_enabled = os.getenv("ENABLE_AI_IMAGE", "true").lower() == "true"
    
    def _build_prompt(self, request: GenerateImageRequest) -> str:
        """
        Build the image generation prompt for consistent pet portraits.
        
        Args:
            request: Image generation request with pet details
            
        Returns:
            Formatted prompt string for DALL-E
        """
        age_text = f"{request.ageMonths}-month-old" if request.ageMonths else "young"
        breed_text = f"{request.breed} " if request.breed else ""
        appearance_text = f"{request.appearance} " if request.appearance else ""
        
        prompt = (
            f"Photorealistic portrait of a {age_text} "
            f"{breed_text}{request.species} named {request.name}. "
            f"{appearance_text}Sitting three-quarter view facing right, but head turned toward viewer, making eye contact. "
            "Soft studio lighting, high detail, shallow depth of field, pastel background, 3:2 aspect ratio. "
            "No text or watermark."
        )
        
        return prompt
    
    async def generate_pet_image(self, request: GenerateImageRequest) -> dict:
        """
        Generate a pet portrait using AI.
        
        Args:
            request: Pet details for image generation
            
        Returns:
            Dictionary with base64 image data and mime type
            
        Raises:
            HTTPException: If service is disabled, API key missing, or generation fails
        """
        if not self.image_generation_enabled:
            raise HTTPException(status_code=503, detail="Image generation disabled")
            
        if not self.openai_api_key:
            raise HTTPException(status_code=500, detail="Missing OpenAI API key")
        
        prompt = self._build_prompt(request)
        print(f"\n🎨 Generating image for {request.species} '{request.name}'...")
        print(f"🔧 Prompt: {prompt[:100]}...")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/images/generations",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "dall-e-3",
                        "prompt": prompt,
                        "size": "1024x1024",
                        "quality": "standard",
                        "response_format": "b64_json"
                    }
                )
            
            if response.status_code != 200:
                error_detail = f"OpenAI API returned {response.status_code}: {response.text}"
                print(f"\n❌ IMAGE GENERATION ERROR: {error_detail}")
                print(f"🔧 Prompt used: {prompt}")
                raise HTTPException(
                    status_code=502, 
                    detail=error_detail
                )
            
            data = response.json()
            b64_image = data["data"][0]["b64_json"]
            
            return {
                "b64": b64_image, 
                "mime": "image/png"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


# Global service instance
image_service = ImageGenerationService()
