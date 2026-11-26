# DEPENDENCIES — Unity 包与外部插件台账（L2 模块级引用项）

## 引擎包（Packages/manifest.json）

| 包 | 版本 | 用途 | 备注 |
| --- | --- | --- | --- |
| com.unity.2d.sprite | 1.0.0 | 2D Sprite 工作流 | 2D 模板默认 |
| com.unity.2d.tilemap | 1.0.0 | 瓦片地图 | 关卡搭建 |
| com.unity.inputsystem | 1.7.0 | New Input System | 表现层与设备解耦；Active Input Handling 切换需用户在 ProjectSettings 手工执行 |
| com.unity.test-framework | 1.1.33 | EditMode/PlayMode 测试 | EditMode 基线 6 用例 |
| com.unity.ugui | 1.0.0 | UI（UGUI） | 文本更新注意 0 GC |

Unity 内置模块条目（physics2d、audio、animation 等）由编辑器首次打开时自动补全，不手工维护。

## 外部插件 / Asset Store 资产

| 包 | 用途 | 引入理由（量化收益） | 移除成本 |
| --- | --- | --- | --- |
| （暂无） | — | — | — |

## 新增依赖审批规则

1. 默认禁止新增或升级（含 manifest.json、插件、渲染管线变更）；需要时在任务书 Constraints 与 Risks 披露。
2. 引入必须附带：量化收益、维护活跃度、移除成本、降级/原生替代方案。
3. 能 Unity 原生不引入第三方；引入后同步本表与 ARCHITECTURE.md。
4. manifest.json / ProjectSettings / 渲染管线变更一律需要重新审批（v4.0 第 10.4 节）。

---
最后核验日期：2026-11-16｜分支：main｜维护人：<项目 Owner>
