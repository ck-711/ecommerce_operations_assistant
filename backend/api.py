import hashlib
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.core.security import create_access_token, decode_access_token
from backend.db import get_db
from backend.models import User, Product, ProductSku, InventoryItem, GenerationJob, Store, ProductDiagnosis, CreativePlan, GeneratedAsset, PerformanceRecord, PromotionLink, AdExperiment, AdRecommendation, ReviewReport
from backend.schemas import LoginRequest, TokenResponse, UserOut, ProductCreate, ProductOut, SkuCreate, SkuOut, InventoryAdjustment, GenerationJobCreate, GenerationJobOut, StoreCreate, StoreOut, DiagnosisOut, CreativePlanCreate, CreativePlanOut, AssetReview, AssetOut, PerformanceCreate, PerformanceOut, PromotionLinkCreate, PromotionLinkOut, ExperimentCreate, ExperimentOut, AdRecommendationOut, ReviewReportOut, Confirmation
import uuid
from backend.worker import execute_generation_job

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

@router.get('/stores', response_model=list[StoreOut])
def stores(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return list(db.scalars(select(Store).order_by(Store.id.desc())))

@router.post('/stores', response_model=StoreOut, status_code=status.HTTP_201_CREATED)
def create_store(body: StoreCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role == 'viewer': raise HTTPException(status_code=403, detail={'code':'forbidden','message':'查看人员无写权限'})
    store=Store(**body.model_dump()); db.add(store); db.commit(); db.refresh(store); return store

@router.post('/products/{product_id}/diagnoses', response_model=DiagnosisOut, status_code=status.HTTP_201_CREATED)
def create_diagnosis(product_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role == 'viewer': raise HTTPException(status_code=403, detail={'code':'forbidden','message':'查看人员无写权限'})
    if not db.get(Product, product_id): raise HTTPException(status_code=404, detail={'code':'not_found','message':'商品不存在'})
    item=ProductDiagnosis(product_id=product_id,positioning='待模型分析',recommendations='待模型分析'); db.add(item); db.commit(); db.refresh(item); return item

@router.get('/products/{product_id}/diagnoses', response_model=list[DiagnosisOut])
def diagnoses(product_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)): return list(db.scalars(select(ProductDiagnosis).where(ProductDiagnosis.product_id==product_id).order_by(ProductDiagnosis.id.desc())))

@router.post('/products/{product_id}/creative-plans', response_model=CreativePlanOut, status_code=status.HTTP_201_CREATED)
def create_plan(product_id: int, body: CreativePlanCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role == 'viewer': raise HTTPException(status_code=403, detail={'code':'forbidden','message':'查看人员无写权限'})
    if not db.get(Product, product_id): raise HTTPException(status_code=404, detail={'code':'not_found','message':'商品不存在'})
    item=CreativePlan(product_id=product_id,**body.model_dump()); db.add(item); db.commit(); db.refresh(item); return item

@router.get('/products/{product_id}/assets', response_model=list[AssetOut])
def assets(product_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)): return list(db.scalars(select(GeneratedAsset).where(GeneratedAsset.product_id==product_id).order_by(GeneratedAsset.id.desc())))

@router.patch('/products/{product_id}/assets/{asset_id}', response_model=AssetOut)
def review_asset(product_id: int, asset_id: int, body: AssetReview, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role == 'viewer': raise HTTPException(status_code=403, detail={'code':'forbidden','message':'查看人员无写权限'})
    item=db.scalar(select(GeneratedAsset).where(GeneratedAsset.id==asset_id,GeneratedAsset.product_id==product_id))
    if not item: raise HTTPException(status_code=404, detail={'code':'not_found','message':'素材不存在'})
    item.review_status=body.review_status; item.score=body.score; db.commit(); db.refresh(item); return item

@router.post('/products/{product_id}/performance-records', response_model=PerformanceOut, status_code=status.HTTP_201_CREATED)
def performance(product_id: int, body: PerformanceCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role == 'viewer': raise HTTPException(status_code=403, detail={'code':'forbidden','message':'查看人员无写权限'})
    item=PerformanceRecord(product_id=product_id,**body.model_dump()); db.add(item); db.commit(); db.refresh(item); return item

@router.post('/products/{product_id}/promotion-links', response_model=PromotionLinkOut, status_code=status.HTTP_201_CREATED)
def promotion_link(product_id: int, body: PromotionLinkCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role == 'viewer': raise HTTPException(status_code=403, detail={'code':'forbidden','message':'查看人员无写权限'})
    item=PromotionLink(product_id=product_id,**body.model_dump(),tracking_code=uuid.uuid4().hex[:10]); db.add(item); db.commit(); db.refresh(item); return item

@router.post('/products/{product_id}/ad-experiments', response_model=ExperimentOut, status_code=status.HTTP_201_CREATED)
def experiment(product_id: int, body: ExperimentCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role == 'viewer': raise HTTPException(status_code=403, detail={'code':'forbidden','message':'查看人员无写权限'})
    item=AdExperiment(product_id=product_id,experiment_name=body.experiment_name); db.add(item); db.commit(); db.refresh(item); return item

@router.post('/products/{product_id}/ad-recommendations/generate', response_model=AdRecommendationOut, status_code=status.HTTP_201_CREATED)
def recommendation(product_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role == 'viewer': raise HTTPException(status_code=403, detail={'code':'forbidden','message':'查看人员无写权限'})
    item=AdRecommendation(product_id=product_id,summary_text='先小预算测试高意向人群，再根据转化扩量'); db.add(item); db.commit(); db.refresh(item); return item

@router.patch('/products/{product_id}/ad-recommendations/{recommendation_id}/confirmation', response_model=AdRecommendationOut)
def confirm_recommendation(product_id: int, recommendation_id: int, body: Confirmation, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role == 'viewer': raise HTTPException(status_code=403, detail={'code':'forbidden','message':'查看人员无写权限'})
    item=db.scalar(select(AdRecommendation).where(AdRecommendation.id==recommendation_id,AdRecommendation.product_id==product_id))
    if not item: raise HTTPException(status_code=404, detail={'code':'not_found','message':'投放建议不存在'})
    item.confirm_status=body.confirm_status; db.commit(); db.refresh(item); return item

@router.post('/products/{product_id}/review-reports/generate', response_model=ReviewReportOut, status_code=status.HTTP_201_CREATED)
def review_report(product_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role == 'viewer': raise HTTPException(status_code=403, detail={'code':'forbidden','message':'查看人员无写权限'})
    item=ReviewReport(product_id=product_id,summary_text='复盘报告已生成：请结合曝光、点击、转化和 ROI 调整下一轮素材测试。'); db.add(item); db.commit(); db.refresh(item); return item

@router.get('/products', response_model=list[ProductOut])
def products(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return list(db.scalars(select(Product).order_by(Product.id.desc())))

@router.post('/products', response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(body: ProductCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role == 'viewer': raise HTTPException(status_code=403, detail={'code':'forbidden','message':'查看人员无写权限'})
    product=Product(**body.model_dump()); db.add(product); db.commit(); db.refresh(product); return product

@router.get('/products/{product_id}/skus', response_model=list[SkuOut])
def skus(product_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return list(db.scalars(select(ProductSku).where(ProductSku.product_id==product_id).order_by(ProductSku.id)))

@router.post('/products/{product_id}/skus', response_model=SkuOut, status_code=status.HTTP_201_CREATED)
def create_sku(product_id: int, body: SkuCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role == 'viewer': raise HTTPException(status_code=403, detail={'code':'forbidden','message':'查看人员无写权限'})
    if not db.get(Product, product_id): raise HTTPException(status_code=404, detail={'code':'not_found','message':'商品不存在'})
    if db.scalar(select(ProductSku).where(ProductSku.product_id==product_id,ProductSku.sku_code==body.sku_code)): raise HTTPException(status_code=409, detail={'code':'conflict','message':'SKU 编码已存在'})
    sku=ProductSku(product_id=product_id,sku_code=body.sku_code,sku_name=body.sku_name,price=body.price); db.add(sku); db.flush(); db.add(InventoryItem(sku_id=sku.id,stock_qty=body.stock_qty,warning_threshold=body.warning_threshold)); db.commit(); db.refresh(sku); return sku

@router.post('/products/{product_id}/skus/{sku_id}/inventory-adjustments')
def adjust_inventory(product_id: int, sku_id: int, body: InventoryAdjustment, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role == 'viewer': raise HTTPException(status_code=403, detail={'code':'forbidden','message':'查看人员无写权限'})
    sku=db.scalar(select(ProductSku).where(ProductSku.id==sku_id,ProductSku.product_id==product_id)); item=db.scalar(select(InventoryItem).where(InventoryItem.sku_id==sku_id)) if sku else None
    if not sku or not item: raise HTTPException(status_code=404, detail={'code':'not_found','message':'SKU 不存在'})
    after=item.stock_qty+body.change_qty
    if after<0: raise HTTPException(status_code=400, detail={'code':'validation_error','message':'库存不能小于 0'})
    before=item.stock_qty; item.stock_qty=after; db.commit(); return {'sku_id':sku_id,'before_qty':before,'after_qty':after}

@router.post('/products/{product_id}/generation-jobs', response_model=GenerationJobOut, status_code=status.HTTP_202_ACCEPTED)
def create_generation_job(product_id: int, body: GenerationJobCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role == 'viewer': raise HTTPException(status_code=403, detail={'code':'forbidden','message':'查看人员无写权限'})
    if not db.get(Product, product_id): raise HTTPException(status_code=404, detail={'code':'not_found','message':'商品不存在'})
    job=GenerationJob(product_id=product_id,job_kind=body.job_kind,job_status='pending'); db.add(job); db.commit(); db.refresh(job)
    execute_generation_job.delay(job.id, product_id, body.job_kind)
    return job

@router.get('/products/{product_id}/generation-jobs', response_model=list[GenerationJobOut])
def generation_jobs(product_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return list(db.scalars(select(GenerationJob).where(GenerationJob.product_id==product_id).order_by(GenerationJob.id.desc())))
