import os
from moviepy.editor import afx
from moviepy.audio.AudioClip import CompositeAudioClip
from moviepy.editor import VideoFileClip, AudioFileClip

from constants.paths import LocalPaths
from logger import get_logger
logger = get_logger()


class MediaProcessor:
    VIDEO_VOLUME = 0.8
    AUDIO_VOLUME = 0.2
    CODEC = "libx264"
    AUDIO_CODEC = "aac"

    def __init__(self):
        self._output_result_dir = LocalPaths.OUTPUT_RESULT_DIR


    def combine_video_and_audio(self, video_path:str, audio_path:str) -> str:
        result_local_output_path = video_path.replace("input/", "output/")
        logger.info(f"{result_local_output_path=} ,{video_path=}")
        self._process_media(result_local_output_path, video_path, audio_path)
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
