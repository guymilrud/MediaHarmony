import asyncio
import threading

import uvicorn
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

from logger import get_logger
from video_publisher import VideoUploader, VideoUploadResponse, VideoInputValidator

logger = get_logger()
app = FastAPI()
video_uploader = VideoUploader()


@app.post("/upload/", response_model=VideoUploadResponse)
async def upload_video(video: UploadFile = File(...)):
    logger.info(f"received {video.filename=} for upload")

    if VideoInputValidator.validate(video):
        return await video_uploader.upload_video(video)
    else:
        return JSONResponse(content={"error": "Invalid video format"}, status_code=400)

def main():
    empty_message_thread = threading.Thread(target=video_uploader.send_empty_message_to_queue)
    empty_message_thread.start()
    asyncio.run(uvicorn.run(app, host="0.0.0.0", port=5000))
    empty_message_thread.join()




if __name__ == "__main__":
    logger.info(f"Running API server")
    main()



