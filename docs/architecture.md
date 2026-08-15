# 概要设计

## 技术方向

- Python 标准库 `http.server` + SQLite，避免 MVP 安装依赖；生产部署时可替换为 FastAPI/SQLAlchemy。
- `app.py` 暂时包含 API、仓储和演示任务 worker；领域状态通过 SQLite 约束和服务层校验。
- `web/` 为静态单页，使用原生 HTML/CSS/JS 调用 `/api/v1`。

## 边界

浏览器 → HTTP API → Service/Repository → SQLite；AI 和素材供应商通过 `DemoAIProvider`/`DemoAssetProvider` 接口隔离。任务 worker 轮询 `generation_jobs`，将 `pending` 推进到 `running`、`succeeded`。

## 安全

密码仅存 SHA-256 hash；token 为内存短 token（重启失效，仅适合演示）。平台账号只存授权状态和元数据，不接受明文 token/cookie。

## 后续替换点

生产版应换 JWT、PostgreSQL、Celery/Redis、对象存储和真实模型适配器，并保留当前 API 契约。
