
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
import yt_dlp
import aiohttp
import os

app = FastAPI()

# --- CONFIGURATION ---
# We use a specific iPhone User-Agent for EVERYTHING
# This tricks YouTube into thinking the request comes from the mobile app
USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"

print(f"📂 Current Folder: {os.getcwd()}")
if os.path.exists("cookies.txt"):
    print("✅ Cookies.txt found and loaded.")
    COOKIE_FILE = "cookies.txt"
else:
    print("⚠️ Cookies.txt MISSING.")
    COOKIE_FILE = None

async def get_stream_link(url: str, format_type: str):
    ydl_opts = {
        'format': 'bestaudio/best' if format_type == 'audio' else 'best[ext=mp4]/best',
        'quiet': True,
        'geo_bypass': True,
        'nocheckcertificate': True,
        
        # 1. Use IPv6 (YouTube trusts it more)
        'source_address': '::', 
        
        # 2. Use Cookies
        'cookiefile': COOKIE_FILE,
        
        # 3. CRITICAL: Force iOS Client
        'extractor_args': {
            'youtube': {
                'player_client': ['ios'],
                'player_skip': ['webpage', 'configs', 'js'], 
            }
        },
        
        # 4. CRITICAL: Match the User Agent
        'user_agent': USER_AGENT,
        
        # 5. Speed Fix
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
    # 6. CRITICAL: Use the SAME User-Agent for downloading
    headers = {"User-Agent": USER_AGENT}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            # If YouTube returns 403/429, we must not send 200 OK to the bot
            if resp.status != 200:
                print(f"❌ YouTube Stream Error: {resp.status}")
                # We yield nothing, forcing the bot to detect a small/empty file
                return 
            
            async for chunk in resp.content.iter_chunked(4096):
                yield chunk

@app.get("/")
def home():
    return {"status": "Online", "mode": "iOS Spoofing"}

@app.get("/audio")
async def audio_dl(url: str):
    print(f"🎵 Audio Request: {url}")
    link = await get_stream_link(url, 'audio')
    
    if not link:
        return JSONResponse(status_code=500, content={"error": "Could not extract link"})
    
    # We pass the generator. If YouTube blocks it, the bot will see a small file and handle it.
    return StreamingResponse(stream_generator(link), media_type="audio/mpeg")

@app.get("/download")
async def video_dl(url: str):
    print(f"🎬 Video Request: {url}")
    link = await get_stream_link(url, 'video')
    if not link:
        return JSONResponse(status_code=500, content={"error": "Could not extract link"})
    return StreamingResponse(stream_generator(link), media_type="video/mp4")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
