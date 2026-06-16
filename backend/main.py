from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from devassist.agent import ask, debug, summarize, explain_diff, generate_commit, review_file

app = FastAPI(title="DevAssist API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str

class ErrorRequest(BaseModel):
    error: str

class FileRequest(BaseModel):
    filepath: str

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/api/ask")
async def ask_endpoint(request: QueryRequest):
    try:
        answer = ask(request.question)
        return {"success": True, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/debug")
async def debug_endpoint(request: ErrorRequest):
    try:
        answer = debug(request.error)
        return {"success": True, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/review")
async def review_endpoint(request: FileRequest):
    try:
        answer = review_file(request.filepath)
        return {"success": True, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/summary")
async def summary_endpoint():
    try:
        answer = summarize(".")
        return {"success": True, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/diff")
async def diff_endpoint():
    try:
        answer = explain_diff(".")
        return {"success": True, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/commit")
async def commit_endpoint():
    try:
        answer = generate_commit(".")
        return {"success": True, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)