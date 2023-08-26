import os

import boto3
import toml
from logger import get_logger

logger = get_logger()


class AWSS3:
    def __init__(self):
        config = toml.load("settings.toml")
        self.access_key = config['aws']['access_key']
        self.secret_key = config['aws']['secret_key']
        self._s3 = self._get_s3_client()

    @property
    def _s3_media_bucket_name(self):
        return toml.load("settings.toml")['aws']['media_bucket_name']

    def _get_s3_client(self) -> boto3.client:
        return boto3.client('s3', aws_access_key_id=self.access_key, aws_secret_access_key=self.secret_key)

    def upload_file(self, local_file_path: str, s3_path: str):
        logger.info(f"uploading {local_file_path=} to {s3_path=}")
        self._s3.upload_file(local_file_path, self._s3_media_bucket_name, s3_path)

    def download_file(self, s3_path: str, local_target_path: str):
        logger.info(f"downloading {s3_path=} and saving it to {local_target_path=}")

        self._mkdir_if_not_exist(local_target_path)
        self._s3.download_file(self._s3_media_bucket_name, s3_path, local_target_path)

    @staticmethod
    def _mkdir_if_not_exist(local_target_path):
        target_dir = os.path.dirname(local_target_path)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

    def is_file_exist(self, s3_path: str) -> bool:
        bucket_name = self._s3_media_bucket_name
        try:
            self._s3.head_object(Bucket=bucket_name, Key=s3_path)
        except Exception as e:
            logger.warning(e)
            return False
        return True
