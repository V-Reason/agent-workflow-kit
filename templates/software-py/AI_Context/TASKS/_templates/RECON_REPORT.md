# RECON REPORT（只读调查，禁止写入）— 附录 F 模板

> 使用：上下文缺失或超预算时由取材员（只读形态）填写，产出后并入上下文包；不构成执行授权。

Task ID: GD-YYYY-NNNN / 请求人: <用户或 Planner> / 调查时间: <YYYY-MM-DD HH:MM 时区>
调查者: <Agent 平台只读任务 或 Executor 只读形态>

## 1. Scope
允许读取的路径与搜索范围（逐条列出）：
- <路径/关键词 1>
- <路径/关键词 2>

## 2. Repo Map Check
MODULE_MAP 核验：<一致 / 漂移>（漂移文件与现状逐条列出）

## 3. Key Files
| 路径 | 一句话职责 |
| --- | --- |
| <路径> | <职责> |

## 4. Interface Facts
接口与依赖事实，每条标 VERIFIED / OBSERVED / INFERRED：
- <事实 1（VERIFIED）>
- <事实 2（INFERRED，验证方式：...）>

## 5. Risks
风险点与疑似坑（引用文件与行号）：
- <风险 1>

## 6. Context Packet
建议包：固定前缀复用项 + L2 选段 + L3 文件，预估 tokens 与成本
- 固定前缀：<复用 vNN>；L2：<选段>；L3：<文件清单，预估 <n> tokens>

## 7. Evidence
命令、搜索关键词与输出位置：
- <命令 / 关键词 → EVIDENCE 路径>

去向：并入 Context Packet（版本号递增）→ 回 PLANNING / 原阶段。
本报告不构成执行授权，不得包含任何项目文件修改。
