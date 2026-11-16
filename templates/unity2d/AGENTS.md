# AGENTS.md — <项目名> 项目级 Agent 规范（Unity 2D）

> 本文件与套件总纲（agent-workflow-kit/AGENTS.md）叠加生效；本文件缺失的条款一律以套件总纲为准。
> 每个会话启动必读；本项目类型为 **Unity 2D 游戏**（asmdef 分层，Unity 2022.3 LTS / Unity 6）。

## 0. 授权门（最高优先级）

- 只有用户明确批准的任务书版本（Status: APPROVED + APPROVAL_RECORD.md）构成写入授权。
- 未批准：只读模式，可做 Preflight 检查与只读调查，禁止任何写入。
- 修改范围 = 任务书第 6 章 File Scope 逐路径白名单；越界即停。

## 1. 资产红线（Unity 特有，宁停勿猜）

1. Agent 不写 `.prefab` / `.unity` / `.asset` / `.unitypackage` / `.xlsx` 等序列化与二进制资产；这类改动一律进"用户手工清单"（每条含路径、期望值、判据），由用户在编辑器完成。
2. `.meta` 必须与资产同进同出；发现资产与 .meta 不匹配、GUID 引用断裂的可能时立即停止。
3. `Packages/manifest.json`、`ProjectSettings/`、渲染管线配置、asmdef 变更默认禁止，需重新审批。
4. 不删除看似无用的资产、元文件或目录；引用断裂在编辑器里才可见，Git 层面看不出来。
5. 高风险操作三件套：备份分支 + `--no-commit --no-ff` + 每文件一句话回滚命令。

## 2. 门禁清单（VALIDATING 前必须全过）

| 门禁 | 操作 | 期望 |
| --- | --- | --- |
| 编译 | Unity 打开工程 | Console 0 error |
| EditMode 测试 | Test Runner > EditMode > Run All | 全绿（基线 6 用例） |
| 结构审计 | GAMEDEV > 审计 > 项目结构审计 | FAIL = 0 |
| 交接包校验 | `python scripts/validate_handover.py <任务目录> --for verifier` | exit 0 |

批处理审计命令见 `AI_Context/BUILD_AND_TEST.md`。

## 3. 分层红线（对齐 AI_Context/ARCHITECTURE.md）

1. 依赖方向：Gameplay → Core，UI → Gameplay → Core，EditorTools → Core；改 asmdef references 需重审。
2. Editor 代码只放 Editor 程序集；测试只放 Tests 程序集（UNITY_INCLUDE_TESTS）。
3. 新系统默认放入现有层；新增程序集必须先登记 DECISION_LOG.md。
4. Hot-Path 0 GC；物理走 FixedUpdate + Interpolate；高频检测 NonAlloc；渲染层级用 Sorting Layer。

## 4. 文件操作边界

| 操作 | 默认 | 需要批准 |
| --- | --- | --- |
| 读 src 脚本/AI_Context/文档 | 允许 | 用户目录、密钥 |
| 创建/修改 .cs / .asmdef / .md | 仅任务书白名单路径 | 白名单外任何路径 |
| 资产（prefab/unity/asset/xlsx） | 禁止 | 永远走用户手工清单 |
| 删除/重命名 | 禁止 | 逐路径列出并说明回滚 |
| manifest/ProjectSettings/管线 | 禁止 | 任务书披露 + 用户批准 |
| Git commit/push | 禁止 | 用户明确说"提交" |

## 5. 执行纪律

1. Preflight 六项逐项完成并写入执行报告第 1 节；Unity 版本与打开状态在 Preflight 记录。
2. 不虚构 API：Unity API 先核对当前版本（2022.3 LTS / Unity 6 差异显著）；不把编译通过当成功能正确。
3. 编译通过只证明语法接受；生命周期、序列化、Prefab 引用、管线兼容必须分开验证。
4. 尝试额度 A01–A03；停止条件见套件总纲第 7/10 节；连续两轮无可验证进展即停。
5. 长任务安排在错峰时段（北京时间 12:00–14:00、18:00–次日 09:00、周末节假日）。

## 6. 交接与归档

- 任务目录：`AI_Context/TASKS/GD-YYYY-NNNN/`（七件套模板在 `TASKS/_templates/`）。
- 证据归档：`AI_Context/EVIDENCE/GD-YYYY-NNNN/`（Console 截图、Test Runner 结果、审计输出）。
- 验收通过 24 小时内提交上下文回写提案，用户审阅合入；MODULE_MAP 漂移随之修正。

## 7. 技能装载

| 场景 | 加载 |
| --- | --- |
| 规划/分级/任务书 | planner-orchestrator（+ unity2d-architect 叠加；玩法系统 + game-systems-designer） |
| 执行 | executor-engine（单独装载；顾问约束已固化在批准版任务书第 4/5/8 章中，执行期不重复挂载顾问） |
| 验证 | engineering-verifier（独立会话/实例，禁止自证） |
| 失败/指标复盘 | failure-retrospector |
