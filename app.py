"""PropertyVision full-stack entrypoint note.

Run the backend:
    uvicorn backend.main:app --reload

Run the frontend:
    cd frontend
    npm run dev
"""


def main() -> None:
    print("PropertyVision runs as FastAPI + React.")
    print("Backend:  uvicorn backend.main:app --reload")
    print("Frontend: cd frontend && npm run dev")
    print("Demo URL: http://localhost:5173")


if __name__ == "__main__":
    main()
