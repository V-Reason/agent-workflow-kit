using UnityEngine;

namespace GAMEDEV.Core
{
    /// <summary>
    /// 组合根引导（Composition Root）：唯一装配入口。
    /// 核心服务在此创建并互相连接；任何"跨系统粘合"逻辑禁止散落到 Gameplay/UI 层，
    /// 需要新增服务时在 Awake 内追加装配步骤，而不是另立全局管理器。
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class GameBootstrap : MonoBehaviour
    {
        /// <summary>当前引导实例；重复加载场景时由本类自行去重，外部不得赋值。</summary>
        public static GameBootstrap Instance { get; private set; }

        /// <summary>核心时间通道（顿帧/慢动作）。表现层读 ScaledDeltaTime，不读 Time.deltaTime。</summary>
        public GameClock Clock { get; private set; }

        private void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }

            Instance = this;
            DontDestroyOnLoad(gameObject);

            Clock = GetComponent<GameClock>();
            if (Clock == null)
            {
                Clock = gameObject.AddComponent<GameClock>();
            }

            Debug.Log("[GameBootstrap] 组合根装配完成");
        }

        private void OnDestroy()
        {
            if (Instance == this)
            {
                Instance = null;
            }
        }
    }
}
