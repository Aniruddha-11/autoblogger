import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'smart_weld_blogs')
    PORT = int(os.getenv('PORT', 5000))
    BRAVE_API_KEY = os.getenv('BRAVE_API_KEY', 'BSATRAeU0Vn6uaehAfipECBb5i_absd')  # Add your Brave API key
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyC6eKmNSTsxqY_nsH1Iju7AYsRCUk_9jzs')

    #gemini-1#AIzaSyC6eKmNSTsxqY_nsH1Iju7AYsRCUk_9jzs
    #gemini-2#AIzaSyC716kanHwjTw3lAUoa2iFW3FfB-hBD1_g
    #gemini-3#AIzaSyCO23rHlEdIpG3jKXJIqm5U1gOh3kIQWBA