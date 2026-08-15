# Redis/Celery Task Spec

## Boundary

FastAPI 负责创建业务记录和投递任务；Celery 负责执行耗时生成、重试和超时扫描；MySQL 负责任务状态与事件持久化；Redis 只作为 broker/result backend，不存业务真相。

## Tasks

- `execute_generation_job(job_id, product_id, job_kind)`：图片/视频任务统一入口，失败自动退避重试最多 3 次。
- `sweep_timeouts()`：定时扫描并标记超时任务。

当前实现使用 demo provider 返回结构化结果，真实 AI provider 在下一阶段注入。
