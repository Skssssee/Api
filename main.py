import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import yt_dlp
import aiohttp
import os

app = FastAPI()

# --- DEBUGGING: PRINT ALL FILES ---
print("\n" + "="*30)
print(f"📂 Current Folder: {os.getcwd()}")
print(f"📄 Files Found: {os.listdir(os.getcwd())}")
print("="*30 + "\n")
# ----------------------------------

# Check for cookies
if os.path.exists("cookies.txt"):
    print("✅ SUCCESS: Cookies.txt found! Loading...")
    COOKIE_FILE = "cookies.txt"
else:
    print("❌ ERROR: cookies.txt is MISSING from this folder!")
    COOKIE_FILE = None

async def get_stream_link(url: str, format_type: str):
    # ... (Keep the rest of your code the same as before)
    # ... ensure 'cookiefile': COOKIE_FILE is inside ydl_opts
    ydl_opts = {
        'format': 'bestaudio/best' if format_type == 'audio' else 'best',
        'quiet': True,
        'geo_bypass': True,
        'nocheckcertificate': True,
        'source_address': '0.0.0.0',
        'cookiefile': COOKIE_FILE, 
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info['url']
    except Exception as e:
        print(f"❌ Extraction Error: {e}")
        return None

# ... (Keep the rest of your API endpoints: stream_generator, /audio, /download)
# ...
