# CONTEXT PACKET v01 — 上下文包模板（第 6 章）

> 使用：复制到任务目录并改名 CONTEXT_PACKET_vNN.md（v02、v03 递增）；内容按层裁剪，禁止全量投喂。

版本: v01
核验 commit: <7-40 位 commit 哈希；无 Git 时写可恢复副本时间>
预算声明: 固定前缀 <tokens> + L2 <tokens> + L3 <tokens> = 合计 <tokens>（上限 150,000）

## 固定前缀（4,000–8,000 tokens，长期稳定，引用不复制全文）

- CODING_STANDARDS.md 全文（约 <n> tokens）
- PROJECT_OVERVIEW.md 全文
- BUILD_AND_TEST.md 全文

## 模块级 L2 选段（≤ 30,000 tokens）

- ARCHITECTURE.md 第 <n> 节：<节标题>
- MODULE_MAP.md 相关行：<路径列表>

## 代码级 L3 文件清单（≤ 100,000 tokens，一次性内容）

| 路径 | 读取理由 | 预估 tokens |
| --- | --- | --- |
| <src/app/...> | <为什么本任务需要读> | <n> |

## 明确排除项（防止注意力稀释）

- <与任务无关的大文件/目录，逐条列出>
