import os.path
import threading
import time
import uuid
import asyncio
import pika
import toml
import uvicorn
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import shutil

from aws_utils import AWSS3
from logger import get_logger

logger = get_logger()


class VideoUploadResponse(BaseModel):
    message: str
    video_link: str


class VideoUploader:
    def __init__(self):
        logger.info("initializing VideoUploader")
        self.aws_s3 = AWSS3()
        self.settings_aws = toml.load("settings.toml")['aws']
        self.settings_rabbitmq = toml.load("settings.toml")['rabbitmq']
        self.rabbitmq_channel = None

    @property
    def _uploads_path(self):
        return self.settings_aws['uploads_path']

    @property
    def _bucket_name(self):
        return self.settings_aws['media_bucket_name']

    @property
    def _outputs_path(self):
        return self.settings_aws['outputs_path']

    @property
    def _rabbitmq_host(self):
        return self.settings_rabbitmq['host']

    @property
    def _queue_name(self):
        return self.settings_rabbitmq['queue_name']

    def send_empty_message_to_queue(self):
        while True:
            try:
                self.publish_video_processing_message("")
                logger.info("Sent empty message to the queue")
                time.sleep(10)
            except Exception as e:
                logger.error("Error sending empty message to queue:", e)

    async def upload_video(self, video: UploadFile = File(...)):
        try:
            unique_path = str(uuid.uuid4())
            target_s3_relative_path = os.path.join(unique_path, video.filename)
            target_s3_path = os.path.join(self._uploads_path, target_s3_relative_path)
            return self._send_file_to_process(target_s3_relative_path, target_s3_path, video.file.read())
        except Exception as e:
            logger.error(e)
            return JSONResponse(content={"error": str(e)}, status_code=500)

    def _send_file_to_process(self, target_s3_relative_path: str, target_s3_path: str,
                              input_video: bytes) -> BaseModel:
        logger.info(f"adding {target_s3_path=} to queue for processing")
        self.aws_s3.upload_file_obj(file_obj=input_video, s3_path=target_s3_path)
        self.publish_video_processing_message(target_s3_relative_path)
        video_link = self.get_presigned_url(target_s3_relative_path)
        return VideoUploadResponse(message="Video uploaded successfully", video_link=video_link)

    @classmethod
    def _store_file_locally(cls, source_local_path, video):
        with open(source_local_path, "wb") as f:
            shutil.copyfileobj(video.file, f)

    def publish_video_processing_message(self, message):
        if not self.rabbitmq_channel:
            self.rabbitmq_channel = self._get_rabbitmq_channel()
        self.rabbitmq_channel.basic_publish(exchange='', routing_key='video_processing_queue',
                                            body=message.encode())

    def get_presigned_url(self, target_s3_relative_path):
        output_dir = self._outputs_path
        s3_output_url = f"{os.path.join(output_dir, target_s3_relative_path)}"
        return self.aws_s3.presign_s3_url(s3_output_url)

    def _get_rabbitmq_channel(self):
        rabbitmq_connection = pika.BlockingConnection(pika.ConnectionParameters(host=self._rabbitmq_host))
        rabbitmq_channel = rabbitmq_connection.channel()
        rabbitmq_channel.queue_declare(queue=self._queue_name)
        return rabbitmq_channel


class VideoInputValidator:
    FORMATS = ["video/mp4", "video/avi", "video/x-msvideo", "video/x-ms-wmv", "video/x-matroska", "video/webm"]
    @classmethod
    def validate(cls, video: UploadFile):
        return video.content_type in cls.FORMATS

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



