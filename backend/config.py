import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # MongoDB Atlas connection
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb+srv://your-atlas-connection')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'smart_weld_blogs')
    
    # Use environment port for GCP
    PORT = int(os.getenv('PORT', 8080))
    
    # API Keys
    BRAVE_API_KEY = os.getenv('BRAVE_API_KEY')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # CORS settings for production
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')

    #gemini-1#AIzaSyC6eKmNSTsxqY_nsH1Iju7AYsRCUk_9jzs
    #gemini-2#AIzaSyC716kanHwjTw3lAUoa2iFW3FfB-hBD1_g
    #gemini-3#AIzaSyCO23rHlEdIpG3jKXJIqm5U1gOh3kIQWBA
    #gemini-4#AIzaSyDX2aHHE91DtoklP-HyUb3LFhTltSsN0_4
    #gemini-5#AIzaSyBORYkuCmYXa2QK0BnHcYVHOjyoy-5MxPY
    #gemini-6#AIzaSyAucwImQqkK305IEcoE2_0Qp-dEfXk1T8w