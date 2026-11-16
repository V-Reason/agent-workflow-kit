# EXECUTION REPORT — 执行报告模板（附录 E · Unity 版）

> 使用：Worker 每次尝试一份，改名 EXECUTION_REPORT_A01.md / A02 / A03；结论用语严格枚举。

Task ID: GD-YYYY-NNNN / Plan Version: vNN / Attempt: A01
Worker（模型与模式）: <模型 + agent/对话> / 思考档位: <low/medium/high/xhigh/不适用>
执行时间: <YYYY-MM-DD HH:MM 时区> / Unity 版本: <2022.3.x / 6000.x> / 分支与 Base Commit: <...>

## 1. Preflight
- 批准版本核验：<APPROVED + vNN 确认结果>
- 工作区状态：<干净 / 用户修改清单>
- 基线与分支：<...>
- 范围检查：<批准范围逐路径确认结论>

## 2. Actual Changes
- Created: <路径列表，无则 none>
- Modified: <路径列表>
- Deleted: <默认应为 none；出现即触发重审>
- 范围外: <必须为 none>

## 3. Step Results
| # | 步骤 | 结果 | 证据 |
| --- | --- | --- | --- |
| 1 | <对应任务书步骤> | PASS / FAIL / BLOCKED | <输出或日志路径> |

## 4. Commands
| 命令/操作 | 工作目录/位置 | 工具版本 | 退出码/结果 | 日志位置 |
| --- | --- | --- | --- | --- |
| <如：Unity 打开工程编译检查> | <工程根> | <Unity 2022.3.x> | <0 error> | <EVIDENCE 路径> |
| <如：EditMode 测试 Run All> | <Test Runner> | <test-framework 1.1.33> | <n passed> | <EVIDENCE 路径> |

## 5. AC Mapping
| AC | 结果 | 证据 |
| --- | --- | --- |
| AC-01 | PASS / FAIL / NOT RUN | <...> |

## 6. Tests
- 编译：<Console 0 error / 实际错误数>
- EditMode 测试：<通过数 / 总数>
- 结构审计：<GAMEDEV > 审计：FAIL n / WARN n>
- 运行时视觉：<用户实跑项，或 NOT RUN>
- 性能：<Profiler 数据，或 NOT APPLICABLE>

## 7. Usage
输入 tokens: <n> / 输出 tokens: <n> / 缓存命中: <n> / 请求数: <n>

## 8. Deviations
<计划偏离、新依赖、asmdef 变更、回归风险；无则写 none>

## 9. Remaining Issues
<已知限制、阻塞项；无则写 none>

## 10. Rollback
<每文件一句话撤销命令；含 .meta 处理>

## 11. Conclusion
Conclusion: PASS / PASS WITH WARNINGS / FAIL / BLOCKED / NOT RUN
所需决策：<用户需要决定的事项；无则写 none>
