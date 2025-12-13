import os
import abc
import io
import logging
from datetime import datetime
import urllib3
import threading
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
    包含本地存储作为灾备方案。
    """
    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket_name: str, secure: bool = False):
        # 配置短超时 HTTP 客户端，确保容灾判断迅速
        # connect: 1s, read: 2s
        self.http_client = urllib3.PoolManager(
            timeout=urllib3.Timeout(connect=1.0, read=2.0),
            retries=urllib3.Retry(
                total=1,  # 库内部只重试1次，我们自己在业务逻辑层控制重试
                backoff_factor=0.2,
                status_forcelist=[500, 502, 503, 504]
            )
        )
        
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
            http_client=self.http_client
        )
        self.bucket_name = bucket_name
        
        # 初始化本地存储作为 fallback
        # 使用默认的数据目录 server/data/records
        base_dir = os.path.join(os.path.dirname(__file__), "data", "records")
        self.local_backup = LocalStorage(base_dir)

        # 同步任务控制
        self._sync_lock = threading.Lock()
        self._sync_active = False
        
        # MinIO 状态标记：如果检测到宕机，后续重试次数减少
        self._minio_down = False

        # 尝试检查 bucket，如果失败不应阻断启动，而是记录日志并依赖运行时 fallback
        try:
            self._ensure_bucket()
        except Exception as e:
            logger.warning(f"MinIO initialization check failed (will fallback to local storage): {e}")

    def _ensure_bucket(self):
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created MinIO bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"MinIO bucket check failed: {e}")
            raise

    def _sync_worker(self):
        """后台同步线程：将本地 fallback 的文件同步到 MinIO"""
        with self._sync_lock:
            if self._sync_active:
                return
            self._sync_active = True

        try:
            logger.info("Starting background sync to MinIO...")
            # 遍历本地备份目录
            for root, _, files in os.walk(self.local_backup.base_dir):
                for file in files:
                    if not file.endswith(".wav"):
                        continue
                        
                    full_path = os.path.join(root, file)
                    # 计算相对路径作为 object key
                    rel_path = os.path.relpath(full_path, self.local_backup.base_dir)
                    
                    try:
                        # 检查 MinIO 是否已存在（可选，但为了避免重复上传，可以先 stat）
                        # 但考虑到这里是 disaster recovery 恢复，直接 overwrite 也可以
                        # 或者只在 MinIO 上传成功后删除本地
                        
                        # 尝试上传
                        with open(full_path, "rb") as f:
                            data = f.read()
                            length = len(data)
                            data_stream = io.BytesIO(data)
                            
                            self.client.put_object(
                                self.bucket_name,
                                rel_path,
                                data_stream,
                                length,
                                content_type="audio/wav"
                            )
                        
                        logger.info(f"Synced file to MinIO: {rel_path}")
                        
                        # 如果之前标记为宕机，现在同步成功说明恢复了
                        if self._minio_down:
                            logger.info("MinIO recovered during background sync.")
                            self._minio_down = False

                        # 上传成功，删除本地文件
                        os.remove(full_path)
                        # 尝试删除空目录
                        try:
                            os.rmdir(os.path.dirname(full_path))
                        except OSError:
                            pass # 目录非空，忽略
                            
                    except Exception as e:
                        logger.warning(f"Failed to sync file {rel_path}: {e}")
                        # 如果出现连接错误，可能 MinIO 还是挂的，终止本次同步
                        # 简单的策略：遇到错误就退出，等待下次触发
                        if "Max retries exceeded" in str(e) or "Connection refused" in str(e):
                             logger.warning("MinIO connection issues detected, aborting sync.")
                             self._minio_down = True
                             return
        except Exception as e:
            logger.error(f"Error in sync worker: {e}")
        finally:
            with self._sync_lock:
                self._sync_active = False
            logger.info("Background sync finished.")

    def _trigger_sync(self):
        """触发后台同步任务"""
        if self._sync_active:
            return
        threading.Thread(target=self._sync_worker, daemon=True).start()

    def save(self, data: bytes, filename: str) -> str:
        """
        保存文件，具有重试和本地回退机制。
        一旦 MinIO 超过 3 次没有存储成功，则将文件存储至本地存储。
        每次保存时，都会尝试触发同步任务。
        """
        # 使用 BytesIO 包装 data
        length = len(data)
        saved_filename = filename
        upload_success = False
        
        # 如果标记为宕机，只重试 1 次；否则重试 3 次
        max_retries = 1 if self._minio_down else 3
        
        # 尝试上传到 MinIO
        for attempt in range(max_retries):
            try:
                data_stream = io.BytesIO(data) # 每次重试创建一个新的流
                self.client.put_object(
                    self.bucket_name,
                    filename,
                    data_stream,
                    length,
                    content_type="audio/wav"
                )
                logger.info(f"Successfully saved to MinIO: {filename}")
                upload_success = True
                
                # 如果成功且之前标记为 down，则恢复状态
                if self._minio_down:
                    self._minio_down = False
                    logger.info("MinIO recovered during save operation.")
                    
                break
            except Exception as e:
                logger.warning(f"MinIO upload attempt {attempt + 1}/{max_retries} failed: {e}")
        
        if not upload_success:
            # 标记 MinIO 为宕机状态
            if not self._minio_down:
                self._minio_down = True
                logger.error(f"MinIO unavailable after {max_retries} attempts. Fallback to LocalStorage for: {filename}")
            else:
                logger.warning(f"MinIO still unavailable. Fallback to LocalStorage for: {filename}")

            try:
                saved_filename = self.local_backup.save(data, filename)
            except Exception as local_e:
                logger.critical(f"Both MinIO and LocalStorage failed for {filename}: {local_e}")
                raise

        # 无论本次保存是在 MinIO 还是本地，都尝试触发一次同步任务
        # 如果 MinIO 刚才失败了，worker 会很快再次失败并退出，不会造成太大负担
        # 如果 MinIO 恢复了，这会把之前的 backlog 传上去
        self._trigger_sync()

        return saved_filename

    def get_url(self, file_path: str) -> str:
        # 返回文件路径
        return file_path

    def get_stream(self, file_path: str):
        """
        获取文件流，优先 MinIO，失败则尝试本地。
        """
        # 尝试 MinIO
        try:
            response = self.client.get_object(self.bucket_name, file_path)
            return response
        except Exception as e:
            logger.warning(f"Failed to get object from MinIO ({e}), trying LocalStorage: {file_path}")
            
            # 回退尝试本地存储
            if self.local_backup.exists(file_path):
                return self.local_backup.get_stream(file_path)
            
            logger.error(f"File not found in both MinIO and LocalStorage: {file_path}")
            return None
    
    def exists(self, file_path: str) -> bool:
        try:
            self.client.stat_object(self.bucket_name, file_path)
            return True
        except Exception:
            # 检查本地备份
            return self.local_backup.exists(file_path)

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
