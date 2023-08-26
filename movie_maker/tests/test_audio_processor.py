import os
import pytest
from moviepy.editor import VideoFileClip, AudioFileClip
from movie_maker.aws_utils import AWSS3
from movie_maker.audio_processor import VideoProcessor


@pytest.fixture
def video_processor():
    return VideoProcessor(skip_rabbit=True)


@pytest.fixture
def test_long_video_file():
    return os.path.join(os.path.dirname(__file__), 'resources', 'English Lesson.mp4')


@pytest.fixture
def test_short_video_file():
    return os.path.join(os.path.dirname(__file__), 'resources', "1-Minute Meditation.mp4")


@pytest.fixture
def test_music_file():
    return os.path.join(os.path.dirname(__file__), 'resources', 'test_music.mp3')


@pytest.fixture
def output_dir():
    return os.path.join(os.path.dirname(__file__), 'output')


@pytest.fixture
def result_long_video_path():
    return os.path.join(os.path.dirname(__file__), 'output', 'result_long.mp4')


@pytest.fixture
def result_short_video_path():
    return os.path.join(os.path.dirname(__file__), 'output', 'result_short.mp4')


@pytest.fixture
def expected_long_video_path():
    return os.path.join(os.path.dirname(__file__), 'resources', 'expected_result_long.mp4')


@pytest.fixture
def expected_short_video_path():
    return os.path.join(os.path.dirname(__file__), 'resources', 'expected_result_short.mp4')


@pytest.fixture
def aws_s3():
    return AWSS3()


def test_video_longer_than_music(output_dir,
                                 video_processor,
                                 result_long_video_path,
                                 test_long_video_file,
                                 test_music_file,
                                 aws_s3,
                                 expected_long_video_path):
    aws_s3._mkdir_if_not_exist(output_dir)
    video_processor._process_media(result_video_path=result_long_video_path, video_path=test_long_video_file,
                                   audio_path=test_music_file)

    with VideoFileClip(result_long_video_path) as video_clip, \
            VideoFileClip(expected_long_video_path) as expected_video_clip:
        assert video_clip.duration == expected_video_clip.duration


def test_video_shorter_than_music(output_dir,
                                  video_processor,
                                  result_short_video_path,
                                  test_short_video_file,
                                  test_music_file,
                                  aws_s3,
                                  expected_short_video_path):
    aws_s3._mkdir_if_not_exist(output_dir)
    video_processor._process_media(result_video_path=result_short_video_path, video_path=test_short_video_file,
                                   audio_path=test_music_file)

    with VideoFileClip(result_short_video_path) as video_clip, \
            VideoFileClip(expected_short_video_path) as expected_video_clip:
        assert video_clip.duration == expected_video_clip.duration
