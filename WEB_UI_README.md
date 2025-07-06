# Sprite Viewer Web UI

A modern web-based interface for the Sprite Viewer application, replacing the Qt-based UI with a clean, responsive web interface.

## Features

- 🚀 **Fast & Responsive**: Built with FastAPI backend and vanilla JavaScript frontend
- 🎨 **Modern Dark Theme**: Clean, professional interface 
- 🔄 **Real-time Updates**: WebSocket support for live frame updates
- 📱 **Cross-platform**: Works on any device with a web browser
- 🎮 **Full Feature Parity**: All sprite viewing and editing capabilities

## Quick Start

1. **Activate virtual environment**:
   ```bash
   source venv/bin/activate  # Linux/Mac/WSL
   # or
   venv\Scripts\activate     # Windows
   ```

2. **Install dependencies** (if not already installed):
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the web server**:
   ```bash
   python run_web.py
   ```

4. **Open in browser**:
   Navigate to http://localhost:8000

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Web Browser   │ ←──→│  FastAPI Server  │ ←──→│  Sprite Model   │
│  (HTML/JS/CSS)  │     │   (web_api.py)   │     │ (Existing Code) │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        ↑                         ↑
        │                         │
        └── WebSocket ────────────┘
           (Real-time updates)
```

## API Endpoints

### Sprite Management
- `POST /api/sprite/upload` - Upload sprite sheet
- `POST /api/sprite/load` - Load from file path
- `GET /api/sprite/info` - Get sprite information
- `GET /api/sprite/original` - Get original sprite image

### Frame Operations
- `POST /api/frames/extract` - Extract frames with settings
- `POST /api/frames/extract/auto` - Auto-detect frames
- `GET /api/frames/{frame_id}` - Get specific frame
- `GET /api/frames/all` - Get all frames as base64

### Animation Control
- `POST /api/animation/play` - Start playback
- `POST /api/animation/pause` - Pause playback
- `POST /api/animation/frame/{frame_id}` - Go to frame
- `GET /api/animation/status` - Get animation status
- `POST /api/animation/fps/{fps}` - Set FPS
- `POST /api/animation/loop/{enabled}` - Toggle loop

### Segments
- `GET /api/segments` - Get all segments
- `POST /api/segments/create` - Create new segment
- `DELETE /api/segments/{name}` - Delete segment

### WebSocket
- `WS /ws` - Real-time updates for frame changes

## Keyboard Shortcuts

- `Space` - Play/Pause animation
- `←/→` - Previous/Next frame
- `+/-` - Zoom in/out
- `0` - Fit to screen

## Key Improvements over Qt

1. **No Installation Required**: Just a web browser
2. **Better Styling**: Modern CSS instead of Qt stylesheets
3. **Easier Development**: Standard web technologies
4. **Remote Access**: Can run on a server
5. **Mobile Support**: Responsive design

## Development

### Adding New Features

1. **Backend**: Add new endpoints in `web_api.py`
2. **Frontend**: Update HTML/JS in `static/index.html`
3. **Styling**: Modify CSS variables for theming

### Testing

```bash
# Run with auto-reload for development
python -m uvicorn web_api:app --reload

# Run tests
pytest tests/
```

## Deployment

For production deployment:

```bash
# Use production server
uvicorn web_api:app --host 0.0.0.0 --port 8000 --workers 4

# Or use gunicorn
gunicorn web_api:app -w 4 -k uvicorn.workers.UvicornWorker
```

## Troubleshooting

### Port Already in Use
Change the port in `run_web.py` or use:
```bash
python -m uvicorn web_api:app --port 8001
```

### CORS Issues
The server allows all origins by default. For production, update CORS settings in `web_api.py`.

### WebSocket Connection Failed
Ensure your firewall allows WebSocket connections on the server port.

## Future Enhancements

- [ ] Progressive Web App (PWA) support
- [ ] Drag & drop file upload
- [ ] Export functionality
- [ ] Touch gesture support
- [ ] Theme customization
- [ ] Multi-language support