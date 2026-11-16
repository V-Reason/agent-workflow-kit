# unity2d — Unity 2D 游戏开发项目模板

Agent 工作流 v2.0 配套模板：**asmdef 物理分层 + 组合根引导 + 独立时间通道 + Editor 审计工具 + AI_Context 上下文体系**。本模板是"工程骨架"：程序集边界、引导流程、门禁工具与约定全部就位，玩法代码按约定填入。

## 实例化步骤（复制后必做）

1. **先建工程**：Unity Hub 新建 2D 工程（Unity 2022.3 LTS 或 Unity 6000.x），命名你的项目。
2. **并入骨架**：把本目录的 `Assets/`、`Packages/manifest.json`、`AI_Context/`、`scripts/`、`AGENTS.md`、`README.md`、`.gitignore`、`.gitattributes` 覆盖/合并进新工程根（合并 .gitignore 与 .gitattributes，不要只覆盖）。
3. **打开编译**：Unity 打开工程，等待 Console 编译完成，期望 **0 error**；首次打开会自动生成 .meta 与 manifest 内置模块条目。
4. **跑基线门禁**：Test Runner > EditMode > Run All（期望 6 用例全绿）；GAMEDEV > 审计 > 项目结构审计（期望 FAIL = 0）。
5. **装配引导**：GAMEDEV > 搭建 > 当前场景插入 GameBootstrap，保存场景为 `Assets/Scenes/Bootstrap.unity`。
6. **填上下文**：`AI_Context/PROJECT_OVERVIEW.md` 填定位与技术基线（渲染管线、PPU、分辨率）；`MODULE_MAP.md` 随代码同步。
7. `git init && git add -A && git commit`（由你自己执行，不交 Agent）。

## 结构导览

| 路径 | 内容 |
| --- | --- |
| `Assets/Scripts/Core/` | GAMEDEV.Core：`GameBootstrap`（组合根）、`GameClock`（独立时间通道） |
| `Assets/Scripts/Gameplay/` | GAMEDEV.Gameplay（空骨架 + 层约定 README） |
| `Assets/Scripts/UI/` | GAMEDEV.UI（空骨架 + 层约定 README） |
| `Assets/Scripts/Editor/` | GAMEDEV.EditorTools：项目结构审计窗口、场景搭建菜单 |
| `Assets/Tests/Editor/` | GAMEDEV.Tests.Editor：GameClock 6 个 EditMode 用例 |
| `Assets/{Art,Scenes,Prefabs}` | 资产目录（Agent 默认不碰） |
| `AI_Context/` | v2.0 第 6 章上下文体系 + 交接包模板 |
| `scripts/validate_handover.py` | 交接包校验器（项目内副本） |
| `AGENTS.md` | 项目级 Agent 规范（叠加套件总纲） |

## 关键设计（已登记 DECISION_LOG.md）

- **独立时间通道**：顿帧/慢动作走 `GameClock.ScaledDeltaTime`，不改全局 `Time.timeScale`；表现层禁读 `Time.deltaTime`。
- **组合根唯一**：服务装配只在 `GameBootstrap.Awake`，不另立全局管理器。
- **asmdef 单向依赖**：Gameplay → Core，UI → Gameplay → Core；编译器强制执行。

## 启用 Smart Merge（可选，多人协作推荐）

`.gitattributes` 中的 `merge=unityyamlmerge` 行默认注释。启用：

```bash
git config merge.unityyamlmerge.name "Unity SmartMerge"
git config merge.unityyamlmerge.driver "\"<Unity安装目录>/Editor/Data/Tools/UnityYAMLMerge\" merge -p %O %A %B %L %P"
```

然后把 `.gitattributes` 中对应行取消注释。单人 + Agent 工作流可不启用。

## 与方法论的对应

- 分层与门禁 ↔ v2.0 第 6 章（上下文）、第 12 章（验证层次 V1–V4）
- `AGENTS.md` ↔ 第 3、4、10、11 章的可执行摘要 + 资产红线
- `AI_Context/TASKS/_templates/` ↔ 附录 C–H（Unity 版）
- `METRICS.md` ↔ 第 15 章六项必记指标
