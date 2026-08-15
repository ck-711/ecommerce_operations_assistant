# Production Migration Spec

## Goal

在不影响 `python app.py` 演示入口的前提下，新增 FastAPI + MySQL + JWT 的生产服务骨架；Redis/Celery 作为下一切片接入。

## Current slice

- `backend/`：配置、SQLAlchemy session、用户模型、JWT、登录/me/users/health API。
- `docker-compose.prod.yml`：MySQL 8.4 和 Redis 7 基础设施。
- `requirements-prod.txt`：生产依赖清单。
- development 环境自动建表；production 必须使用 Alembic migration。

## Acceptance

- `DATABASE_URL=mysql+pymysql://...` 时服务使用 MySQL。
- JWT 过期或签名错误返回 401；非管理员访问 `/users` 返回 403。
- SQLite 演示入口继续可用；生产入口为 `python -m backend.main`。

## Next slice

已增加 Alembic 初始迁移、Celery app/任务基类、Redis health check、Docker API 服务和商品/库存路由迁移。下一步是接入真实 AI Provider、完善全量业务表迁移和 CI/CD。
