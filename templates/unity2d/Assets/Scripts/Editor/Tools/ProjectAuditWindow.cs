using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace GAMEDEV.EditorTools
{
    /// <summary>
    /// 项目结构审计：检查目录约定、程序集定义与关键文件是否齐备，输出 PASS / WARN / FAIL 清单。
    /// 对应 AGENTS.md 第 1 节门禁，可在任务书第 10 章（Test Plan）引用。
    /// GUI 入口：菜单 GAMEDEV/审计/项目结构审计；
    /// 批处理入口：RunBatchAudit（FAIL 大于 0 时以退出码 1 结束，供 CI 拦截）。
    /// </summary>
    public sealed class ProjectAuditWindow : EditorWindow
    {
        private const string StatusPass = "PASS ";
        private const string StatusWarn = "WARN ";
        private const string StatusFail = "FAIL ";

        private readonly List<string> _lines = new List<string>();
        private Vector2 _scroll;

        [MenuItem("GAMEDEV/审计/项目结构审计", priority = 0)]
        public static void Open()
        {
            var window = GetWindow<ProjectAuditWindow>("项目结构审计");
            window.RunAudit();
        }

        private void OnGUI()
        {
            if (GUILayout.Button("重新审计"))
            {
                RunAudit();
            }

            _scroll = GUILayout.BeginScrollView(_scroll);
            foreach (string line in _lines)
            {
                EditorGUILayout.LabelField(line, EditorStyles.wordWrappedLabel);
            }
            GUILayout.EndScrollView();
        }

        private void RunAudit()
        {
            _lines.Clear();
            RunAuditCore(_lines, out int failCount, out int warnCount);
            Debug.Log($"[ProjectAudit] FAIL {failCount} / WARN {warnCount}（详见审计窗口）");
        }

        /// <summary>
        /// 纯静态审计核心：不触碰 EditorWindow 与 OnGUI，GUI 与批处理共用同一套逻辑。
        /// 将审计清单逐行写入 lines（PASS / WARN / FAIL 前缀），通过 out 参数返回统计。
        /// </summary>
        /// <returns>FAIL 条数</returns>
        public static int RunAuditCore(List<string> lines, out int failCount, out int warnCount)
        {
            string projectRoot = Directory.GetParent(Application.dataPath).FullName;

            // ---- 1. 脚本分层目录与程序集定义 ----
            CheckDirectory(lines, "Assets/Scripts/Core");
            CheckDirectory(lines, "Assets/Scripts/Gameplay");
            CheckDirectory(lines, "Assets/Scripts/UI");
            CheckDirectory(lines, "Assets/Scripts/Editor");

            CheckFile(lines, Path.Combine(projectRoot, "Assets/Scripts/Core/Core.asmdef"), "Core.asmdef");
            CheckFile(lines, Path.Combine(projectRoot, "Assets/Scripts/Gameplay/Gameplay.asmdef"), "Gameplay.asmdef");
            CheckFile(lines, Path.Combine(projectRoot, "Assets/Scripts/UI/UI.asmdef"), "UI.asmdef");
            CheckFile(lines, Path.Combine(projectRoot, "Assets/Scripts/Editor/Editor.asmdef"), "Editor.asmdef");
            CheckFile(lines, Path.Combine(projectRoot, "Assets/Tests/Editor/Tests.Editor.asmdef"), "Tests.Editor.asmdef");

            // ---- 2. 工作流关键文件 ----
            CheckFile(lines, Path.Combine(projectRoot, "AGENTS.md"), "AGENTS.md（项目级 Agent 规范）");
            CheckFile(lines, Path.Combine(projectRoot, "README.md"), "README.md");
            CheckFile(lines, Path.Combine(projectRoot, "AI_Context/README_AI.md"), "AI_Context/README_AI.md");
            CheckFile(lines, Path.Combine(projectRoot, "AI_Context/PROJECT_OVERVIEW.md"), "AI_Context/PROJECT_OVERVIEW.md");
            CheckFile(lines, Path.Combine(projectRoot, "AI_Context/MODULE_MAP.md"), "AI_Context/MODULE_MAP.md");
            CheckFile(lines, Path.Combine(projectRoot, "AI_Context/PROJECT_BOARD.md"), "AI_Context/PROJECT_BOARD.md（Secretary 台账）");
            CheckFile(lines, Path.Combine(projectRoot, "scripts/validate_handover.py"), "scripts/validate_handover.py（交接包校验器）");
            CheckFile(lines, Path.Combine(projectRoot, "scripts/stage_context.py"), "scripts/stage_context.py（物理投喂箱）");

            // ---- 3. 资产目录 ----
            CheckDirectory(lines, "Assets/Art");
            CheckDirectory(lines, "Assets/Scenes");
            CheckDirectory(lines, "Assets/Prefabs");
            CheckDirectory(lines, "Assets/Tests/Editor");

            // ---- 4. 命名与 meta 检查（仅 Assets/Scripts 下） ----
            int scriptCount = 0;
            int missingMeta = 0;
            int badNaming = 0;
            string scriptsRoot = Path.Combine(Application.dataPath, "Scripts");
            if (Directory.Exists(scriptsRoot))
            {
                foreach (string file in Directory.GetFiles(scriptsRoot, "*.cs", SearchOption.AllDirectories))
                {
                    scriptCount++;
                    string fileName = Path.GetFileName(file);
                    if (!IsPascalCaseFileName(fileName))
                    {
                        badNaming++;
                        AddLine(lines, StatusWarn, $"命名不符 PascalCase：Assets/Scripts/{fileName}");
                    }

                    if (!File.Exists(file + ".meta"))
                    {
                        missingMeta++;
                        AddLine(lines, StatusFail, $"缺少 .meta：{fileName}（Unity 打开后会自动生成）");
                    }
                }
            }

            AddLine(
                lines,
                missingMeta == 0 ? StatusPass : StatusFail,
                $"脚本 .meta 完整性：{scriptCount} 个脚本，缺 {missingMeta} 个 meta");
            AddLine(
                lines,
                badNaming == 0 ? StatusPass : StatusWarn,
                $"命名检查：{badNaming} 个文件名不符 PascalCase");

            failCount = CountLines(lines, StatusFail);
            warnCount = CountLines(lines, StatusWarn);
            AddLine(lines, StatusPass, $"审计完成：FAIL {failCount} / WARN {warnCount}");
            return failCount;
        }

        /// <summary>
        /// 无头批处理入口（CI 门禁）：
        ///   "Unity编辑器路径" -batchmode -nographics -projectPath "工程根"
        ///     -executeMethod GAMEDEV.EditorTools.ProjectAuditWindow.RunBatchAudit -logFile audit.log
        /// 逐条输出审计日志（FAIL 行用 Error 级别），最后以 EditorApplication.Exit 显式控制退出码：
        /// FAIL 大于 0 → 1，否则 → 0。因此命令中不要追加 -quit。
        /// </summary>
        public static void RunBatchAudit()
        {
            var lines = new List<string>();
            int failCount = RunAuditCore(lines, out _, out int warnCount);
            foreach (string line in lines)
            {
                if (line.StartsWith(StatusFail, System.StringComparison.Ordinal))
                {
                    Debug.LogError(line);
                }
                else
                {
                    Debug.Log(line);
                }
            }

            Debug.Log($"[ProjectAudit] 批处理审计完成：FAIL {failCount} / WARN {warnCount}，退出码 {(failCount > 0 ? 1 : 0)}");
            EditorApplication.Exit(failCount > 0 ? 1 : 0);
        }

        private static bool IsPascalCaseFileName(string fileName)
        {
            string stem = Path.GetFileNameWithoutExtension(fileName);
            return stem.Length > 0 && char.IsUpper(stem[0]);
        }

        private static void CheckDirectory(List<string> lines, string relativePath)
        {
            string full = Path.Combine(Application.dataPath, "..", relativePath);
            bool exists = Directory.Exists(full);
            AddLine(
                lines,
                exists ? StatusPass : StatusFail,
                $"目录 {relativePath}{(exists ? string.Empty : "（缺失）")}");
        }

        private static void CheckFile(List<string> lines, string fullPath, string label)
        {
            bool exists = File.Exists(fullPath);
            string relative = fullPath.Substring(Directory.GetParent(Application.dataPath).FullName.Length + 1);
            AddLine(
                lines,
                exists ? StatusPass : StatusFail,
                $"文件 {relative}{(exists ? string.Empty : $"（缺失：{label}）")}");
        }

        private static void AddLine(List<string> lines, string status, string message)
        {
            lines.Add($"{status}  {message}");
        }

        private static int CountLines(List<string> lines, string status)
        {
            int count = 0;
            foreach (string line in lines)
            {
                if (line.StartsWith(status, System.StringComparison.Ordinal))
                {
                    count++;
                }
            }
            return count;
        }
    }
}
