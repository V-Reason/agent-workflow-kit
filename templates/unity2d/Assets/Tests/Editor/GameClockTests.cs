using GAMEDEV.Core;
using NUnit.Framework;
using UnityEngine;

namespace GAMEDEV.Tests
{
    /// <summary>
    /// GameClock 独立时间通道的 EditMode 测试。
    /// 运行方式：Window &gt; General &gt; Test Runner &gt; EditMode。
    /// </summary>
    public sealed class GameClockTests
    {
        private GameObject _owner;

        [SetUp]
        public void SetUp()
        {
            _owner = new GameObject("GameClockUnderTest");
        }

        [TearDown]
        public void TearDown()
        {
            Object.DestroyImmediate(_owner);
        }

        [Test]
        public void Tick_WithoutFreeze_PassesUnscaledTimeThrough()
        {
            var clock = _owner.AddComponent<GameClock>();

            clock.Tick(0.016f);

            Assert.That(clock.ScaledDeltaTime, Is.EqualTo(0.016f).Within(1e-6f));
            Assert.That(clock.Frozen, Is.False);
        }

        [Test]
        public void Tick_WhileFrozen_ZeroesScaledDeltaTime()
        {
            var clock = _owner.AddComponent<GameClock>();
            clock.Freeze(0.12f); // 重击顿帧 0.12s，比例 0（完全冻结）

            clock.Tick(0.016f);

            Assert.That(clock.Frozen, Is.True);
            Assert.That(clock.ScaledDeltaTime, Is.EqualTo(0f).Within(1e-6f));
        }

        [Test]
        public void Tick_AfterFreezeExpires_ResumesFullTime()
        {
            var clock = _owner.AddComponent<GameClock>();
            clock.Freeze(0.10f);
            clock.Tick(0.10f); // 冻结窗口耗尽（仍在窗口内：本帧缩放为 0）
            Assert.That(clock.ScaledDeltaTime, Is.EqualTo(0f).Within(1e-6f));

            clock.Tick(0.016f); // 下一帧恢复正常

            Assert.That(clock.Frozen, Is.False);
            Assert.That(clock.ScaledDeltaTime, Is.EqualTo(0.016f).Within(1e-6f));
        }

        [Test]
        public void Freeze_OverlappingTakes_LongerWindow()
        {
            var clock = _owner.AddComponent<GameClock>();
            clock.Freeze(0.03f); // 轻攻击顿帧
            clock.Freeze(0.12f); // 重攻击顿帧覆盖

            clock.Tick(0.05f);

            Assert.That(clock.Frozen, Is.True); // 窗口应按 0.12s 而不是 0.03s
        }

        [Test]
        public void ClearFreeze_ImmediatelyUnfreezes()
        {
            var clock = _owner.AddComponent<GameClock>();
            clock.Freeze(0.12f);
            clock.ClearFreeze();

            clock.Tick(0.016f);

            Assert.That(clock.Frozen, Is.False);
            Assert.That(clock.ScaledDeltaTime, Is.EqualTo(0.016f).Within(1e-6f));
        }

        [Test]
        public void Tick_NegativeInput_Ignored()
        {
            var clock = _owner.AddComponent<GameClock>();
            clock.Freeze(0.10f);

            clock.Tick(-1f); // 非法输入不推进、不产生 NaN

            Assert.That(clock.ScaledDeltaTime, Is.EqualTo(0f).Within(1e-6f));
            Assert.That(clock.Frozen, Is.True);
        }
    }
}
