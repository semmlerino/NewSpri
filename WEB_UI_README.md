# Web Sprite Viewer

A modern web-based version of the Python Sprite Viewer application, featuring sprite sheet animation preview, intelligent frame extraction, and comprehensive export capabilities.

## Features

### Core Functionality
- **Sprite Sheet Loading**: Upload and display sprite sheets (PNG, JPG, BMP, GIF)
- **Intelligent Frame Detection**: Auto-detect frame sizes with multiple algorithms
- **Animation Playback**: Smooth animation with FPS control (1-60 FPS)
- **Zoom & Pan Canvas**: Interactive sprite display with precise controls
- **Grid Overlay**: Toggle grid overlay for alignment

### Frame Extraction
- **Grid-Based Extraction**: Traditional grid-based frame splitting
- **CCL Extraction**: Connected Component Labeling for irregular sprites
- **Frame Size Presets**: Pre-configured sizes (16×16 to 256×256)
- **Custom Dimensions**: Manual frame size configuration
- **Offset & Spacing**: Fine-tune extraction parameters

### Animation Splitting
- **Frame Selection**: Multi-select frames with mouse and keyboard
- **Named Segments**: Create and manage animation segments
- **Color Coding**: Visual segment identification
- **Segment Preview**: Individual segment playback

### Export System
- **Individual Frames**: Export each frame separately
- **Sprite Sheets**: Combine frames into new sprite sheets
- **Segments Per Row**: Export segments as rows (game engine ready)
- **Animated GIF**: Export as animated GIF (planned)
- **Multiple Formats**: PNG, JPG, BMP support
- **Scale Options**: 0.5x to 4.0x scaling
- **Custom Layouts**: Configurable spacing and padding

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **PIL/Pillow**: Image processing
- **NumPy**: Numerical operations
- **Uvicorn**: ASGI server

### Frontend
- **React 18**: Modern React with hooks
- **HTML5 Canvas**: High-performance sprite rendering
- **CSS Grid**: Responsive layout system
- **Axios**: API communication
- **File-saver**: Client-side file downloads

## Installation & Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn

### Backend Setup
```bash
cd web_backend
pip install -r requirements.txt
```

### Frontend Setup
```bash
cd web_frontend
npm install
```

## Running the Application

### Start Backend (Terminal 1)
```bash
cd web_backend
python main.py
```
Backend runs on: http://localhost:8000

### Start Frontend (Terminal 2)
```bash
cd web_frontend
npm start
```
Frontend runs on: http://localhost:3000

## Usage Guide

### 1. Upload Sprite Sheet
- Click "Upload Sprite Sheet" or drag & drop an image file
- Supported formats: PNG, JPG, BMP, GIF

### 2. Extract Frames
- Use "Auto Detect Frame Size" for automatic detection
- Or select from preset frame sizes
- Or enter custom dimensions manually
- Click "Extract Frames" to process

### 3. Preview Animation
- Use playback controls to play/pause animation
- Adjust FPS (1-60) for different speeds
- Navigate frames with arrow buttons or slider
- Zoom and pan the canvas for detailed view

### 4. Animation Splitting (Optional)
- Switch to "Animation Splitting" tab
- Select frames using mouse (Ctrl for multi-select, Shift for range)
- Right-click to create segments from selection
- Name your animation segments (walk, run, jump, etc.)

### 5. Export
- Click "Export" button to open export dialog
- Choose export type:
  - **Individual Frames**: Separate files for each frame
  - **Sprite Sheet**: Combined sprite sheet
  - **Segments Per Row**: Each segment as a row (recommended for game engines)
- Configure format, scale, and layout options
- Click "Export" to download

## Keyboard Shortcuts

- **Space**: Play/Pause animation
- **Left/Right Arrow**: Previous/Next frame
- **Home**: First frame
- **End**: Last frame
- **Ctrl+Click**: Multi-select frames (in splitting view)
- **Shift+Click**: Range select frames (in splitting view)

## API Endpoints

### Upload Sprite Sheet
```
POST /upload-sprite
Content-Type: multipart/form-data
```

### Extract Frames
```
POST /extract-frames
Content-Type: application/json
{
  "frame_width": 32,
  "frame_height": 32,
  "offset_x": 0,
  "offset_y": 0,
  "spacing_x": 0,
  "spacing_y": 0,
  "extraction_mode": "grid"
}
```

### Auto-Detect Frame Size
```
POST /auto-detect
Content-Type: application/json
{
  "min_frames": 2,
  "max_frames": 200
}
```

### Get Frame Presets
```
GET /frame-presets
```

## Comparison with Desktop Version

### Implemented Features ✅
- Sprite sheet loading and display
- Frame extraction (grid and basic CCL)
- Animation playback with timing controls
- Frame selection and animation splitting
- Export system with multiple formats
- Auto-detection algorithms
- Zoom/pan canvas with grid overlay
- Responsive design for mobile devices

### Planned Features 🔄
- Advanced CCL extraction algorithm
- Animated GIF export with proper timing
- Keyboard shortcuts system
- Recent files management
- Advanced export options
- Performance optimizations

### Web-Specific Advantages 🌟
- **Cross-Platform**: Works on any device with a web browser
- **No Installation**: Access instantly without downloading software
- **Modern UI**: Responsive design adapts to different screen sizes
- **Cloud Ready**: Can be deployed to cloud platforms
- **Collaborative**: Easy sharing via URL

## Development

### Project Structure
```
web_backend/
├── main.py              # FastAPI application
└── requirements.txt     # Python dependencies

web_frontend/
├── src/
│   ├── components/      # React components
│   │   ├── SpriteCanvas.js
│   │   ├── FrameExtractor.js
│   │   ├── PlaybackControls.js
│   │   ├── AnimationGridView.js
│   │   └── ExportDialog.js
│   ├── App.js          # Main application
│   └── index.js        # React entry point
├── public/
│   └── index.html      # HTML template
└── package.json        # Node.js dependencies
```

### Adding New Features
1. **Backend**: Add new endpoints in `main.py`
2. **Frontend**: Create new components in `src/components/`
3. **Styling**: Add CSS files alongside components
4. **Integration**: Update `App.js` to integrate new features

## Browser Compatibility

- **Chrome**: Fully supported
- **Firefox**: Fully supported
- **Safari**: Fully supported
- **Edge**: Fully supported
- **Mobile**: Responsive design works on tablets and phones

## Performance Considerations

- **Canvas Rendering**: Uses HTML5 Canvas for optimal sprite display
- **Frame Caching**: Efficient frame storage and retrieval
- **Progressive Loading**: Large sprite sheets load progressively
- **Memory Management**: Automatic cleanup of unused resources

## Troubleshooting

### Backend Issues
- **Port 8000 in use**: Change port in `main.py`
- **CORS errors**: Check frontend URL in CORS middleware
- **Import errors**: Ensure Python dependencies are installed

### Frontend Issues
- **Blank page**: Check browser console for errors
- **API errors**: Ensure backend is running on port 8000
- **Upload issues**: Check file format and size limits

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with proper testing
4. Submit a pull request with detailed description

## License

This project maintains the same license as the original Python Sprite Viewer application.

---

**Note**: This web version is based on the desktop Python Sprite Viewer and aims to provide feature parity while leveraging modern web technologies for improved accessibility and cross-platform compatibility.