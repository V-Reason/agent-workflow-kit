using System;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace AgentWorkflow.EditorTools
{
    public static class WorkflowAuditWindow
    {
        private static readonly string[] RequiredFiles =
        {
            "AGENTS.md",
            "AI_Context/WORKFLOW_PROFILE.toml",
            "AI_Context/WORKFLOW_LOCK.toml",
            "AI_Context/PROJECT_BOARD.md",
            "scripts/workflow.py",
            "scripts/stage_context.py",
            "scripts/validate_handover.py",
            ".agents/skills/worker-engine/SKILL.md",
        };

        [MenuItem("Tools/Agent Workflow/Workflow Audit")]
        public static void RunAudit()
        {
            var projectRoot = Directory.GetParent(Application.dataPath)?.FullName;
            if (string.IsNullOrWhiteSpace(projectRoot))
            {
                Debug.LogError("[AgentWorkflow] 无法定位 Unity 项目根。");
                return;
            }

            var failures = 0;
            foreach (var relative in RequiredFiles)
            {
                var path = Path.Combine(projectRoot, relative);
                if (File.Exists(path))
                {
                    continue;
                }

                failures++;
                Debug.LogError($"[AgentWorkflow] 缺少文件：{relative}");
            }

            var skillRoot = Path.Combine(projectRoot, ".agents", "skills");
            var skillCount = Directory.Exists(skillRoot)
                ? Directory.GetDirectories(skillRoot).Length
                : 0;
            if (skillCount != 8)
            {
                failures++;
                Debug.LogError($"[AgentWorkflow] 技能数量应为 8，实际为 {skillCount}。");
            }

            if (failures == 0)
            {
                Debug.Log("[AgentWorkflow] Workflow Audit PASS：FAIL=0。");
            }
            else
            {
                Debug.LogError($"[AgentWorkflow] Workflow Audit FAIL：FAIL={failures}。");
            }
        }
    }
}
