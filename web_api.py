"""
FastAPI backend for Sprite Viewer
==================================

Provides REST API and WebSocket endpoints for sprite sheet operations.
Integrates with existing SpriteModel for all sprite processing.
"""

from fastapi import FastAPI, WebSocket, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import json
import io
import base64
from pathlib import Path
from typing import Optional, List, Dict, Any
from PIL import Image
import numpy as np

# Qt Application initialization (required for QPixmap)
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'  # For headless environments

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor

# Create QApplication instance if not exists
app = QApplication.instance()
if app is None:
    app = QApplication([])

# Import existing sprite model and controllers
from sprite_model import SpriteModel
from core.animation_controller import AnimationController
from managers.animation_segment_manager import AnimationSegmentManager
from config import Config

# Store application state
app_state = {
    "sprite_model": None,
    "animation_controller": None,
    "segment_manager": None,
    "websocket_clients": set(),
    "current_file": None
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup application resources."""
    # Startup
    app_state["sprite_model"] = SpriteModel()
    app_state["animation_controller"] = AnimationController()  # No parameters
    app_state["segment_manager"] = AnimationSegmentManager()
    
    # Initialize the animation controller with sprite model (viewer is None for web API)
    app_state["animation_controller"].initialize(app_state["sprite_model"], None)
    
    # Connect signals for real-time updates
    app_state["sprite_model"].frameChanged.connect(on_frame_changed)
    app_state["sprite_model"].dataLoaded.connect(on_data_loaded)
    app_state["sprite_model"].extractionCompleted.connect(on_extraction_completed)
    
    yield
    
    # Cleanup
    # Disconnect signals
    app_state["sprite_model"].frameChanged.disconnect(on_frame_changed)
    app_state["sprite_model"].dataLoaded.disconnect(on_data_loaded)
    app_state["sprite_model"].extractionCompleted.disconnect(on_extraction_completed)

# Create FastAPI app
app = FastAPI(title="Sprite Viewer API", version="1.0.0", lifespan=lifespan)

# Add CORS middleware for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Signal handlers for real-time updates
def on_frame_changed(current_frame: int, total_frames: int):
    """Broadcast frame changes to all connected clients."""
    asyncio.create_task(broadcast_update({
        "type": "frame_changed",
        "current_frame": current_frame,
        "total_frames": total_frames
    }))

def on_data_loaded(file_path: str):
    """Notify clients when new sprite sheet is loaded."""
    asyncio.create_task(broadcast_update({
        "type": "sprite_loaded",
        "file_path": file_path
    }))

def on_extraction_completed(frame_count: int):
    """Notify clients when frame extraction is complete."""
    asyncio.create_task(broadcast_update({
        "type": "extraction_completed",
        "frame_count": frame_count
    }))

async def broadcast_update(data: dict):
    """Send update to all connected WebSocket clients."""
    disconnected = set()
    for websocket in app_state["websocket_clients"]:
        try:
            await websocket.send_json(data)
        except:
            disconnected.add(websocket)
    
    # Remove disconnected clients
    app_state["websocket_clients"] -= disconnected

# API Endpoints

@app.get("/")
async def read_root():
    """Serve the main HTML page."""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Sprite Viewer API is running. Upload index.html to static/ directory."}

@app.post("/api/sprite/upload")
async def upload_sprite(file: UploadFile = File(...)):
    """Upload a sprite sheet file."""
    try:
        # Save uploaded file temporarily
        content = await file.read()
        temp_path = Path(f"/tmp/{file.filename}")
        temp_path.write_bytes(content)
        
        # Load into sprite model
        success, message = app_state["sprite_model"].load_sprite_sheet(str(temp_path))
        
        if success:
            app_state["current_file"] = file.filename
            
            # Get sprite info
            pixmap = app_state["sprite_model"].original_sprite_sheet
            return {
                "success": True,
                "message": message,
                "filename": file.filename,
                "width": pixmap.width() if pixmap else 0,
                "height": pixmap.height() if pixmap else 0
            }
        else:
            raise HTTPException(status_code=400, detail=message)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sprite/load")
async def load_sprite(file_path: str):
    """Load a sprite sheet from local file system."""
    try:
        success, message = app_state["sprite_model"].load_sprite_sheet(file_path)
        
        if success:
            app_state["current_file"] = Path(file_path).name
            
            # Get sprite info
            pixmap = app_state["sprite_model"].original_sprite_sheet
            return {
                "success": True,
                "message": message,
                "filename": app_state["current_file"],
                "width": pixmap.width() if pixmap else 0,
                "height": pixmap.height() if pixmap else 0
            }
        else:
            raise HTTPException(status_code=400, detail=message)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sprite/info")
async def get_sprite_info():
    """Get information about the currently loaded sprite."""
    model = app_state["sprite_model"]
    
    if not model.is_loaded:
        raise HTTPException(status_code=404, detail="No sprite sheet loaded")
    
    pixmap = model.original_sprite_sheet
    
    return {
        "filename": app_state["current_file"],
        "width": pixmap.width(),
        "height": pixmap.height(),
        "has_frames": model.frame_count > 0,
        "frame_count": model.frame_count,
        "current_frame": model.current_frame,
        "frame_settings": {
            "width": model.get_frame_width(),
            "height": model.get_frame_height(),
            "offset_x": model.get_offset_x(),
            "offset_y": model.get_offset_y(),
            "spacing_x": model.get_spacing_x(),
            "spacing_y": model.get_spacing_y()
        }
    }

@app.get("/api/sprite/original")
async def get_original_sprite():
    """Get the original sprite sheet as an image."""
    model = app_state["sprite_model"]
    
    if not model.is_loaded:
        raise HTTPException(status_code=404, detail="No sprite sheet loaded")
    
    # Convert QPixmap to PIL Image
    pixmap = model.original_sprite_sheet
    qimage = pixmap.toImage()
    
    # Convert QImage to bytes
    buffer = bytearray()
    qbuffer = qimage.bits()
    qbuffer.setsize(qimage.sizeInBytes())
    buffer.extend(qbuffer.asstring())
    
    # Create PIL Image from bytes
    img = Image.frombytes(
        "RGBA",
        (qimage.width(), qimage.height()),
        bytes(buffer),
        "raw",
        "BGRA"
    )
    
    # Return as PNG
    img_io = io.BytesIO()
    img.save(img_io, format='PNG')
    img_io.seek(0)
    
    return StreamingResponse(img_io, media_type="image/png")

@app.post("/api/frames/extract")
async def extract_frames(
    width: int,
    height: int,
    offset_x: int = 0,
    offset_y: int = 0,
    spacing_x: int = 0,
    spacing_y: int = 0
):
    """Extract frames from the sprite sheet."""
    model = app_state["sprite_model"]
    
    if not model.is_loaded:
        raise HTTPException(status_code=404, detail="No sprite sheet loaded")
    
    success, message, frame_count = model.extract_frames(
        width, height, offset_x, offset_y, spacing_x, spacing_y
    )
    
    if success:
        return {
            "success": True,
            "message": message,
            "frame_count": frame_count
        }
    else:
        raise HTTPException(status_code=400, detail=message)

@app.post("/api/frames/extract/auto")
async def auto_detect_frames():
    """Auto-detect and extract frames."""
    model = app_state["sprite_model"]
    
    if not model.is_loaded:
        raise HTTPException(status_code=404, detail="No sprite sheet loaded")
    
    # Perform auto-detection
    results = model.detect_frames()
    
    if results:
        best_result = results[0]  # First result is best
        
        # Extract with best settings
        success, message, frame_count = model.extract_frames(
            best_result['width'],
            best_result['height'],
            best_result.get('offset_x', 0),
            best_result.get('offset_y', 0),
            best_result.get('spacing_x', 0),
            best_result.get('spacing_y', 0)
        )
        
        if success:
            return {
                "success": True,
                "message": f"Auto-detected {frame_count} frames",
                "frame_count": frame_count,
                "settings": best_result,
                "all_results": results[:5]  # Top 5 results
            }
    
    raise HTTPException(status_code=400, detail="Could not auto-detect frames")

@app.get("/api/frames/{frame_id}")
async def get_frame(frame_id: int):
    """Get a specific frame as an image."""
    model = app_state["sprite_model"]
    
    if model.frame_count == 0:
        raise HTTPException(status_code=404, detail="No frames extracted")
    
    if frame_id < 0 or frame_id >= model.frame_count:
        raise HTTPException(status_code=404, detail=f"Frame {frame_id} not found")
    
    # Get frame pixmap
    pixmap = model.get_frame(frame_id)
    if not pixmap:
        raise HTTPException(status_code=404, detail=f"Frame {frame_id} is empty")
    
    # Convert QPixmap to PIL Image
    qimage = pixmap.toImage()
    buffer = bytearray()
    qbuffer = qimage.bits()
    qbuffer.setsize(qimage.sizeInBytes())
    buffer.extend(qbuffer.asstring())
    
    img = Image.frombytes(
        "RGBA",
        (qimage.width(), qimage.height()),
        bytes(buffer),
        "raw",
        "BGRA"
    )
    
    # Return as PNG
    img_io = io.BytesIO()
    img.save(img_io, format='PNG')
    img_io.seek(0)
    
    return StreamingResponse(img_io, media_type="image/png")

@app.get("/api/frames/all")
async def get_all_frames():
    """Get all frames as base64 encoded images."""
    model = app_state["sprite_model"]
    
    if model.frame_count == 0:
        raise HTTPException(status_code=404, detail="No frames extracted")
    
    frames = []
    for i in range(model.frame_count):
        pixmap = model.get_frame(i)
        if pixmap:
            # Convert to base64
            qimage = pixmap.toImage()
            buffer = bytearray()
            qbuffer = qimage.bits()
            qbuffer.setsize(qimage.sizeInBytes())
            buffer.extend(qbuffer.asstring())
            
            img = Image.frombytes(
                "RGBA",
                (qimage.width(), qimage.height()),
                bytes(buffer),
                "raw",
                "BGRA"
            )
            
            img_io = io.BytesIO()
            img.save(img_io, format='PNG')
            img_io.seek(0)
            
            frames.append({
                "id": i,
                "data": base64.b64encode(img_io.getvalue()).decode()
            })
    
    return {"frames": frames}

@app.post("/api/animation/play")
async def play_animation():
    """Start animation playback."""
    controller = app_state["animation_controller"]
    controller.start_animation()
    return {"status": "playing"}

@app.post("/api/animation/pause")
async def pause_animation():
    """Pause animation playback."""
    controller = app_state["animation_controller"]
    controller.pause_animation()
    return {"status": "paused"}

@app.post("/api/animation/frame/{frame_id}")
async def set_frame(frame_id: int):
    """Go to a specific frame."""
    model = app_state["sprite_model"]
    
    if frame_id < 0 or frame_id >= model.frame_count:
        raise HTTPException(status_code=404, detail=f"Frame {frame_id} not found")
    
    model.set_current_frame(frame_id)
    return {"current_frame": frame_id}

@app.get("/api/animation/status")
async def get_animation_status():
    """Get current animation status."""
    controller = app_state["animation_controller"]
    model = app_state["sprite_model"]
    
    return {
        "is_playing": controller.is_playing,  # property, not method
        "current_frame": model.current_frame,
        "total_frames": model.frame_count,
        "fps": controller.current_fps,  # property
        "loop": controller.loop_enabled  # property
    }

@app.post("/api/animation/fps/{fps}")
async def set_fps(fps: int):
    """Set animation FPS."""
    if fps < 1 or fps > 60:
        raise HTTPException(status_code=400, detail="FPS must be between 1 and 60")
    
    controller = app_state["animation_controller"]
    controller.set_fps(fps)
    return {"fps": fps}

@app.post("/api/animation/loop/{enabled}")
async def set_loop(enabled: bool):
    """Enable/disable animation looping."""
    controller = app_state["animation_controller"]
    controller.set_loop_mode(enabled)
    return {"loop": enabled}

@app.get("/api/segments")
async def get_segments():
    """Get all animation segments."""
    manager = app_state["segment_manager"]
    model = app_state["sprite_model"]
    
    if app_state["current_file"]:
        segments = manager.get_all_segments()
        
        return {
            "segments": [
                {
                    "name": seg.name,
                    "start_frame": seg.start_frame,
                    "end_frame": seg.end_frame,
                    "color": [seg.color.red(), seg.color.green(), seg.color.blue()],
                    "frame_count": seg.end_frame - seg.start_frame + 1
                }
                for seg in segments
            ]
        }
    
    return {"segments": []}

@app.post("/api/segments/create")
async def create_segment(
    name: str,
    start_frame: int,
    end_frame: int,
    color: Optional[List[int]] = None
):
    """Create a new animation segment."""
    manager = app_state["segment_manager"]
    
    if not app_state["current_file"]:
        raise HTTPException(status_code=400, detail="No sprite loaded")
    
    sprite_path = Path(app_state["current_file"]).stem
    
    # Create segment
    success, error_msg = manager.add_segment(name, start_frame, end_frame, None if not color else QColor(*color), "")
    
    if success:
        # Get the created segment
        segment = manager.get_segment(name)
        
        return {
            "success": True,
            "segment": {
                "name": segment.name,
                "start_frame": segment.start_frame,
                "end_frame": segment.end_frame,
                "color": [segment.color.red(), segment.color.green(), segment.color.blue()]
            }
        }
    else:
        raise HTTPException(status_code=400, detail=f"Failed to create segment: {error_msg}")

@app.delete("/api/segments/{name}")
async def delete_segment(name: str):
    """Delete an animation segment."""
    manager = app_state["segment_manager"]
    
    if not app_state["current_file"]:
        raise HTTPException(status_code=400, detail="No sprite loaded")
    
    sprite_path = Path(app_state["current_file"]).stem
    
    # Remove segment
    manager.remove_segment(name)
    
    return {"success": True, "message": f"Deleted segment: {name}"}

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection for real-time updates."""
    await websocket.accept()
    app_state["websocket_clients"].add(websocket)
    
    try:
        # Send initial status
        model = app_state["sprite_model"]
        controller = app_state["animation_controller"]
        
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "has_sprite": model.is_loaded,
            "has_frames": model.frame_count > 0,
            "frame_count": model.frame_count,
            "current_frame": model.current_frame if model.frame_count > 0 else 0
        })
        
        # Keep connection alive and handle messages
        while True:
            data = await websocket.receive_json()
            
            # Handle client commands
            if data.get("command") == "ping":
                await websocket.send_json({"type": "pong"})
            
    except Exception:
        pass
    finally:
        app_state["websocket_clients"].discard(websocket)

if __name__ == "__main__":
    import uvicorn
    print("Starting Sprite Viewer API server...")
    print("Open http://localhost:8000 in your browser")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)