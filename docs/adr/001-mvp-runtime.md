# ADR-001：MVP 运行时选择

## 状态

已接受

## 背景

项目需要在新环境快速演示，且当前阶段重点是验证业务闭环，不应被依赖安装和外部服务阻塞。

## 决策

使用 Python 标准库 HTTP Server + SQLite + 原生 HTML/JS；异步素材任务由进程内 worker 模拟。AI、平台授权、对象存储和队列通过 API/表结构预留替换边界。

## 后果

- 优点：零第三方依赖、启动快、演示可重复。
- 限制：内存 token 重启失效，单进程 worker 不适合生产并发，SQLite 不适合多实例写入。
- 升级路径：JWT、PostgreSQL、Redis/Celery、对象存储和真实供应商适配器。
