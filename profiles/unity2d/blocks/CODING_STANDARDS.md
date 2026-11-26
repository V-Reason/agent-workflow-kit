## Unity C# 标准

- Runtime 与 Editor 代码物理隔离；新增 asmdef 或 references 必须先批准。
- 物理更新使用 `FixedUpdate`；高频路径用 Profiler 证据而不是口头声明。
- 生命周期、序列化和资产引用分别验证；编译通过不等于运行行为正确。
