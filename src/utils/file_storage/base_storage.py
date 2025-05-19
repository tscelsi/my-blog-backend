import abc
import logging

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class S3Credentials(BaseSettings):
    AWS_SECRET_ACCESS_KEY: str
    AWS_ACCESS_KEY_ID: str
    AWS_REGION: str = "eu-west-2"


class AbstractFileStorage(abc.ABC):
    @abc.abstractmethod
    async def save(self, key: str, data: bytes):
        pass

    @abc.abstractmethod
    async def remove(self, key: str):
        pass

    @abc.abstractmethod
    async def generate_presigned_url(self, key: str) -> str:
        pass
