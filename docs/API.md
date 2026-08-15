# API 快速索引

统一前缀：`/api/v1`；除登录和静态资源外均需 `Authorization: Bearer <token>`。

| 领域 | 主要接口 |
| --- | --- |
| 认证 | `POST /auth/login`、`GET /auth/me` |
| 工作台 | `GET /workspace/dashboard`、`POST /workspace/demo-data` |
| 导入 | `POST /workspace/imports/{products|sku-inventory|performance-records}/{preview|commit}` |
| 店铺 | `GET/POST /stores`、`GET /stores/{id}`、`POST /stores/{id}/platform-accounts` |
| 商品 | `GET/POST /products`、`GET /products/{id}` |
| 库存 | `POST /products/{id}/skus`、`PATCH /products/{id}/skus/{sku_id}`、`POST .../inventory-adjustments` |
| 内容 | `POST .../diagnoses/generate`、`POST .../creative-plans/{type}/generate` |
| 任务/素材 | `POST .../generation-jobs/{id}/{retry|cancel}`、`PATCH .../assets/{id}` |
| 分析 | `POST .../performance-records`、`POST .../review-reports/generate` |
| 投放 | `POST .../promotion-links`、`POST .../ad-recommendations/generate`、`POST .../ad-experiments` |

错误格式统一为：`{"code":"...","message":"...","details":{}}`。
