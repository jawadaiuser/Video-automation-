import os
import subprocess
import uuid
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse
import requests

app = FastAPI()


@app.post("/merge")
async def merge_video(audio: UploadFile = File(...), video_url: str = Form(...)):
    task_id = str(uuid.uuid4())
    audio_path = f"/tmp/{task_id}_audio.mp3"
    video_path = f"/tmp/{task_id}_bg.mp4"
    output_path = f"/tmp/{task_id}_output.mp4"

    try:
        # Save audio file
        with open(audio_path, "wb") as f:
            f.write(await audio.read())

        # Clean URL format (remove extra spaces or brackets)
        clean_url = video_url.strip("[]'\" ")

        # Download video file
        r = requests.get(clean_url, stream=True)
        with open(video_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)

        # Fixed FFmpeg command (No stream_loop crash)
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

        subprocess.run(cmd, check=True)

        return FileResponse(
            output_path, media_type="video/mp4", filename="final_video.mp4"
        )

    finally:
        # Auto cleanup temporary files
        for path in [audio_path, video_path]:
            if os.path.exists(path):
                os.remove(path)
