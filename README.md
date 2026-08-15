# 电商运营助手

面向中小电商团队的单品运营闭环 MVP：店铺/商品、SKU 库存、竞品、商品诊断、内容方案、异步生成任务、素材审核、CSV 导入、经营数据和复盘。

## 快速启动

```powershell
python app.py
```

打开 `http://127.0.0.1:8000/`。首次启动自动创建 SQLite 数据库和演示账号：

| 用户名 | 密码 | 角色 |
| --- | --- | --- |
| admin | admin123 | 管理员 |
| operator | operator123 | 运营人员 |
| viewer | viewer123 | 查看人员 |

登录后点击“初始化演示数据”，即可查看单品闭环。API 前缀为 `/api/v1`，完整阶段设计见 `docs/specs/`。

## 验证

```powershell
python -m unittest discover -s tests -v
python -m py_compile app.py
```

## 生产化骨架

生产服务骨架位于 `backend/`，依赖见 `requirements-prod.txt`。准备 Python 环境后可执行：

```powershell
pip install -r requirements-prod.txt
python -m backend.main
```

默认监听 `http://127.0.0.1:8001`，OpenAPI 地址为 `/docs`。MySQL/Redis 基础设施可用 `docker compose -f docker-compose.prod.yml up -d` 启动；通过 `.env` 设置 `DATABASE_URL`、`JWT_SECRET` 和 `REDIS_URL`。

Celery worker（安装生产依赖后）：

```powershell
celery -A backend.worker.celery_app worker --loglevel=INFO
```

Docker 方式：

```powershell
Copy-Item .env.example .env
docker compose -f docker-compose.prod.yml up --build
```

前端切换到生产 API：在浏览器控制台执行 `localStorage.setItem('API_BASE','http://127.0.0.1:8001/api/v1'); location.reload()`；恢复同源演示可执行 `localStorage.removeItem('API_BASE'); location.reload()`。

## 生产替换边界

当前使用 Python 标准库、SQLite、内存 token 和确定性演示 worker。生产环境应替换为 JWT、PostgreSQL、Redis/Celery、对象存储和真实 AI/平台适配器；系统不会保存明文平台 token/cookie，也不会自动执行投放或扣费。
