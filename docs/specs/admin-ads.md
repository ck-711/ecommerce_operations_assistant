# Admin, Platform Placeholder & Ads Spec

## Scope

补齐管理端最低闭环：管理员查看用户、店铺平台账号安全占位、投放建议人工确认、投放实验状态更新。系统不保存明文 token/cookie，不直接执行广告。

## API

- `GET /api/v1/users`：仅 admin，返回用户安全字段。
- `POST /api/v1/stores/{store_id}/platform-accounts`：创建账号占位。
- `POST /api/v1/products/{product_id}/ad-recommendations/{id}/confirmation`：body `{confirm_status,confirm_remark}`，状态 confirmed/rejected。
- `POST /api/v1/products/{product_id}/ad-experiments`：创建 draft 实验。
- `PATCH /api/v1/products/{product_id}/ad-experiments/{id}`：更新状态 draft/confirmed/running/finished/cancelled。

## Rules

admin 才能看用户；admin/operator 才能确认建议和更新实验；只有 confirmed 才能进入 running；终态 finished/cancelled 不可回退。平台授权接口只生成占位元数据。
