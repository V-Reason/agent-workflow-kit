using UnityEditor;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace GAMEDEV.EditorTools
{
    /// <summary>
    /// 场景搭建菜单：向当前场景插入 GameBootstrap 组合根对象。
    /// 资产级操作（保存场景、创建 Prefab）由用户在编辑器内完成，本工具只做对象级装配。
    /// </summary>
    public static class BootstrapSceneMenu
    {
        [MenuItem("GAMEDEV/搭建/当前场景插入 GameBootstrap", priority = 0)]
        public static void InsertIntoOpenScene()
        {
            // FindObjectOfType 在 Unity 2022.3 LTS 可用；Unity 6 可改用
            // FindFirstObjectByType<GameBootstrap>()（2023.1+ API），行为一致。
            if (Object.FindObjectOfType<GameBootstrap>() != null)
            {
                EditorUtility.DisplayDialog(
                    "GameBootstrap",
                    "当前场景已存在 GameBootstrap，无需重复插入。",
                    "知道了");
                return;
            }

            var go = new GameObject("GameBootstrap");
            go.AddComponent<GameBootstrap>();
            Undo.RegisterCreatedObjectUndo(go, "Insert GameBootstrap");
            EditorUtility.MarkSceneDirty(go.scene);
            Debug.Log("[BootstrapSceneMenu] 已插入 GameBootstrap；请记得保存场景（Ctrl+S）。");
        }

        [MenuItem("GAMEDEV/搭建/移除当前场景 GameBootstrap", priority = 1)]
        public static void RemoveFromOpenScene()
        {
            GameBootstrap existing = Object.FindObjectOfType<GameBootstrap>();
            if (existing == null)
            {
                EditorUtility.DisplayDialog("GameBootstrap", "当前场景没有 GameBootstrap。", "知道了");
                return;
            }

            Scene scene = existing.gameObject.scene;
            Undo.DestroyObjectImmediate(existing.gameObject);
            EditorUtility.MarkSceneDirty(scene);
            Debug.Log("[BootstrapSceneMenu] 已移除 GameBootstrap；请记得保存场景（Ctrl+S）。");
        }
    }
}
