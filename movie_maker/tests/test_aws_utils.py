import os

from movie_maker.aws_utils import AWSS3

this_path = os.path.dirname(os.path.abspath(__file__))


def test_upload_file():
    aws_s3 = AWSS3()
    s3_path = "tests/dummy.txt"
    source_path = os.path.join(this_path, "resources/dummy.txt")
    aws_s3.upload_file(source_path, s3_path)
    assert aws_s3.is_file_exist(s3_path)



def test_download_file():
    result_path = os.path.join(this_path, "output/downloadable.txt")
    try:
        aws_s3 = AWSS3()
        aws_s3._mkdir_if_not_exist(os.path.join(this_path, "output"))

        aws_s3.download_file("tests/downloadable.txt", result_path)
    finally:
        assert os.path.exists(result_path)
        os.remove(result_path)
