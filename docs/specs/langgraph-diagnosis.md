# LangGraph 商品诊断工作流

当前工作流节点：

```text
load product → analyze with AIProvider → persist diagnosis
```

生产依赖必须安装 `langgraph`；未安装时工作流会明确失败，不再静默回退。诊断、内容方案、投放建议和复盘均通过 LangGraph 图执行；后续节点可扩展为竞品加载、受众分析、风险分析和人工审核 checkpoint，API 契约不变。
