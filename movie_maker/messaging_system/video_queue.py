import os
import pika
import toml

from media.media_processor import MediaProcessor
from aws_utils import AWSS3
from logger import get_logger
from constants.paths import LocalPaths

logger = get_logger()


class VideoQueue:
    def __init__(self):
        self._aws_s3 = AWSS3()
        self._settings_aws = toml.load("settings.toml")['aws']
        self._local_media_storage = LocalPaths.INPUT_STORAGE_DIR
        self._rabbitmq_channel = None
        self._settings_rabbitmq = toml.load("settings.toml")['rabbitmq']
        self._rabbitmq_channel = pika.BlockingConnection(
            pika.ConnectionParameters(self._rabbitmq_host)).channel()
        self._rabbitmq_channel.queue_declare(queue=self._queue_name)

    @property
    def _rabbitmq_host(self):
        return self._settings_rabbitmq['host']

    @property
    def _queue_name(self):
        return self._settings_rabbitmq['queue_name']

    @property
    def _s3_uploads_dir(self):
        return self._settings_aws['uploads_path']

    @property
    def _s3_outputs_dir(self):
        return self._settings_aws['outputs_path']

    @property
    def _s3_resources_dir(self):
        return self._settings_aws['resources_path']

    @property
    def _s3_audio_path(self):
        return os.path.join(self._s3_resources_dir, self._resource_audio_name)

    @property
    def _resource_audio_name(self):
        return self._settings_aws['resource_audio_name']

    @property
    def resource_audio_path(self):
        return os.path.join(self._local_media_storage, self._s3_resources_dir, self._resource_audio_name)

    @property
    def _local_input_audio_path(self):
        return os.path.join(LocalPaths.INPUT_STORAGE_DIR, self._s3_resources_dir, self._resource_audio_name)

    def process_videos(self):
        def callback(ch, method, properties, body):
            try:
                video_relative_s3_path = body.decode()
                if video_relative_s3_path == "":
                    logger.info("Received empty message, skipping")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    return

                ch.handle_video(video_relative_s3_path)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logger.error(f"session failed with {e})")
                ch.basic_nack(delivery_tag=method.delivery_tag)


        self._rabbitmq_channel.basic_consume(queue=self._queue_name, on_message_callback=callback)
        logger.info("Audio Processor service is listening to the queue")
        self._rabbitmq_channel.start_consuming()

    def _upload_to_s3(self, output_path, video_relative_path):
        s3_target_output_path = os.path.join(self._s3_outputs_dir, video_relative_path)
        self._aws_s3.upload_file(local_file_path=output_path, s3_path=s3_target_output_path)

    def handle_video(self, video_relative_s3_path):
        logger.info(f"Processing video at relative path {video_relative_s3_path}")
        source_local_video_path = os.path.join(self._local_media_storage, video_relative_s3_path)
        self._download_media(video_relative_s3_path, source_local_video_path)
        source_video_path = os.path.join(self._local_media_storage, video_relative_s3_path)
        result_video_path = MediaProcessor().combine_video_and_audio(video_path=source_video_path,
                                                                     audio_path=self.resource_audio_path)
        self._upload_to_s3(result_video_path, video_relative_s3_path)
        logger.info(f"Processed video saved at {result_video_path}")

    def _download_media(self, video_s3_path: str, local_video_path:str) -> None:
        self._aws_s3.download_file(s3_path=self._s3_audio_path, local_target_path=self.resource_audio_path)
        self._aws_s3.download_file(s3_path=video_s3_path, local_target_path=local_video_path)




if __name__ == "__main__":
    message_queue = VideoQueue()
    message_queue.process_videos()
