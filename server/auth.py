import logging
from datetime import datetime
import uuid
import json

from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
)
from webauthn.helpers.structs import (
    RegistrationCredential,
    AuthenticationCredential,
    AuthenticatorSelectionCriteria,
    ResidentKeyRequirement,
)
from database import get_db_connection

logger = logging.getLogger(__name__)

# 在单用户模式下，我们可以使用一个固定的 user_id
# 在多用户系统中，这里应该是实际的用户 ID
FIXED_USER_ID = "default-user"
RP_ID = "localhost"  # 依赖于实际部署的域名
RP_NAME = "DreamTalker"
ORIGIN = "http://localhost:5173" # 依赖于前端服务的地址

def get_user_credentials(user_id: str) -> list[RegistrationCredential]:
    """从数据库获取用户的凭证"""
    credentials = []
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, public_key, sign_count, transports FROM webauthn_credentials WHERE user_id = ?",
                (user_id,),
            )
            for row in cursor.fetchall():
                transports_list = json.loads(row["transports"]) if row["transports"] else []
                credentials.append(
                    RegistrationCredential(
                        id=row["id"],
                        public_key=row["public_key"],
                        sign_count=row["sign_count"],
                        transports=transports_list
                    )
                )
    except Exception as e:
        logger.error(f"Failed to get credentials for user {user_id}: {e}")
    return credentials

def save_credential(user_id: str, cred: RegistrationCredential) -> None:
    """将新凭证保存到数据库"""
    now = datetime.utcnow().isoformat()
    transports_json = json.dumps(cred.transports) if cred.transports else None
    
    try:
        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO webauthn_credentials
                (id, user_id, public_key, sign_count, transports, created_at, last_used_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cred.id,
                    user_id,
                    cred.public_key,
                    cred.sign_count,
                    transports_json,
                    now,
                    now
                ),
            )
            conn.commit()
        logger.info(f"Successfully saved credential {cred.id} for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to save credential for user {user_id}: {e}")
        raise

def update_credential_sign_count(cred_id: str, new_sign_count: int) -> None:
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
