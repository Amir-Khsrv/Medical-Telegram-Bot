# run.py
import uvicorn
from main import app  # Import the FastAPI app from the main file

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
