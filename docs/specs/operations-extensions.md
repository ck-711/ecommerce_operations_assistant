# Operations Extensions Spec

## Scope

补齐店铺详情、竞品录入、推广链接建议和投放建议演示能力。真实平台授权、广告执行和扣费仍不在范围内。

## API

- `GET /api/v1/stores/{store_id}`：店铺、商品、SKU 数量、低库存 SKU 和最近流水。
- `POST /api/v1/products/{product_id}/competitors`：录入竞品名称、平台、链接、价格和卖点。
- `POST /api/v1/products/{product_id}/promotion-links/generate`：生成建议追踪参数，不创建外部投放。
- `POST /api/v1/products/{product_id}/promotion-links`：创建内部追踪链接。
- `POST /api/v1/products/{product_id}/ad-recommendations/generate`：生成可编辑的投放建议，状态 pending。

所有写操作需要 admin/operator；viewer 只读。链接点击和真实广告执行留待后续适配。
