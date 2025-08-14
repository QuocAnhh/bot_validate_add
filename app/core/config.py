import os
from dotenv import load_dotenv

load_dotenv()

GOONG_API_KEY = os.getenv("GOONG_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 
DATABASE_URL = os.getenv("DATABASE_URL") 