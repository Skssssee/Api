import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
import yt_dlp
import aiohttp
import os

app = FastAPI()

# Checks if cookies.txt exists in the repo
COOKIE_FILE = "cookies.txt" if os.path.exists("cookies.txt") else None

async def get_stream_link(url: str, format_type: str):
    ydl_opts = {
        'format': 'bestaudio/best' if format_type == 'audio' else 'best',
        'quiet': True,
        'geo_bypass': True,
        'nocheckcertificate': True,
        # TRICK: Mimic an Android Phone to bypass "Sign in to confirm"
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
                'player_skip': ['webpage', 'configs', 'js'], 
            }
        },
    }

    if COOKIE_FILE:
        ydl_opts['cookiefile'] = COOKIE_FILE

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info['url']
    except Exception as e:
        print(f"Error: {e}")
        return None

async def stream_generator(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            async for chunk in resp.content.iter_chunked(4096):
                yield chunk

@app.get("/")
def home():
    return {"status": "Online", "mode": "Private API"}

@app.get("/audio")
async def audio_dl(url: str):
    stream_url = await get_stream_link(url, 'audio')
    if not stream_url:
        raise HTTPException(status_code=500, detail="Failed to get YouTube Link")
    return StreamingResponse(stream_generator(stream_url), media_type="audio/mpeg")

@app.get("/download")
async def video_dl(url: str):
    stream_url = await get_stream_link(url, 'video')
    if not stream_url:
        raise HTTPException(status_code=500, detail="Failed to get YouTube Link")
    return StreamingResponse(stream_generator(stream_url), media_type="video/mp4")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
