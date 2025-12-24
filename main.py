
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
import yt_dlp
import aiohttp
import os

app = FastAPI()

# --- SETUP ---
print(f"📂 Current Folder: {os.getcwd()}")
# We INTENTIONALLY ignore cookies for Android TV mode
COOKIE_FILE = None 
print("ℹ️ Mode: Android TV (Cookies Disabled to prevent conflicts)")

async def get_stream_link(url: str, format_type: str):
    ydl_opts = {
        'format': 'bestaudio/best' if format_type == 'audio' else 'best[ext=mp4]/best',
        'quiet': True,
        'geo_bypass': True,
        'nocheckcertificate': True,
        
        # 1. Use IPv6 (Crucial for Cloud Servers)
        'source_address': '::', 
        
        # 2. DISABLE Cookies (They cause conflicts with TV client)
        'cookiefile': None,
        
        # 3. FORCE Android TV Client
        # This client is whitelisted by YouTube and rarely gets "Sign in" blocks
        'extractor_args': {
            'youtube': {
                'player_client': ['android_tv'],
                'player_skip': ['webpage', 'configs', 'js'], 
            }
        },
        
        # 4. Speed Fix (Node.js)
        'params': {'js_runtimes': ['node']},
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info['url']
    except Exception as e:
        print(f"❌ Extraction Error: {e}")
        return None

async def stream_generator(url: str):
    # Use a generic User-Agent for the download part
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            # Check for immediate blocks
            if resp.status != 200:
                print(f"❌ Stream Error: {resp.status}")
                return
                
            async for chunk in resp.content.iter_chunked(4096):
                yield chunk

@app.get("/")
def home():
    return {"status": "Online", "mode": "Android TV"}

@app.get("/audio")
async def audio_dl(url: str):
    print(f"🎵 Audio Request: {url}")
    link = await get_stream_link(url, 'audio')
    if not link:
        return JSONResponse(status_code=500, content={"error": "Blocked"})
    return StreamingResponse(stream_generator(link), media_type="audio/mpeg")

@app.get("/download")
async def video_dl(url: str):
    print(f"🎬 Video Request: {url}")
    link = await get_stream_link(url, 'video')
    if not link:
        return JSONResponse(status_code=500, content={"error": "Blocked"})
    return StreamingResponse(stream_generator(link), media_type="video/mp4")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
