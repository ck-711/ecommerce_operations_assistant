# OpenAI Provider

`backend/ai_provider.py` 提供 OpenAI-compatible 实现，使用 JSON mode 输出结构化结果。生产必须设置 `OPENAI_API_KEY`；可通过 `OPENAI_BASE_URL` 接入兼容 OpenAI 协议的网关。API Key 不写入数据库、不写入日志、不提交仓库。
