# Backend configuration for Genie AI Smart Home Assistant

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = "sqlite:///./genie.db"

# API configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Server configuration
HOST = "0.0.0.0"
PORT = 8000

# CORS origins
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
] 