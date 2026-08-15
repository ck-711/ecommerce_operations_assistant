# Full-stack Delivery

Compose 服务：

```text
frontend (Nginx :8080)
    ↓ /api proxy
api (FastAPI :8001)
    ├── mysql
    ├── redis
    └── worker (Celery + LangGraph)
```

前端容器直接复用 `web/` 静态资源，Nginx 将 `/api/*` 代理到 FastAPI，因此浏览器无需配置跨域 API 地址。SQLite `python app.py` 仍保留为离线演示模式。
