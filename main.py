from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
import subprocess
import uuid
import os
import requests

app = FastAPI()

@app.post("/merge")
async def merge_video(
    audio: UploadFile = File(...),
    video_url: str = Form(...)
):
    task_id = str(uuid.uuid4())
    audio_path = f"/tmp/{task_id}_audio.mp3"
    video_path = f"/tmp/{task_id}_bg.mp4"
    output_path = f"/tmp/{task_id}_output.mp4"

    # Save incoming audio file
    with open(audio_path, "wb") as f:
        f.write(await audio.read())

    # Download background video from provided URL
    r = requests.get(video_url, stream=True)
    with open(video_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024*1024):
            f.write(chunk)

    # FFmpeg instant merge
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_path
    ]
    subprocess.run(cmd, check=True)

    return FileResponse(output_path, media_type="video/mp4", filename="final_video.mp4")
