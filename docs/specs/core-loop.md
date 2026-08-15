# Core Loop Module Spec

## 1. Module goal and scope

- Goal: 用一个商品完成可重复的运营闭环。
- Actors: admin/operator 可写；viewer 只读。
- In scope: 认证、店铺/商品、SKU 库存、竞品、诊断、方案、异步任务、经营数据、复盘。
- Out of scope: 真实平台授权、自动广告执行、真实模型供应商。

## 2. User flows and surfaces

| Surface | Role | Primary actions | States |
| --- | --- | --- | --- |
| 工作台 | all | 查看店铺/商品、创建演示数据 | loading/empty/error/success |
| 商品详情 | all/write | 查看并编辑商品、生成诊断/方案 | loading/empty/error/success |
| 任务与复盘 | all/write | 轮询任务、重试/取消、录入数据、生成报告 | pending/running/succeeded/failed/cancelled |

## 3. Data entities

MVP 表：`users`、`stores`、`products`、`product_skus`、`inventory_items`、`competitors`、`product_diagnoses`、`creative_plans`、`generation_jobs`、`generation_job_events`、`performance_records`、`review_reports`。所有业务实体通过 `product_id` 归属商品；时间字段使用 UTC ISO 字符串。

状态：商品 `draft|active|inactive`；方案 `draft|selected|archived`；任务 `pending|running|succeeded|failed|cancelled|timeout`。

## 4. API contract

统一前缀 `/api/v1`，Bearer token。核心接口：`POST /auth/login`、`GET /auth/me`、`GET/POST /stores`、`GET/POST/PATCH /products`、`POST /products/{id}/diagnoses/generate`、`POST /products/{id}/creative-plans/{type}/generate`、`POST /products/{id}/generation-jobs/{id}/retry|cancel`、`POST /products/{id}/performance-records`、`POST /products/{id}/review-reports/generate`、`POST /workspace/demo-data`。

错误：`{"code":"...","message":"...","details":{}}`。重复生成请求使用 `Idempotency-Key`（相同商品和类型的 pending/running 任务复用）。

## 5. Business rules

1. viewer 的所有 POST/PATCH 返回 403。
2. 诊断/方案/任务/经营数据/复盘必须引用存在的商品。
3. 任务只允许从 failed/timeout 重试，从 pending/running 取消；终态不可变。
4. 经营数据周期结束不得早于开始；指标不得为负数。
5. 复盘由最近一段经营数据聚合生成，允许人工编辑后保存（MVP 返回生成快照）。

## 6. File plan

| Area | Files |
| --- | --- |
| Backend | `app.py`, `schema.sql`, `requirements.txt` |
| Frontend | `web/index.html`, `web/app.js`, `web/styles.css` |
| Tests | `tests/test_api.py` |

## 7. Acceptance criteria

- Given 有效账号，登录返回 token，viewer 写操作被拒绝。
- Given 商品存在，生成诊断包含七个结构化字段；主图/视频方案各至少 3 条。
- Given 任务 pending，刷新后可看到事件和 succeeded；失败任务可重试、运行中可取消。
- Given 有效经营数据，生成复盘包含周期摘要、核心洞察、问题判断、下一步动作。
- 新环境调用演示数据接口后可直接跑通上述链路。

## 8. Verification

运行 `python -m unittest discover -s tests`；手动执行 `python app.py` 后打开 `http://127.0.0.1:8000/`。
