# LangGraph 商品诊断工作流

当前工作流节点：

```text
load product → analyze with AIProvider → persist diagnosis
```

安装 `langgraph` 后自动使用 StateGraph；未安装时走同一 Provider 的顺序回退路径。后续节点可扩展为竞品加载、受众分析、风险分析和人工审核 checkpoint，API 契约不变。
