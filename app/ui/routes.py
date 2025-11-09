"""UI routes for simple web interface"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

router = APIRouter()

# Get static files directory
static_dir = Path(__file__).parent / "static"


@router.get("/ui", response_class=HTMLResponse)
async def ui_index():
    """Serve main UI page"""
    html_file = static_dir / "index.html"
    
    if not html_file.exists():
        return HTMLResponse(
            content="<h1>UI not found</h1><p>Please create app/ui/static/index.html</p>",
            status_code=404
        )
    
    with open(html_file, 'r', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())


@router.get("/ui/static/{file_path:path}")
async def serve_static(file_path: str):
    """Serve static files (CSS, JS, etc.)"""
    file = static_dir / file_path
    
    if not file.exists() or not file.is_file():
        return {"error": "File not found"}, 404
    
    # Determine content type
    content_type = "text/plain"
    if file_path.endswith('.css'):
        content_type = "text/css"
    elif file_path.endswith('.js'):
        content_type = "application/javascript"
    elif file_path.endswith('.html'):
        content_type = "text/html"
    elif file_path.endswith('.png'):
        content_type = "image/png"
    elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
        content_type = "image/jpeg"
    
    return FileResponse(
        path=file,
        media_type=content_type
    )

