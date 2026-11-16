using UnityEngine;

namespace GAMEDEV.Core
{
    /// <summary>
    /// 独立时间通道：顿帧（Hit-stop）与慢动作不得篡改全局 <see cref="Time.timeScale"/>，
    /// 否则会连带暂停 UI、音频与补间。所有依赖游戏节奏的系统读取 <see cref="ScaledDeltaTime"/>
    /// 替代 Time.deltaTime；全局暂停仍用 Time.timeScale = 0，两层语义分离。
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class GameClock : MonoBehaviour
    {
        private float _timeScale = 1f;
        private float _freezeRemaining;
        private float _freezeScale;

        /// <summary>本帧的游戏时间步长（已叠加通道缩放与冻结窗口）。</summary>
        public float ScaledDeltaTime { get; private set; }

        /// <summary>是否处于冻结（顿帧）窗口内。</summary>
        public bool Frozen => _freezeRemaining > 0f;

        /// <summary>设置常驻通道缩放（1 = 正常，0.5 = 慢动作）；不改全局 timeScale。</summary>
        public void SetChannelScale(float scale)
        {
            _timeScale = Mathf.Clamp(scale, 0f, 4f);
        }

        /// <summary>触发顿帧。<paramref name="duration"/> 为真实秒数；
        /// <paramref name="scale"/> 为冻结期间的时间比例（0 = 完全冻结，默认）。</summary>
        public void Freeze(float duration, float scale = 0f)
        {
            if (duration <= 0f)
            {
                return;
            }

            // 重复触发取更长窗口，避免轻击顿帧覆盖重击顿帧。
            _freezeRemaining = Mathf.Max(_freezeRemaining, duration);
            _freezeScale = Mathf.Clamp01(scale);
        }

        /// <summary>立即解除冻结窗口（下一帧恢复正常步长）。</summary>
        public void ClearFreeze()
        {
            _freezeRemaining = 0f;
        }

        /// <summary>
        /// 推进时间通道。由 <see cref="Update"/> 以 Time.unscaledDeltaTime 驱动；
        /// 公开为方法以便 EditMode 测试与确定性回放直接调用。
        /// </summary>
        public void Tick(float unscaledDeltaTime)
        {
            if (unscaledDeltaTime < 0f)
            {
                return;
            }

            if (_freezeRemaining > 0f)
            {
                _freezeRemaining -= unscaledDeltaTime;
                ScaledDeltaTime = unscaledDeltaTime * _freezeScale;
            }
            else
            {
                ScaledDeltaTime = unscaledDeltaTime * _timeScale;
            }
        }

        private void Update()
        {
            Tick(Time.unscaledDeltaTime);
        }
    }
}
