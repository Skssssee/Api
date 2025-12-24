import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
import yt_dlp
import aiohttp
import os

app = FastAPI()

# --- DEBUG & SETUP ---
print("\n" + "="*30)
print(f"📂 Current Folder: {os.getcwd()}")
print(f"📄 Files Found: {os.listdir(os.getcwd())}")
print("="*30 + "\n")

if os.path.exists("cookies.txt"):
    print("✅ Cookies.txt found! Loading...")
    COOKIE_FILE = "cookies.txt"
else:
    print("❌ ERROR: cookies.txt is MISSING! You will likely get blocked.")
    COOKIE_FILE = None

async def get_stream_link(url: str, format_type: str):
    # 1. Select Format
    if format_type == 'audio':
        fmt = 'bestaudio/best'
    else:
        # We try to get an MP4. If not available, we accept 'best' (any format)
        # to avoid the "Requested format not available" error.
        fmt = 'best[ext=mp4]/best'

    ydl_opts = {
        'format': fmt,
        'quiet': True,
        'geo_bypass': True,
        'nocheckcertificate': True,
        'source_address': '0.0.0.0', 
        'cookiefile': COOKIE_FILE,
        
        # --- THE FIX: USE iOS CLIENT ---
        # Android failed with cookies. iOS works well with cookies.
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'web'],
                'player_skip': ['webpage', 'configs', 'js'], 
            }
        },
        
        # Enable Node.js (Speed Fix)
        'params': {
            'js_runtimes': ['node'],
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info['url']
    except Exception as e:
        print(f"❌ Extraction Error: {e}")
        return None

async def stream_generator(url: str):
    # Use iOS User-Agent to match the client we spoofed
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            async for chunk in resp.content.iter_chunked(4096):
                yield chunk

# --- ENDPOINTS ---

@app.get("/")
def home():
    return {"status": "Online", "cookies": "Loaded" if COOKIE_FILE else "Missing"}

@app.get("/audio")
async def audio_dl(url: str):
    print(f"🎵 Audio Request: {url}")
    stream_url = await get_stream_link(url, 'audio')
    
    if not stream_url:
        return JSONResponse(status_code=500, content={"error": "Failed to get Audio Link"})
    
    return StreamingResponse(stream_generator(stream_url), media_type="audio/mpeg")

@app.get("/download")
async def video_dl(url: str):
    print(f"🎬 Video Request: {url}")
    stream_url = await get_stream_link(url, 'video')
    
    if not stream_url:
        return JSONResponse(status_code=500, content={"error": "Failed to get Video Link"})
    
    return StreamingResponse(stream_generator(stream_url), media_type="video/mp4")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
