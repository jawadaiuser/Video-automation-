import os
import subprocess
import uuid
import requests
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

app = FastAPI()


@app.post("/merge")
async def merge_video(audio: UploadFile = File(...), video_url: str = Form(...)):
    task_id = str(uuid.uuid4())
    audio_path = f"/tmp/{task_id}_audio.mp3"
    video_path = f"/tmp/{task_id}_bg.mp4"
    output_path = f"/tmp/{task_id}_output.mp4"

    try:
        # 1. Save uploaded audio file
        with open(audio_path, "wb") as f:
            f.write(await audio.read())

        # 2. Clean URL and set User-Agent header
        clean_url = video_url.strip("[]'\" ")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        # 3. Download Video
        response = requests.get(
            clean_url, headers=headers, stream=True, timeout=30
        )
        if response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Video download failed with HTTP status {response.status_code}",
            )

        with open(video_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

        # Check if downloaded file is valid
        if os.path.getsize(video_path) < 1000:
            raise HTTPException(
                status_code=400, detail="Downloaded video file is corrupt or empty."
            )

        # 4. FFmpeg Command (No stream_loop)
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-i",
            audio_path,
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-shortest",
            output_path,
        ]

        process = subprocess.run(cmd, capture_output=True, text=True)
        if process.returncode != 0:
            raise HTTPException(
                status_code=500, detail=f"FFmpeg Error: {process.stderr}"
            )

        return FileResponse(
            output_path, media_type="video/mp4", filename="final_video.mp4"
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Cleanup temporary input files
        for path in [audio_path, video_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass
