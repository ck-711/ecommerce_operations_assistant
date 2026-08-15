from fastapi import FastAPI
from backend.api import router
from backend.core.config import settings
from backend.db import Base, engine
from backend import models  # noqa: F401

app = FastAPI(title=settings.app_name, version='1.0.0')
app.include_router(router)

@app.on_event('startup')
def startup():
    # Development fallback only; production uses Alembic migrations.
    if settings.environment != 'production': Base.metadata.create_all(bind=engine)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('backend.main:app', host='0.0.0.0', port=8001, reload=settings.environment == 'development')
