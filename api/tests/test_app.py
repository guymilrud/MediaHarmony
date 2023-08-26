import os
import pytest
from fastapi.testclient import TestClient

from routes import app
from video_publisher import VideoUploader

client = TestClient(app)

@pytest.fixture
def video_uploader():
    return VideoUploader()

def test_upload_video_invalid_format(video_uploader):
    file_path = os.path.join(os.path.dirname(__file__),'resources', 'dummy.txt')
    with open(file_path, 'rb') as f:
        response = client.post('/upload/', files={'video': f})
    assert response.status_code == 400
    assert response.json()['error'] == 'Invalid video format'


def test_upload_fake_mp4_invalid_format(video_uploader):
    file_path = os.path.join(os.path.dirname(__file__),'resources', 'dummy.mp3')
    with open(file_path, 'rb') as f:
        response = client.post('/upload/', files={'video': f})
    assert response.status_code == 400
    assert response.json()['error'] == 'Invalid video format'
