# Frontend API Cutover

旧单页默认调用同源 `/api/v1`，生产 FastAPI 位于 8001 端口时可通过 `window.API_BASE` 切换。FastAPI 已允许本地 8000/3000 开发源跨域访问。

验收：登录、商品列表、商品详情和任务轮询均能使用 FastAPI API；旧 SQLite 演示入口不受影响。
