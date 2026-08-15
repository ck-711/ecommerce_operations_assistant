from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import router
from backend.core.config import settings
from backend.db import Base, engine
from backend import models  # noqa: F401

app = FastAPI(title=settings.app_name, version='1.0.0')
app.add_middleware(CORSMiddleware, allow_origins=['http://127.0.0.1:8000','http://localhost:8000','http://127.0.0.1:3000','http://localhost:3000'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
app.include_router(router)

@app.on_event('startup')
def startup():
    # Development fallback only; production uses Alembic migrations.
    if settings.environment != 'production': Base.metadata.create_all(bind=engine)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('backend.main:app', host='0.0.0.0', port=8001, reload=settings.environment == 'development')
