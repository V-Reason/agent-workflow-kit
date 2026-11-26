# APPROVAL RECORD — 批准记录模板（第 10.3 节）

> 使用：用户审阅任务书后填写；把 PLAN_vNN.md 的 Status 改为 APPROVED 属于用户的动作，Worker 不得代写。

Task ID / Approved Plan: GD-YYYY-NNNN / vNN
Workflow Version: v3.1
Decision: APPROVED
Approved Write Boundaries:
- MODIFY <目录/模式或精确路径>
- CREATE <目录/模式或精确路径>
Explicitly Forbidden:
- <必须保持为零改动的路径或模式>
Computer-Use Authorization: NONE
<!-- 如需授权：AUTHORIZED: TARGET=<窗口/应用>; ACTIONS=<动作白名单>; SCOPE=<目录/场景范围> -->
Conditions: <附加约束；无则写"无">
Branch / Base Commit: <分支 / commit>
Approver: <批准人>
Approval Time: <YYYY-MM-DD HH:MM (UTC+8)>

附：用户审核七问自查（第 10.1 节）
1. 目标被准确理解、无擅自加需求？
2. 方案符合现有架构、无多余抽象？
3. 写入边界足够小，Forbidden 覆盖依赖、公共接口、配置与资产？
4. 步骤顺序合理、无依赖未确认事实？
5. 验收标准能真正判断功能正确？
6. 风险与回滚充分、不影响未提交修改？
7. 有清晰暂停点与再请示情形？
