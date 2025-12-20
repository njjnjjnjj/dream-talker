from contextlib import asynccontextmanager
import logging
from pydantic import BaseModel
import uvicorn
import yaml
import os
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request, Depends
from fastapi.responses import JSONResponse
from datetime import date, timedelta, datetime
from typing import List, Dict, Optional

from log import init_log
from vad.engine import VadEngine
from stt import get_stt_engine, STTEngine
from database import init_db, add_record
from schemas import MonthlyActivity, SleepRecordCreate, SleepRecord, StatisticsResponse
from records import get_records_by_date, get_audio_file_by_id, get_monthly_record_activity, update_record_favorite_status, get_statistics
from storage import get_storage_backend, StorageBackend
from auth import (
    get_user_credentials,
    save_credential,
    update_credential_sign_count,
    RP_ID,
    RP_NAME,
    ORIGIN,
    FIXED_USER_ID,
)
from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
)
from webauthn.helpers import options_to_json_dict
from webauthn.helpers.structs import AuthenticatorSelectionCriteria, ResidentKeyRequirement, UserVerificationRequirement

init_log()
logger = logging.getLogger(__name__)

# 临时存储挑战码
challenge_storage: Dict[str, bytes] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI 的生命周期事件，在应用启动时执行。"""
    init_db()
    await startup_event()
    yield


app = FastAPI(lifespan=lifespan)

# 全局 VAD, STT 和 Storage 实例
vad_engine: VadEngine = None
stt_engine: STTEngine = None
storage_backend: StorageBackend = None


ACCESS_CODE = None

# 简单的内存速率限制存储
# 格式: {ip_address: {"count": int, "blocked_until": datetime}}
login_attempts = {}
MAX_LOGIN_ATTEMPTS = 5
BLOCK_DURATION_MINUTES = 10

async def startup_event():
    """在应用启动时加载配置和模型。"""
    global vad_engine, stt_engine, storage_backend, ACCESS_CODE
    config_path = os.path.join(os.path.dirname(__file__), '.config.yaml')
    config = {}
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    
    # 加载安全配置
    security_config = config.get('security', {})
    ACCESS_CODE = security_config.get('access_code')
    if not ACCESS_CODE:
        logger.warning("安全警告: 访问码未在 .config.yaml 中设置。认证将不会启用。")
    elif ACCESS_CODE == "changeme-please":
        logger.warning("安全警告: 您正在使用默认的访问码 'changeme-please'。请立即在 .config.yaml 中修改为一个强密码。")

    # 初始化存储后端
    storage_config = config.get('storage', {})
    storage_backend = get_storage_backend(storage_config)
    logger.info(f"存储后端已初始化: {storage_config.get('type', 'local')}")

    # 初始化 VAD 引擎
    vad_config = config.get('vad', {})
    vad_engine = VadEngine(vad_config=vad_config)

    # 初始化 STT 引擎
    stt_config = config.get('stt', {})
    stt_engine = get_stt_engine(stt_config)


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """中间件，用于保护 API 路由。"""
    path = request.url.path
    # 豁免登录和 webauthn 相关的端点
    exempt_paths = ["/api/login", "/api/webauthn"]
    if ACCESS_CODE and path.startswith("/api/") and not any(path.startswith(p) for p in exempt_paths):
        auth_header = request.headers.get("Authorization")
        if auth_header is None:
            return JSONResponse(status_code=401, content={"detail": "未提供认证信息"})
        
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer" or token != ACCESS_CODE:
                raise ValueError("无效的 Token 或 Scheme")
        except ValueError as e:
            return JSONResponse(status_code=401, content={"detail": str(e)})

    response = await call_next(request)
    return response


class LoginRequest(BaseModel):
    access_code: str

@app.post("/api/login")
async def login(request: LoginRequest, raw_request: Request):
    """验证访问码。"""
    # 强制要求 ACCESS_CODE 必须被设置
    if not ACCESS_CODE:
        logger.error("安全风险：尝试登录，但服务器未配置 access_code。")
        raise HTTPException(status_code=500, detail="服务器认证未正确配置")

    client_ip = raw_request.client.host
    now = datetime.now()

    # 检查 IP 是否被封禁
    if client_ip in login_attempts:
        record = login_attempts[client_ip]
        if record.get("blocked_until") and record["blocked_until"] > now:
            remaining = (record["blocked_until"] - now).seconds // 60 + 1
            logger.warning(f"IP {client_ip} 尝试登录，但已被封禁。剩余时间: {remaining} 分钟")
            raise HTTPException(status_code=429, detail=f"尝试次数过多，请 {remaining} 分钟后再试")

    if request.access_code == ACCESS_CODE:
        # 登录成功，清除该 IP 的失败记录
        if client_ip in login_attempts:
            del login_attempts[client_ip]
        return {"status": "success", "message": "登录成功"}
    else:
        # 登录失败，记录尝试次数
        if client_ip not in login_attempts:
            login_attempts[client_ip] = {"count": 0, "blocked_until": None}
        
        record = login_attempts[client_ip]
        record["count"] += 1
        
        if record["count"] >= MAX_LOGIN_ATTEMPTS:
            record["blocked_until"] = now + timedelta(minutes=BLOCK_DURATION_MINUTES)
            logger.warning(f"IP {client_ip} 因连续 {MAX_LOGIN_ATTEMPTS} 次登录失败被封禁 {BLOCK_DURATION_MINUTES} 分钟。")
            raise HTTPException(status_code=429, detail="尝试次数过多，请稍后再试")
            
        raise HTTPException(status_code=401, detail="无效的访问码")


@app.get("/api/webauthn/register/options")
async def webauthn_register_options():
    """生成 WebAuthn 注册选项"""
    options = generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,
        user_id=FIXED_USER_ID.encode('utf-8'),
        user_name=FIXED_USER_ID,
        exclude_credentials=get_user_credentials(FIXED_USER_ID),
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.REQUIRED,
            user_verification=UserVerificationRequirement.REQUIRED
        )
    )
    challenge_storage[FIXED_USER_ID] = options.challenge
    return JSONResponse(content=options_to_json_dict(options))

class RegistrationVerificationRequest(BaseModel):
    response: dict

@app.post("/api/webauthn/register/verify")
async def webauthn_register_verify(request: RegistrationVerificationRequest, raw_request: Request):
    """验证 WebAuthn 注册响应"""
    try:
        challenge = challenge_storage.pop(FIXED_USER_ID, None)
        if not challenge:
            raise HTTPException(status_code=400, detail="Challenge not found")
            
        verification = verify_registration_response(
            credential=request.response,
            expected_challenge=challenge,
            expected_origin=ORIGIN,
            expected_rp_id=RP_ID,
            require_user_verification=True
        )
        
        save_credential(FIXED_USER_ID, verification)
        return {"status": "success", "message": "设备绑定成功"}
    except Exception as e:
        logger.error(f"WebAuthn registration verification failed: {e}")
        raise HTTPException(status_code=400, detail="设备绑定失败")

@app.get("/api/webauthn/login/options")
async def webauthn_login_options():
    """生成 WebAuthn 登录选项"""
    options = generate_authentication_options(
        rp_id=RP_ID,
        allow_credentials=get_user_credentials(FIXED_USER_ID)
    )
    challenge_storage[FIXED_USER_ID] = options.challenge
    return JSONResponse(content=options_to_json_dict(options))

class AuthenticationVerificationRequest(BaseModel):
    response: dict

@app.post("/api/webauthn/login/verify")
async def webauthn_login_verify(request: AuthenticationVerificationRequest, raw_request: Request):
    """验证 WebAuthn 登录响应"""
    try:
        challenge = challenge_storage.pop(FIXED_USER_ID, None)
        if not challenge:
            raise HTTPException(status_code=400, detail="Challenge not found")

        verification = verify_authentication_response(
            credential=request.response,
            expected_challenge=challenge,
            expected_origin=ORIGIN,
            expected_rp_id=RP_ID,
            require_user_verification=True,
            credentials=get_user_credentials(FIXED_USER_ID)
        )
        
        update_credential_sign_count(verification.credential_id, verification.new_sign_count)
        return {"status": "success", "message": "登录成功"}
    except Exception as e:
        logger.error(f"WebAuthn authentication verification failed: {e}")
        raise HTTPException(status_code=401, detail="无效的凭证")

@app.websocket("/vad")
async def websocket_binary(websocket: WebSocket):
    """处理 WebSocket 二进制音频流的端点。"""
    await websocket.accept()
    logger.info("WebSocket 连接已接受。")

    async def on_speech_end(record_data: SleepRecordCreate):
        """当检测到语音片段结束时的回调函数，将数据保存到数据库。"""
        logger.info(f"接收到新的语音记录: {record_data}")
        add_record(record_data)

    # 为当前 WebSocket 连接创建一个 VadWrapper 实例
    vad_wrapper = vad_engine.get_vad_wrapper(on_speech_end, stt_engine, storage_backend)

    try:
        # 持续接收来自客户端的音频数据
        while True:
            data: bytes = await websocket.receive_bytes()
            # 将音频数据喂给 VAD 处理器
            await vad_wrapper.process(data)
    except WebSocketDisconnect:
        # 当客户端断开连接时，重置 VAD 状态
        vad_wrapper.reset()
        logger.info("WebSocket 连接已断开。")
    except Exception:
        # 发生其他异常时，同样重置 VAD 状态
        vad_wrapper.reset()
        logger.error("WebSocket 发生错误", exc_info=True)


@app.get("/api/records", response_model=List[SleepRecord])
async def read_records_by_date(date: date):
    """
    获取指定日期的梦话记录。
    """
    return get_records_by_date(date)


@app.get("/api/records/activity", response_model=MonthlyActivity)
async def read_record_activity(year: int, month: int):
    """
    获取指定月份每日的梦话记录数量。
    """
    return get_monthly_record_activity(year, month)


@app.get("/api/statistics", response_model=StatisticsResponse)
async def read_statistics(start_date: Optional[date] = None, end_date: Optional[date] = None, days: Optional[int] = None):
    """
    获取统计数据。
    """
    if days is not None and start_date is None and end_date is None:
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        
    return get_statistics(start_date, end_date)


class UpdateFavoriteRequest(BaseModel):
    is_favorite: bool

@app.put("/api/records/{record_id}/favorite")
async def update_favorite_status(record_id: str, request: UpdateFavoriteRequest):
    """
    更新记录的收藏状态。
    """
    success = update_record_favorite_status(record_id, request.is_favorite)
    if not success:
        raise HTTPException(status_code=404, detail="Record not found or update failed")
    return {"status": "success", "message": "Favorite status updated"}


@app.get("/api/audio/{record_id}")
async def stream_audio_file(record_id: str, request: Request):
    """
    以文件流形式提供音频文件。
    """
    return get_audio_file_by_id(record_id, storage_backend, request)


if __name__ == "__main__":
    # FIXME: reload 会监听 logs 文件
    uvicorn.run(
        "app:app", host="0.0.0.0", port=8569, reload=True, reload_excludes=["logs"]
    )
