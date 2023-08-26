import os

from moviepy.editor import afx
import pika
import toml

from aws_utils import AWSS3
from logger import get_logger
from moviepy.audio.AudioClip import CompositeAudioClip
from moviepy.editor import VideoFileClip, AudioFileClip
from constants.paths import LocalPaths

logger = get_logger()


class VideoProcessor:
    VIDEO_VOLUME = 0.8
    AUDIO_VOLUME = 0.2
    CODEC = "libx264"
    AUDIO_CODEC = "aac"

    def __init__(self, skip_rabbit: bool = False):
        self._aws_s3 = AWSS3()
        self._settings_aws = toml.load("settings.toml")['aws']
        self._input_media_storage = LocalPaths.INPUT_STORAGE_DIR
        self._output_result_dir = LocalPaths.OUTPUT_RESULT_DIR
        if not skip_rabbit:
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
    def _resource_audio_path(self):
        return os.path.join(self._input_media_storage, self._s3_resources_dir, self._resource_audio_name)

    @property
    def _local_input_audio_path(self):
        return os.path.join(LocalPaths.INPUT_STORAGE_DIR, self._s3_resources_dir, self._resource_audio_name)

    def process_videos(self):
        def callback(ch, method, properties, body):
            try:
                video_relative_path = body.decode()
                if video_relative_path == "":
                    logger.info("Received empty message, skipping")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    return

                logger.info(f"Processing video at relative path {video_relative_path}")
                output_path = self.process_video_with_music(video_relative_path)
                self._upload_to_s3(output_path, video_relative_path)
                logger.info(f"Processed video saved at {output_path}")
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

    def process_video_with_music(self, video_path) -> str:
        source_local_video_path = os.path.join(self._input_media_storage, video_path)
        result_local_output_path = os.path.join(self._output_result_dir, video_path)
        source_s3_video_path = os.path.join(self._s3_uploads_dir, video_path)
        self._download_media(source_local_video_path, source_s3_video_path)
        self._process_media(result_local_output_path, source_local_video_path, self._local_input_audio_path)
        return result_local_output_path

    def _process_media(self, result_video_path: str, video_path: str, audio_path: str):
        logger.info("start processing clip")
        with VideoFileClip(video_path) as video_clip, \
                AudioFileClip(audio_path) as audio_clip:
            audio_clip, video_clip = self._adjust_media_volume(audio_clip, video_clip)
            audio_clip = self._adjust_audio_duration(audio_clip, video_clip)
            final_audio, video_clip = self.merge_video_with_audio(audio_clip, video_clip)
            self._save_result_video(result_video_path, video_clip)

    def _save_result_video(self, result_local_output_path, video_clip):
        os.makedirs(os.path.dirname(result_local_output_path), exist_ok=True)
        video_clip.write_videofile(result_local_output_path, codec=self.CODEC, audio_codec=self.AUDIO_CODEC)

    def merge_video_with_audio(self, audio_clip: AudioFileClip, video_clip: VideoFileClip) -> [AudioFileClip,
                                                                                               VideoFileClip]:
        final_audio = CompositeAudioClip([video_clip.audio, audio_clip])
        video_clip = video_clip.set_audio(final_audio)
        return final_audio, video_clip

    def _adjust_audio_duration(self, audio_clip: AudioFileClip, video_clip: VideoFileClip) -> AudioFileClip:
        if audio_clip.duration < video_clip.duration:
            audio_clip = afx.audio_loop( audio_clip, duration=video_clip.duration)
        elif audio_clip.duration > video_clip.duration:
            audio_clip = audio_clip.subclip(0, video_clip.duration)
        return audio_clip


    def _adjust_media_volume(self, audio_clip: AudioFileClip, video_clip: VideoFileClip):
        video_clip = video_clip.volumex(self.VIDEO_VOLUME)
        audio_clip = audio_clip.volumex(self.AUDIO_VOLUME)
        return audio_clip, video_clip

    def _download_media(self, resource_local_output_path: str, source_s3_video_path: str) -> None:
        self._aws_s3.download_file(s3_path=self._s3_audio_path, local_target_path=self._resource_audio_path)
        self._aws_s3.download_file(s3_path=source_s3_video_path, local_target_path=resource_local_output_path)


if __name__ == "__main__":
    video_processor = VideoProcessor()
    video_processor.process_videos()
