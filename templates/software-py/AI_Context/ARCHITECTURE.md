# ARCHITECTURE — 分层架构与依赖规则（L2 模块级引用项）

## 分层拓扑（VERIFIED，与 src/ 实际结构一致）

```text
src/app/
  domain/       实体、值对象、领域错误、纯业务规则；零外部依赖、零 I/O
  application/  用例编排、端口（Protocol）；只依赖 domain
  infra/        仓库实现、外部服务适配器；实现 application 的端口
  interfaces/   CLI / HTTP 处理器（组合根）；依赖 application
tests/unit/         领域与应用层快测
tests/integration/  组合根与真实装配的慢测
```

## 依赖方向铁律

1. 单向依赖：interfaces → application → domain；infra 实现 application 的 Protocol（依赖倒置）。
2. domain 零 I/O、零框架：不发请求、不碰数据库、不读文件。
3. 组合根在 interfaces 层装配具体实现并注入；替换存储只改 `interfaces/cli.py` 的 `build_service()`。
4. 新增分层前先问能否放入现有层；第 3 处相似变动才允许新分层。

## 关键设计决策

| 决策 | 理由 | 记录位置 |
| --- | --- | --- |
| 不可变实体（frozen dataclass） | 跨层值语义、可测试 | DECISION_LOG.md ADR-0002 |
| Protocol 而非抽象基类 | 结构化类型、避免继承耦合 | DECISION_LOG.md ADR-0002 |

## 反过度设计约定

出现第 3 处相似变动前，禁止：抽象基类与泛型基础设施、事件总线、插件机制、自研框架层、过早微服务。

---
最后核验日期：2026-11-15｜分支：main｜维护人：<项目 Owner>
