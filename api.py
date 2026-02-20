"""
Accordo Agent - REST API Server

A simple FastAPI server that exposes the Accordo workflow as HTTP endpoints.
The frontend connects to this API to generate Concerto models.

Run with: python3 api.py
"""

import os
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Check dependencies
try:
    from fastapi import FastAPI, HTTPException, UploadFile, File
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
except ImportError:
    print("❌ Missing dependencies. Install with:")
    print("   pip install fastapi uvicorn --break-system-packages")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.workflow import AccordoWorkflow
from src.models import UserRequest

# Initialize FastAPI
app = FastAPI(
    title="Accordo Agent API",
    description="Generate Concerto models from natural language",
    version="0.1.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class GenerateRequest(BaseModel):
    description: str
    namespace: str | None = None
    context: str | None = None

class GenerateResponse(BaseModel):
    success: bool
    cto: str | None = None
    namespace: str | None = None
    error: str | None = None

class AudioGenerateResponse(BaseModel):
    success: bool
    transcript: str | None = None
    cto: str | None = None
    namespace: str | None = None
    error: str | None = None

class ValidateRequest(BaseModel):
    cto: str

class ValidateResponse(BaseModel):
    valid: bool
    status: str
    error: str | None = None
    details: str | None = None

class HealthResponse(BaseModel):
    status: str
    groq_configured: bool
    concerto_version: str | None = None


# API Endpoints

@app.get("/", response_model=dict)
async def root():
    """API root - basic info."""
    return {
        "name": "Accordo Agent API",
        "version": "0.1.0",
        "endpoints": {
            "POST /generate": "Generate a Concerto model from description",
            "POST /validate": "Validate CTO code",
            "GET /health": "Check API health"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    import subprocess
    
    groq_configured = bool(os.getenv("GROQ_API_KEY"))
    
    # Check concerto version
    concerto_version = None
    try:
        result = subprocess.run(
            ["npx", "concerto", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=Path(__file__).parent
        )
        if result.returncode == 0:
            concerto_version = result.stdout.strip()
    except Exception:
        pass
    
    return HealthResponse(
        status="healthy" if groq_configured else "degraded",
        groq_configured=groq_configured,
        concerto_version=concerto_version
    )


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """Generate a Concerto model from natural language description."""
    
    # Check API key
    if not os.getenv("GROQ_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="GROQ_API_KEY not configured. Please set the environment variable."
        )
    
    if not request.description.strip():
        raise HTTPException(
            status_code=400,
            detail="Description is required"
        )
    
    try:
        # Create workflow and run
        workflow = AccordoWorkflow(verbose=False)
        
        result = workflow.run(
            description=request.description,
            namespace=request.namespace,
            context=request.context
        )
        
        if result.success and result.cto_content:
            # Extract namespace from CTO content
            ns_match = None
            if result.cto_content:
                import re
                match = re.search(r'namespace\s+(\S+)', result.cto_content)
                if match:
                    ns_match = match.group(1)
            
            return GenerateResponse(
                success=True,
                cto=result.cto_content,
                namespace=ns_match
            )
        else:
            return GenerateResponse(
                success=False,
                error=result.error_message or "Unknown error during generation"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.post("/generate-from-audio", response_model=AudioGenerateResponse)
async def generate_from_audio(
    audio: UploadFile = File(...),
    namespace: str | None = None,
    context: str | None = None
):
    """Generate a Concerto model from a voice/audio description via Groq Whisper."""

    if not os.getenv("GROQ_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="GROQ_API_KEY not configured. Please set the environment variable."
        )

    # Persist the upload to a temp file so the workflow can open it by path
    suffix = Path(audio.filename).suffix if audio.filename else ".wav"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await audio.read())
            tmp_path = tmp.name

        workflow = AccordoWorkflow(verbose=False)
        result = workflow.run_from_audio(
            audio_path=tmp_path,
            namespace=namespace,
            context=context
        )

        if result.success and result.cto_content:
            import re
            ns_match = re.search(r'namespace\s+(\S+)', result.cto_content)
            return AudioGenerateResponse(
                success=True,
                transcript=result.transcript,
                cto=result.cto_content,
                namespace=ns_match.group(1) if ns_match else None
            )
        else:
            return AudioGenerateResponse(
                success=False,
                transcript=result.transcript,
                error=result.error_message or "Unknown error during generation"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


@app.post("/validate", response_model=ValidateResponse)
async def validate(request: ValidateRequest):
    """Validate CTO code."""
    
    from src.tools.concerto_tools import validate_cto_string
    
    if not request.cto.strip():
        raise HTTPException(
            status_code=400,
            detail="CTO code is required"
        )
    
    try:
        result = validate_cto_string(request.cto)
        
        return ValidateResponse(
            valid=result.is_valid,
            status=result.status.value,
            error=result.error_message,
            details=result.error_details
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# Run server
if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("🚀 Accordo Agent API Server")
    print("=" * 50)
    
    # Check configuration
    if os.getenv("GROQ_API_KEY"):
        print("✅ GROQ_API_KEY configured")
    else:
        print("⚠️  GROQ_API_KEY not set - generation will fail")
    
    print("\n📡 Starting server at http://localhost:8000")
    print("📄 API docs at http://localhost:8000/docs")
    print("\n🌐 Open frontend/index.html in your browser")
    print("   Or serve with: python3 -m http.server 3000 -d frontend")
    print("\nPress Ctrl+C to stop\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
