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

@app.get("/api/graph")
async def get_graph():
    """Returns the entire knowledge graph for visualization (Neo4j)."""
    try:
        from memory.neo4j_store import Neo4jMemoryStore
        store = Neo4jMemoryStore()
        
        # Fetch all nodes and edges
        # Note: In a production app with huge graphs, you'd never do "MATCH (n) RETURN n"
        # You would fetch a subgraph or use pagination.
        with store.driver.session() as session:
            # Get nodes
            node_result = session.run("MATCH (n:Entity) RETURN n.id as id, n.type as type")
            nodes = [{"id": r["id"], "group": 1} for r in node_result]
            
            # Get edges
            edge_result = session.run("MATCH (s:Entity)-[r]->(d:Entity) RETURN s.id as src, d.id as dst, type(r) as label")
            links = [{"source": r["src"], "target": r["dst"], "label": r["label"]} for r in edge_result]
            
        store.close()
        return {"nodes": nodes, "links": links}

    except Exception as e:
        print(f"Graph retrieval error: {e}")
        return {"nodes": [], "links": []}


@app.post("/api/reset")
async def reset_memory():
    """Wipes all memory (RAM, SQLite, Chroma, Neo4j)."""
    wipe_all_memory()
    # Clear RAM contexts
    ram_context_store.clear()
    return {"status": "ok", "message": "All memories wiped successfully."}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)