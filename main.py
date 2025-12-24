
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
import yt_dlp
import aiohttp
import os

app = FastAPI()

# --- CONFIGURATION (Reverted to Stable) ---
print(f"📂 Current Folder: {os.getcwd()}")

if os.path.exists("cookies.txt"):
    print("✅ Cookies.txt found and loaded.")
    COOKIE_FILE = "cookies.txt"
else:
    print("⚠️ Cookies.txt MISSING.")
    COOKIE_FILE = None

async def get_stream_link(url: str, format_type: str):
    ydl_opts = {
        # 1. Standard Format Selection
        'format': 'bestaudio/best' if format_type == 'audio' else 'best[ext=mp4]/best',
        'quiet': True,
        'geo_bypass': True,
        'nocheckcertificate': True,
        
        # 2. Use IPv6 (This allows Cloud Servers to bypass some blocks)
        'source_address': '::', 
        
        # 3. Use Cookies (The only way to bypass "Sign In")
        'cookiefile': COOKIE_FILE,
        
        # 4. REMOVED "extractor_args" to stop the "Skipping client" errors.
        # We let yt-dlp use the default 'web' client which SUPPORTS cookies.
        
        # 5. Speed Fix (Node.js) - Critical
        'params': {'js_runtimes': ['node']},
        
        # 6. Standard Browser User Agent (Matches your cookies)
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
    # Use the same Browser User-Agent for downloading
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                print(f"❌ Stream Error: {resp.status}")
                return
            async for chunk in resp.content.iter_chunked(4096):
                yield chunk

@app.get("/")
def home():
    return {"status": "Online", "mode": "Stable Web + Cookies"}

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
