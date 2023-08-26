import requests

from api.aws_utils import AWSS3

def test_presign_s3_url():
    aws_s3 = AWSS3()
    url = aws_s3.presign_s3_url("tests/downloadable.txt", expires_in=10)
    assert requests.get(url).text == "just some text"

def test_upload_file_obj():
    aws_s3 = AWSS3()
    s3_relative_path = "tests/uploaded.txt"
    expected_text = "just some text for obj"
    aws_s3.upload_file_obj(expected_text.encode(), s3_relative_path)
    url = aws_s3.presign_s3_url(s3_path=s3_relative_path, expires_in=10)
    assert requests.get(url).text == expected_text