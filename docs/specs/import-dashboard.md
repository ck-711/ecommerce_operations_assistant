# Import Center & Dashboard Spec

## Scope

提供商品、SKU/库存、经营数据三类 CSV 的模板说明、预览、错误行反馈和部分成功导入；工作台展示店铺数、商品数、低库存 SKU 数和待审核素材数。

## API

- `GET /api/v1/workspace/dashboard`：返回 `{stores,products,low_stock_skus,pending_assets}`。
- `POST /api/v1/workspace/imports/{kind}/preview`：body `{csv_text}`，kind 为 `products|sku-inventory|performance-records`，返回 `valid_rows/errors`。
- `POST /api/v1/workspace/imports/{kind}/commit`：同 body，导入有效行并返回 `{success_count,error_count,errors}`。

导入永远不覆盖已有记录；重复 SKU、缺失关联商品、数值错误作为错误行返回，其余行继续导入。

## Acceptance

- CSV 预览在不写库的情况下返回行号和错误原因。
- commit 能部分成功，成功/失败数量准确。
- dashboard 能反映低库存和待审核素材数量。
