import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from json_api import app

# Add CORS middleware with proper WebSocket support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "ws://localhost:5173", "ws://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def main():
    uvicorn.run(
        "json_api:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
