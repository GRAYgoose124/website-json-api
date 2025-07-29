import uvicorn
from json_api import app

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
