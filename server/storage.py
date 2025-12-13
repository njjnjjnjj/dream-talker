import os
import abc
import io
import logging
from datetime import datetime
from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)

class StorageBackend(abc.ABC):
    """
    存储后端抽象基类。
    定义了保存和获取文件的标准接口。
    """

    @abc.abstractmethod
    def save(self, data: bytes, filename: str) -> str:
        """
        保存数据到存储后端。
        :param data: 要保存的二进制数据
        :param filename: 文件名（建议包含相对路径以避免冲突）
        :return: 文件的访问路径或标识符 (例如相对路径或对象 Key)
        """
        pass

    @abc.abstractmethod
    def get_url(self, file_path: str) -> str:
        """
        获取文件的访问 URL 或路径。
        :param file_path: save 方法返回的文件标识符
        :return: 可直接访问或用于读取的路径/URL
        """
        pass

    @abc.abstractmethod
    def get_stream(self, file_path: str):
        """
        获取文件内容流。
        :return: 一个可读的文件对象或生成器
        """
        pass
    
    @abc.abstractmethod
    def exists(self, file_path: str) -> bool:
        """
        检查文件是否存在。
        """
        pass

class LocalStorage(StorageBackend):
    """
    本地文件系统存储实现。
    """
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    def save(self, data: bytes, filename: str) -> str:
        # 确保目录存在
        full_path = os.path.join(self.base_dir, filename)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, "wb") as f:
            f.write(data)
        
        return filename # 对于本地存储，我们存储相对路径

    def get_url(self, file_path: str) -> str:
        # 对于本地存储，返回相对路径，由 API 负责组装完整路径或提供文件流
        return file_path

    def get_stream(self, file_path: str):
        full_path = os.path.join(self.base_dir, file_path)
        if not os.path.exists(full_path):
            return None
        return open(full_path, "rb")
    
    def exists(self, file_path: str) -> bool:
        full_path = os.path.join(self.base_dir, file_path)
        return os.path.exists(full_path)

class MinioStorage(StorageBackend):
    """
    MinIO 对象存储实现。
    """
    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket_name: str, secure: bool = False):
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        self.bucket_name = bucket_name
        self._ensure_bucket()

    def _ensure_bucket(self):
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created MinIO bucket: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"MinIO bucket check failed: {e}")
            raise

    def save(self, data: bytes, filename: str) -> str:
        # 使用 BytesIO 包装 data
        data_stream = io.BytesIO(data)
        length = len(data)
        
        try:
            self.client.put_object(
                self.bucket_name,
                filename,
                data_stream,
                length,
                content_type="audio/wav" # 假设我们主要存 wav
            )
            return filename
        except S3Error as e:
            logger.error(f"Failed to upload to MinIO: {e}")
            raise

    def get_url(self, file_path: str) -> str:
        # 返回预签名的 URL，或者直接返回 file_path 让前端通过 API 代理
        # 这里我们假设前端直接通过我们的后端 API 获取文件流，或者后端 API 重定向到 MinIO
        # 为了统一，我们暂时返回 file_path (object key)
        return file_path

    def get_stream(self, file_path: str):
        try:
            response = self.client.get_object(self.bucket_name, file_path)
            return response
        except S3Error as e:
            logger.error(f"Failed to get object from MinIO: {e}")
            return None
    
    def exists(self, file_path: str) -> bool:
        try:
            self.client.stat_object(self.bucket_name, file_path)
            return True
        except S3Error:
            return False

def get_storage_backend(config: dict) -> StorageBackend:
    """
    工厂函数，根据配置创建存储后端实例。
    """
    storage_type = config.get("type", "local")
    
    if storage_type == "minio":
        return MinioStorage(
            endpoint=config.get("minio", {}).get("endpoint", "localhost:9000"),
            access_key=config.get("minio", {}).get("access_key", "minioadmin"),
            secret_key=config.get("minio", {}).get("secret_key", "minioadmin"),
            bucket_name=config.get("minio", {}).get("bucket_name", "dream-talker"),
            secure=config.get("minio", {}).get("secure", False)
        )
    else:
        # 默认为本地存储
        base_dir = os.path.join(os.path.dirname(__file__), "data", "records")
        return LocalStorage(base_dir)
