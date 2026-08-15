# AI Provider Boundary

API 和任务 worker 不直接依赖具体模型 SDK。`backend/ai_provider.py` 定义 `AIProvider` 协议，当前 `DemoAIProvider` 保证本地可重复演示；生产环境通过 `get_ai_provider()` 替换为真实模型实现。

后续 LangGraph 只负责编排 `diagnose_product`、`generate_review` 等节点，并通过检查点和人工审核暂停恢复；Provider 负责单次模型调用和结构化输出校验。
