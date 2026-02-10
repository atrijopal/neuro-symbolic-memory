# web_ui.py
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import sys
from pathlib import Path
from jinja2.exceptions import TemplateNotFound
import sqlite3

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import SQLITE_DB_PATH as DB_PATH
from fast_pipe import fast_pipe
from memory.ram_context import RAMContext
from memory.reset import wipe_all_memory


# --- Setup UI directories and check for files ---
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Create directories if they don't exist to prevent startup crash
STATIC_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

# Check for essential files and provide guidance if they are missing
if not (TEMPLATES_DIR / "index.html").exists():
    print("\n[WARNING] 'templates/index.html' not found. The UI will not load.")
    print("          Please ensure you have an 'index.html' file inside the 'templates' directory.\n")


app = FastAPI(title="Neuro-Symbolic Memory Agent")

# Mount static files (for CSS/JS) and templates (for HTML)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# In-memory store for RAM context. In a real multi-user app, use Redis or similar.
ram_context_store = {}

class ChatRequest(BaseModel):
    user_input: str
    session_id: str

@app.on_event("startup")
async def startup_event():
    """Wipe memory from previous runs to start fresh."""
    print("Wiping all memory on startup...")
    wipe_all_memory()
    print("Memory wiped. UI is ready.")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Handles browser requests for the site icon to prevent 404 errors."""
    return Response(status_code=204)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serves the main chat interface HTML page."""
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except TemplateNotFound:
        error_message = """
        <h1>500 - Internal Server Error: Template Not Found</h1>
        <p>The server could not find the <code>index.html</code> file in the <code>templates</code> directory.</p>
        <p><strong>How to fix:</strong> Please make sure you have a directory named <code>templates</code> in your project root, and that <code>index.html</code> is inside it.</p>
        <hr>
        <p>Your project structure should look like this:</p>
        <pre>
neuro_symbolic_memory/
├── templates/
│   └── index.html
├── static/
│   └── main.js
│   └── style.css
└── web_ui.py
... (other files)</pre>
        """
        return HTMLResponse(content=error_message, status_code=500)

@app.post("/api/chat")
async def chat_endpoint(chat_request: ChatRequest):
    """Handles a user's chat message and returns the agent's response."""
    session_id = chat_request.session_id
    user_input = chat_request.user_input

    if session_id not in ram_context_store:
        ram_context_store[session_id] = RAMContext()
    ram_context = ram_context_store[session_id]
    
    ram_context.add(session_id, user_input)

    result = fast_pipe(
        user_input=user_input,
        session_id=session_id,
        ram_context=ram_context,
    )
    return result

@app.get("/api/graph/{session_id}")
async def get_full_graph(session_id: str):
    """Retrieves the entire persisted knowledge graph for a given session."""
    if not DB_PATH.exists():
        return {"nodes": [], "edges": []}
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT DISTINCT src, dst, relation FROM edges WHERE user_id = ?", (session_id,))
        edges_result = cursor.fetchall()
        node_ids = {row['src'] for row in edges_result} | {row['dst'] for row in edges_result}
        nodes = [{"id": node_id, "label": node_id} for node_id in node_ids]
        edges = [{"from": r['src'], "to": r['dst'], "label": r['relation']} for r in edges_result]
        return {"nodes": nodes, "edges": edges}
    except Exception:
        return {"nodes": [], "edges": []}
    finally:
        conn.close()

@app.post("/api/reset")
async def reset_memory(chat_request: ChatRequest):
    """Wipes all memory globally."""
    wipe_all_memory()
    if chat_request.session_id in ram_context_store:
        del ram_context_store[chat_request.session_id]
    return {"status": "success", "message": "All memory has been wiped."}

if __name__ == "__main__":
    print("Starting Neuro-Symbolic Memory UI...")
    print("Open your browser to http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)