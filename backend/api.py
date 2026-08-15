import hashlib
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.core.security import create_access_token, decode_access_token
from backend.db import get_db
from backend.models import User
from backend.schemas import LoginRequest, TokenResponse, UserOut

router = APIRouter(prefix='/api/v1')
bearer = HTTPBearer(auto_error=False)

def password_hash(value: str) -> str: return hashlib.sha256(value.encode()).hexdigest()

def current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)) -> User:
    if not credentials: raise HTTPException(status_code=401, detail={'code':'unauthorized','message':'请先登录'})
    try: payload = decode_access_token(credentials.credentials); user_id = int(payload['sub'])
    except Exception as exc: raise HTTPException(status_code=401, detail={'code':'unauthorized','message':'令牌无效'}) from exc
    user = db.get(User, user_id)
    if not user or user.status != 'active': raise HTTPException(status_code=401, detail={'code':'unauthorized','message':'用户不可用'})
    return user

@router.get('/health')
def health(): return {'status':'ok'}

@router.post('/auth/login', response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == body.username, User.status == 'active'))
    if not user or user.password_hash != password_hash(body.password): raise HTTPException(status_code=401, detail={'code':'invalid_credentials','message':'用户名或密码错误'})
    return {'access_token':create_access_token(user.id,user.username,user.role),'user':user}

@router.get('/auth/me', response_model=UserOut)
def me(user: User = Depends(current_user)): return user

@router.get('/users', response_model=list[UserOut])
def users(user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role != 'admin': raise HTTPException(status_code=403, detail={'code':'forbidden','message':'仅管理员可查看用户'})
    return list(db.scalars(select(User).order_by(User.id)))
