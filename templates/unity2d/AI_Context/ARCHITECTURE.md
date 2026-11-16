# ARCHITECTURE — asmdef 分层与依赖规则（L2 模块级引用项）

## 分层拓扑（VERIFIED，与 Assets/Scripts 实际结构一致）

```text
Assets/Scripts/
  Core/       GAMEDEV.Core        引导（GameBootstrap）、组合根、时间通道（GameClock）
  Gameplay/   GAMEDEV.Gameplay    玩法逻辑；仅依赖 Core
  UI/         GAMEDEV.UI          表现与界面；依赖 Core + Gameplay
  Editor/     GAMEDEV.EditorTools Editor 工具；依赖 Core；仅 Editor 平台
Assets/Tests/Editor/             EditMode 测试；UNITY_INCLUDE_TESTS 限定
Assets/{Art, Scenes, Prefabs}    资产目录；Agent 默认不碰
```

## 依赖方向铁律

1. 单向依赖：Gameplay → Core，UI → Gameplay → Core，EditorTools → Core；严禁循环引用与反向依赖。
2. Runtime 与 Editor 物理隔离：Editor 代码仅存在于 Editor 程序集，严禁打包进构建。
3. 测试隔离：Tests.Editor 定义约束 `UNITY_INCLUDE_TESTS`，不污染运行时。
4. 新增程序集前先问：能否放入现有层？出现第 3 处相似变动才允许新分层。

## 关键设计决策

| 决策 | 理由 | 记录位置 |
| --- | --- | --- |
| 独立时间通道（GameClock） | 顿帧/慢动作不改全局 timeScale，UI 与音频不受牵连 | DECISION_LOG.md ADR-0003 |
| 组合根唯一（GameBootstrap） | 服务装配集中一处，防全局管理器蔓延 | DECISION_LOG.md ADR-0002 |
| 空层骨架（Gameplay/UI 仅 asmdef） | 先立约定后填肉，防结构性返工 | DECISION_LOG.md ADR-0002 |

## 反过度设计约定

出现第 3 处相似变动前，禁止：事件总线框架、DI 容器、独立状态机框架（组合根内解决）、完整 ECS、
通用参数化设施为单次需求服务、为单实现者抽接口、反射注册、独立调试 UI（用 `[ContextMenu]`）。

---
最后核验日期：2026-11-15｜分支：main｜维护人：<项目 Owner>
