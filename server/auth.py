import logging
import os
from datetime import datetime
import json
from typing import Optional, List, Dict

from webauthn.helpers.structs import (
    RegistrationCredential,
    PublicKeyCredentialDescriptor,
    AuthenticatorTransport,
)
from database import get_db_connection

logger = logging.getLogger(__name__)

# 在单用户模式下，我们可以使用一个固定的 user_id
# 在多用户系统中，这里应该是实际的用户 ID
FIXED_USER_ID = "dreamtalker"
RP_ID = "localhost"
RP_NAME = "DreamTalker"
ORIGIN = "http://localhost:5173"

def init_auth_config(security_config: Dict):
    """初始化认证配置"""
    global RP_ID, ORIGIN
    # 优先从配置中读取，如果没有则回退到环境变量，最后是默认值
    RP_ID = security_config.get("rp_id", os.getenv("RP_ID", "localhost"))
    ORIGIN = security_config.get("origin", os.getenv("ORIGIN", "http://localhost:5173"))
    logger.info(f"Auth config initialized: RP_ID='{RP_ID}', ORIGIN='{ORIGIN}'")

def get_user_credentials(user_id: str) -> List[PublicKeyCredentialDescriptor]:
    """从数据库获取用户的凭证列表，用于 exclude/allow credentials"""
    descriptors = []
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, transports FROM webauthn_credentials WHERE user_id = ?",
                (user_id,),
            )
            for row in cursor.fetchall():
                transports_list = json.loads(row["transports"]) if row["transports"] else []
                # 转换 transports 字符串列表为 Enum 列表
                transports_enum = [AuthenticatorTransport(t) for t in transports_list] if transports_list else None
                
                descriptors.append(
                    PublicKeyCredentialDescriptor(
                        id=row["id"],
                        transports=transports_enum
                    )
                )
    except Exception as e:
        logger.error(f"Failed to get credentials for user {user_id}: {e}")
    return descriptors

def get_credential_by_id(credential_id: bytes) -> Optional[dict]:
    """根据 ID 获取单个凭证的详细信息（公钥、签名计数等）"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT public_key, sign_count FROM webauthn_credentials WHERE id = ?",
                (credential_id,),
            )
            row = cursor.fetchone()
            if row:
                return {
                    "public_key": row["public_key"],
                    "sign_count": row["sign_count"]
                }
    except Exception as e:
        logger.error(f"Failed to get credential by id: {e}")
    return None

def save_credential(user_id: str, verification: RegistrationCredential) -> None:
    """将新凭证保存到数据库"""
    now = datetime.utcnow().isoformat()
    # The `transports` attribute is not available on the verification object.
    # We will save it as None.
    transports_json = None
    
    try:
        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO webauthn_credentials
                (id, user_id, public_key, sign_count, transports, created_at, last_used_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    verification.credential_id,
                    user_id,
                    verification.credential_public_key,
                    verification.sign_count, 
                    transports_json,
                    now,
                    now
                ),
            )
            conn.commit()
        logger.info(f"Successfully saved credential {verification.credential_id} for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to save credential for user {user_id}: {e}")
        raise

def update_credential_sign_count(cred_id: bytes, new_sign_count: int) -> None:
    """更新凭证的签名计数"""
    now = datetime.utcnow().isoformat()
    try:
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE webauthn_credentials SET sign_count = ?, last_used_at = ? WHERE id = ?",
                (new_sign_count, now, cred_id),
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Failed to update sign count for credential {cred_id}: {e}")
