import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
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
    ydl_opts = {
        'format': 'bestaudio/best' if format_type == 'audio' else 'best',
        'quiet': True,
        'geo_bypass': True,
        'nocheckcertificate': True,
        'source_address': '0.0.0.0', # Fix for Koyeb IPv6 issues
        'cookiefile': COOKIE_FILE, 
        # Spoof User Agent to look like a real PC
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info['url']
    except Exception as e:
        print(f"❌ Extraction Error: {e}")
        return None

async def stream_generator(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            async for chunk in resp.content.iter_chunked(4096):
                yield chunk

# --- API ENDPOINTS (Do not delete these!) ---

@app.get("/")
def home():
    return {
        "status": "Online", 
        "cookies": "Loaded" if COOKIE_FILE else "Missing",
        "message": "Bot is ready to download."
    }

@app.get("/audio")
async def audio_dl(url: str):
    print(f"🎵 Requesting Audio: {url}")
    stream_url = await get_stream_link(url, 'audio')
    
    if not stream_url:
        return JSONResponse(status_code=500, content={"error": "YouTube Blocked the request or Link is Invalid."})
    
    return StreamingResponse(stream_generator(stream_url), media_type="audio/mpeg")

@app.get("/download")
async def video_dl(url: str):
    print(f"🎬 Requesting Video: {url}")
    stream_url = await get_stream_link(url, 'video')
    
    if not stream_url:
        return JSONResponse(status_code=500, content={"error": "YouTube Blocked the request or Link is Invalid."})
    
    return StreamingResponse(stream_generator(stream_url), media_type="video/mp4")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
