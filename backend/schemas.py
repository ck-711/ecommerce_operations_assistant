from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=128)

class UserOut(BaseModel):
    id: int
    username: str
    display_name: str
    role: str
    status: str
    model_config = {'from_attributes': True}

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    user: UserOut

class ProductCreate(BaseModel):
    store_id: int
    name: str = Field(min_length=1, max_length=200)
    platform: str = 'other'
    category: str = ''
    price: float = Field(default=0, ge=0)
    cost: float = Field(default=0, ge=0)

class StoreCreate(BaseModel):
    store_name: str = Field(min_length=1, max_length=160)
    platform: str = 'other'
    owner_name: str = ''
    remark: str = ''

class StoreOut(StoreCreate):
    id: int
    model_config = {'from_attributes': True}

class DiagnosisOut(BaseModel):
    id: int
    product_id: int
    positioning: str
    recommendations: str
    model_config = {'from_attributes': True}

class CreativePlanCreate(BaseModel):
    plan_type: str = Field(pattern='^(main-images|video-scripts)$')
    title: str = Field(min_length=1, max_length=200)
    content_json: str = '[]'

class CreativePlanOut(CreativePlanCreate):
    id: int
    product_id: int
    status: str
    model_config = {'from_attributes': True}

class AssetReview(BaseModel):
    review_status: str = Field(pattern='^(pending|approved|rejected)$')
    score: float | None = Field(default=None, ge=0, le=5)

class AssetOut(BaseModel):
    id: int
    product_id: int
    asset_type: str
    asset_url: str
    review_status: str
    score: float | None
    model_config = {'from_attributes': True}

class ProductOut(ProductCreate):
    id: int
    status: str
    model_config = {'from_attributes': True}

class SkuCreate(BaseModel):
    sku_code: str = Field(min_length=1, max_length=100)
    sku_name: str = Field(min_length=1, max_length=200)
    price: float = Field(default=0, ge=0)
    stock_qty: int = Field(default=0, ge=0)
    warning_threshold: int = Field(default=10, ge=0)

class SkuOut(SkuCreate):
    id: int
    product_id: int
    status: str
    model_config = {'from_attributes': True}

class InventoryAdjustment(BaseModel):
    change_qty: int
    reason_text: str = Field(min_length=1, max_length=300)

class GenerationJobCreate(BaseModel):
    job_kind: str = Field(pattern='^(image|video)$')

class GenerationJobOut(BaseModel):
    id: int
    product_id: int
    job_kind: str
    job_status: str
    attempts: int
    model_config = {'from_attributes': True}
