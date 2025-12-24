
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
import yt_dlp
import aiohttp
import os

app = FastAPI()

# Check cookies
if os.path.exists("cookies.txt"):
    print("✅ Cookies loaded")
    COOKIE_FILE = "cookies.txt"
else:
    print("⚠️ No cookies found")
    COOKIE_FILE = None

async def get_stream_link(url: str, format_type: str):
    ydl_opts = {
        'format': 'bestaudio/best' if format_type == 'audio' else 'best',
        'quiet': True,
        'geo_bypass': True,
        'nocheckcertificate': True,
        'source_address': '0.0.0.0', 
        'cookiefile': COOKIE_FILE,
        
        # --- NEW SETTINGS FROM WIKI ---
        # 1. Force use of Node.js
        # 2. Use Android client to mimic mobile
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
                'player_skip': ['webpage', 'configs', 'js'],
            }
        },
        # Explicitly tell yt-dlp to use the Node we installed
        'params': {
            'js_runtimes': ['node'],
        }
        # ------------------------------
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info['url']
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

async def stream_generator(url: str):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            async for chunk in resp.content.iter_chunked(4096):
                yield chunk

@app.get("/")
def home():
    return {"status": "Online"}

@app.get("/audio")
async def audio_dl(url: str):
    link = await get_stream_link(url, 'audio')
    if not link: return JSONResponse(status_code=500, content={"error": "Failed"})
    return StreamingResponse(stream_generator(link), media_type="audio/mpeg")

@app.get("/download")
async def video_dl(url: str):
    link = await get_stream_link(url, 'video')
    if not link: return JSONResponse(status_code=500, content={"error": "Failed"})
    return StreamingResponse(stream_generator(link), media_type="video/mp4")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
