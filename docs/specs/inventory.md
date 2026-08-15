# SKU & Inventory Module Spec

## Goal and scope

运营人员维护商品 SKU 和库存，所有调整可追溯，并在商品详情、店铺详情和工作台看到低库存 SKU。admin/operator 可写，viewer 只读。

## Entities

- `product_skus`: `product_id`, `sku_code`（商品内唯一）、`sku_name`, `price`, `status(active|inactive)`。
- `inventory_items`: `sku_id` 唯一、`stock_qty`, `locked_qty`, `warning_threshold`。
- `inventory_movements`: `sku_id`, `movement_type(adjustment)`, `change_qty`, `before_qty`, `after_qty`, `reason_text`, `created_at`。

## API

- `GET /api/v1/products/{product_id}` 返回 `skus`（含库存与 `low_stock`）和 `inventory_movements`。
- `POST /api/v1/products/{product_id}/skus` body `{sku_code,sku_name,price,warning_threshold,stock_qty}`。
- `PATCH /api/v1/products/{product_id}/skus/{sku_id}` body `{sku_name?,price?,status?,warning_threshold?}`。
- `POST /api/v1/products/{product_id}/skus/{sku_id}/inventory-adjustments` body `{change_qty,reason_text}`；返回前后库存与流水。

错误沿用 `{code,message,details}`；重复 SKU 返回 409，负库存和空原因返回 400，viewer 写操作返回 403。

## Acceptance criteria

- 新建 SKU 后库存为指定数量，并可查询低库存状态。
- 调整库存后 `before_qty + change_qty = after_qty`，流水记录完整。
- 调整后库存不得小于 0；缺少原因、非整数变更被拒绝。
- viewer 可读但不能新增 SKU 或调整库存。
