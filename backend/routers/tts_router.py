"""
TTS (Text-to-Speech) API Router

Handles text-to-speech conversion using OpenAI TTS API.
Uses Fable voice by default for warm, sympathetic narration.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from openai import OpenAI
import io
from pathlib import Path
from typing import Optional

router = APIRouter(prefix="/tts", tags=["tts"])


@router.post("/generate")
async def generate_tts(request: dict):
    """
    Generate speech audio from text using OpenAI TTS API.
    
    Request body:
        {
            "text": "Text to convert to speech",
            "voice": "fable" (optional, defaults to "fable")
        }
    
    Returns:
        Audio file (MP3) as streaming response
    """
    try:
        client = OpenAI()
        
        text = request.get("text", "")
        voice = request.get("voice", "fable")  # Fable = British, sympathetic
        
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        # Generate speech using OpenAI TTS
        response = client.audio.speech.create(
            model="tts-1",  # Fast, good quality for POC
            voice=voice,
            input=text
        )
        
        # Convert to bytes and return as streaming response
        audio_bytes = io.BytesIO(response.content)
        audio_bytes.seek(0)
        
        return StreamingResponse(
            audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=tts_audio.mp3"
            }
        )
        
    except Exception as e:
        print(f"TTS generation error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audio/{journey_id}/{month_idx}")
async def get_tts_audio(journey_id: str, month_idx: int):
    """
    Get pre-generated TTS audio file for a journey/month.
    
    This serves the MP3 file that was generated during Stage 5.
    Much faster than generating on-demand (instant vs 2-3 seconds).
    
    Returns:
        Audio file (MP3) as file response
    """
    try:
        # Look for the pre-generated audio file
        audio_dir = Path("agents/outputs/tts_summaries")
        journey_short = journey_id[:8]
        
        # Find the most recent audio file for this journey+month
        pattern = f"tts_summary_{journey_short}_month{month_idx}_*.mp3"
        files = list(audio_dir.glob(pattern))
        
        if not files:
            raise HTTPException(
                status_code=404, 
                detail=f"TTS audio not found for journey {journey_id}, month {month_idx}. Run the pipeline first."
            )
        
        # Get the most recent file
        latest_file = max(files, key=lambda p: p.stat().st_mtime)
        
        # Return audio file
        return FileResponse(
            latest_file,
            media_type="audio/mpeg",
            filename=f"tts_{journey_short}_month{month_idx}.mp3"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error serving TTS audio: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

