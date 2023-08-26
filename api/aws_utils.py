import os
from io import BytesIO

import boto3
import toml
from logger import get_logger

logger = get_logger()


class AWSS3:
    def __init__(self):
        self.settings_aws = toml.load("settings.toml")['aws']
        self.access_key = self.settings_aws['access_key']
        self.secret_key = self.settings_aws['secret_key']
        self._s3 = self._get_s3_client()

    @property
    def _s3_media_bucket_name(self):
        return self.settings_aws['media_bucket_name']

    def _get_s3_client(self):
        return boto3.client('s3', aws_access_key_id=self.access_key, aws_secret_access_key=self.secret_key)

    def upload_file(self, local_file_path: str, s3_path: str):
        logger.info(f"uploading {local_file_path=} to {s3_path=}")
        bucket_name = self._s3_media_bucket_name

        self._s3.upload_file(local_file_path, bucket_name, s3_path)

    def upload_file_obj(self, file_obj: bytes, s3_path: str):
        logger.info(f"uploading {s3_path=}")
        bucket_name = self._s3_media_bucket_name

        self._s3.upload_fileobj(BytesIO(file_obj), bucket_name, s3_path)

    def presign_s3_url(self, s3_path: str, expires_in: int = 3600) -> str:
        bucket_name = self._s3_media_bucket_name
        return self._s3.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': s3_path},
                                         ExpiresIn=expires_in)
