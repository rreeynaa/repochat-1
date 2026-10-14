"""
Convenience entry point: starts the FastAPI backend.

Usage:
    python run.py

Then, in a second terminal, start the frontend:
    streamlit run frontend/app.py
"""

import uvicorn

from backend.config import settings

if __name__ == "__main__":
    problems = settings.validate()
    if problems:
        print("Configuration warnings:")
        for p in problems:
            print(f"  - {p}")
        print()

    uvicorn.run("backend.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)
