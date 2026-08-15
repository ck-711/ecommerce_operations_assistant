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
