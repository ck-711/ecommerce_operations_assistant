# Task Center & Asset Review Module Spec

## 1. Module goal and scope

- Goal: 让运营人员能观察生成任务全过程，并对成功素材完成审核、评分和备注。
- Actors: admin/operator 可查看任务、重试、取消、审核素材；viewer 只读。
- In scope: 任务列表、状态与事件时间线、轮询、失败重试、运行中取消、生成素材落库、审核字段更新。
- Out of scope: 真实图片/视频供应商、对象存储、发布到平台。

## 2. User flows and surfaces

| Surface | Role | Actions | States |
| --- | --- | --- | --- |
| 商品详情-任务 | all/write | 查看、刷新、重试、取消 | pending/running/succeeded/failed/cancelled/timeout |
| 商品详情-素材库 | all/write | 查看素材、审核、评分、标签、备注 | pending/approved/rejected |

## 3. Data entities

`generated_assets`: `id`, `product_id`, `creative_plan_id`, `job_id`, `asset_type`, `asset_url`, `review_status`, `version_no`, `usage_scene`, `score`, `tags_json`, `remark`, `created_at`, `updated_at`。审核状态为 `pending|approved|rejected`；一个成功 job 至多创建一个 demo asset。

## 4. API contract

- `GET /api/v1/products/{product_id}`：详情中的 `jobs` 包含 `events`，并返回 `assets`。
- `POST /api/v1/products/{product_id}/generation-jobs/{job_id}/retry`：仅 failed/timeout，返回 pending job。
- `POST /api/v1/products/{product_id}/generation-jobs/{job_id}/cancel`：仅 pending/running，返回 cancelled job。
- `PATCH /api/v1/products/{product_id}/assets/{asset_id}`：body `{review_status?,score?,tags?,remark?,usage_scene?}`；返回更新后的素材。

错误统一为 `{code,message,details}`，viewer 写操作 403，跨商品资源 404。

## 5. Business rules and failure handling

1. worker 先写 running 事件，再写 succeeded 事件和素材；重复轮询不重复建素材。
2. score 必须为 0-5；审核状态只能是三种枚举。
3. 终态任务不可取消；成功任务不可重试。
4. 前端每 2 秒刷新详情，页面隐藏时暂停，失败请求显示错误但不清空已有数据。

## 6. File plan

| Area | Files | Responsibility |
| --- | --- | --- |
| Backend | `schema.sql`, `app.py` | 素材表、事件查询、审核 API、worker 落库 |
| Frontend | `web/index.html`, `web/app.js`, `web/styles.css` | 任务/素材卡片、轮询、审核控件 |
| Tests | `tests/test_api.py` | 任务生命周期、权限、素材审核 |

## 7. Acceptance criteria

- Given image/video job is created, within 3 seconds detail shows running→succeeded events and one asset.
- Given failed/timeout job, operator can retry; pending/running job can cancel; viewer receives 403.
- Given asset, operator can approve/reject and set score 0-5; invalid score/status receives 400.
- Given product detail, jobs include chronological events and assets are visible in the single-page UI.
