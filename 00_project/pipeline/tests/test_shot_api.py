"""`setup_render` / `create_preview` 的 API 层测试。不需要 bpy。

spec §5.2 的核心主张是「一份实现，两个消费者」（模板生成器 + setup_render）。
逐任务审查只验了消费者之一 —— `apply_preset` 全部经由 `build_templates.build`
与 `test_preset` 被测，**真正用来出片的 setup_render 被测 0 次**。
C-2 那个「静默渲 17 帧」就是这么活下来的。

本文件刻意不 import bpy：它跑在纯 Python（系统 python3）下，
所以「无 bpy 时必须返回带 hint 的失败」这条路径在这里是真实执行的。
"""

import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import utils
import shot
import review


def _fake_render_tree(shot_id, version, stage, frame_start, frame_end):
    """造出 create_preview 需要的帧文件名（空文件即可，dry_run 不读内容）。"""
    root = tempfile.mkdtemp()
    d = os.path.join(root, "06_shots", shot_id, "render", stage, version)
    os.makedirs(d)
    for f in range(frame_start, frame_end + 1):
        open(os.path.join(d, f"{shot_id}_{stage}_{version}.{f:04d}.exr"), "wb").close()
    return root


class TestSetupRenderFrameRange(unittest.TestCase):
    """C-2：帧范围缺失必须失败，不是静默落占位"""

    def test_missing_frame_range_returns_ok_false(self):
        r = shot.setup_render("seq010_sh010", "light", project_root="/tmp/opencode")
        self.assertFalse(r["ok"], "未给帧范围却返回 ok=True —— 会静默渲占位帧数")
        self.assertIn("帧范围", r["error"])
        self.assertTrue(r["hint"], "失败必须带 hint")

    def test_missing_frame_range_hint_points_at_shotlist(self):
        r = shot.setup_render("seq010_sh010", "light", project_root="/tmp/opencode")
        self.assertIn("shotlist.csv", r["hint"])

    def test_dry_run_also_refuses_to_guess(self):
        """dry_run 只报告计划，但计划里写 17 帧同样是在骗人"""
        r = shot.setup_render("seq010_sh010", "light", dry_run=True,
                              project_root="/tmp/opencode")
        self.assertFalse(r["ok"], r)
        self.assertIn("帧范围", r["error"])

    def test_dry_run_echoes_given_frame_range(self):
        r = shot.setup_render("seq010_sh010", "light", frame_start=1001, frame_end=1160,
                              dry_run=True, project_root="/tmp/opencode")
        self.assertTrue(r["ok"], r)
        self.assertEqual(1001, r["frame_start"])
        self.assertEqual(1160, r["frame_end"])

    def test_dry_run_does_not_need_bpy(self):
        """dry_run 在纯 Python 下也必须能跑 —— 它不碰 scene"""
        saved = sys.modules.get("bpy", None)
        sys.modules["bpy"] = None
        try:
            r = shot.setup_render("seq010_sh010", "light", frame_start=1001,
                                  frame_end=1160, dry_run=True,
                                  project_root="/tmp/opencode")
        finally:
            if saved is None:
                sys.modules.pop("bpy", None)
            else:
                sys.modules["bpy"] = saved
        self.assertTrue(r["ok"], r)


class TestSetupRenderFailures(unittest.TestCase):
    def test_unknown_stage_returns_ok_false(self):
        r = shot.setup_render("seq010_sh010", "BOGUS_STAGE",
                              frame_start=1001, frame_end=1160,
                              project_root="/tmp/opencode")
        self.assertFalse(r["ok"], r)
        self.assertIn("BOGUS_STAGE", r["error"])
        self.assertIn("light", r["hint"])   # hint 必须列出合法值

    def test_without_bpy_returns_failure_with_hint(self):
        """`import bpy` 失败时必须返回失败 + hint，不是崩栈也不是 ok=True"""
        saved = sys.modules.get("bpy", None)
        sys.modules["bpy"] = None      # 让 import bpy 抛 ImportError
        try:
            r = shot.setup_render("seq010_sh010", "light",
                                  frame_start=1001, frame_end=1160,
                                  project_root="/tmp/opencode")
        finally:
            if saved is None:
                sys.modules.pop("bpy", None)
            else:
                sys.modules["bpy"] = saved
        self.assertFalse(r["ok"], r)
        self.assertIn("bpy", r["error"])
        self.assertIn("blender", r["hint"])

    def test_invalid_view_transform_is_reported_not_raised(self):
        """动态 RNA enum 不能靠 enum_items 校验；赋值失败必须变成 ok:False"""
        r = shot.setup_render("seq010_sh010", "light",
                              view_transform="No Such View Transform 12345",
                              frame_start=1001, frame_end=1160,
                              project_root="/tmp/opencode")
        # 纯 Python 下没有 bpy，会先撞 bpy 守卫；有 bpy 时必须报 view transform
        self.assertFalse(r["ok"], r)


class TestSetupRenderViewTransformPassthrough(unittest.TestCase):
    """I-8：--view-transform 透传。G0-T4 定了关键 FX 镜头要换 Transform，
    透传断了就等于对策失效且没人知道。"""

    def test_dry_run_echoes_view_transform(self):
        r = shot.setup_render("seq010_sh020", "light",
                              view_transform="Khronos PBR Neutral",
                              frame_start=1001, frame_end=1136, dry_run=True,
                              project_root="/tmp/opencode")
        self.assertTrue(r["ok"], r)
        self.assertEqual("Khronos PBR Neutral", r["view_transform"])

    def test_dry_run_note_reads_spec_from_utils(self):
        """dry-run note 里的分辨率/帧率必须来自 utils，不是抄进去的字面量"""
        with mock.patch.object(utils, "RESOLUTION", (640, 360)), \
                mock.patch.object(utils, "FPS", 30):
            r = shot.setup_render("seq010_sh010", "light", frame_start=1001,
                                  frame_end=1160, dry_run=True,
                                  project_root="/tmp/opencode")
        self.assertIn("640x360@30fps", r["note"])


class TestCreateShot(unittest.TestCase):
    def test_frame_range_is_echoed_not_guessed(self):
        """帧范围是 per-shot 数据，缺了就回显 None，不猜"""
        r = shot.create_shot("010", "010", project_root=tempfile.mkdtemp(),
                             dry_run=True)
        self.assertTrue(r["ok"], r)
        self.assertIsNone(r["frame_start"])
        self.assertIsNone(r["frame_end"])

    def test_given_frame_range_is_echoed_verbatim(self):
        r = shot.create_shot("010", "010", frame_start=1001, frame_end=1160,
                             project_root=tempfile.mkdtemp(), dry_run=True)
        self.assertEqual(1001, r["frame_start"])
        self.assertEqual(1160, r["frame_end"])


class TestCreatePreviewFrames(unittest.TestCase):
    def test_missing_frame_range_returns_ok_false(self):
        r = review.create_preview("seq010_sh010", "v001", "light",
                                  project_root=tempfile.mkdtemp(), dry_run=True)
        self.assertFalse(r["ok"], "未给帧范围却返回 ok=True")
        self.assertIn("帧范围", r["error"])
        self.assertIn("shotlist.csv", r["hint"])

    def test_fps_is_single_source_for_timecode_and_encoder(self):
        """⚠️ I-2 里最危险的一处：_timecode 读 utils.FPS 而 ffmpeg -r 写死 24。
        改 FPS 后画面时码与编码帧率不同源 → 时码持续漂移且无任何报错。"""
        root = _fake_render_tree("seq010_sh010", "v001", "light", 1001, 1002)
        with mock.patch.object(utils, "FPS", 25):
            r = review.create_preview("seq010_sh010", "v001", "light",
                                      frame_start=1001, frame_end=1002,
                                      project_root=root, dry_run=True)
            tc = review._timecode(1001)
        self.assertTrue(r["ok"], r)
        self.assertIn(f"-r {25}", r["cmd"])
        # 时码按 25 算：1001 → f=1000，1000//25=40s → 00:00:40:00
        self.assertEqual("00:00:40:00", tc)

    def test_cmd_rate_follows_utils_fps_at_default(self):
        root = _fake_render_tree("seq010_sh010", "v001", "light", 1001, 1002)
        r = review.create_preview("seq010_sh010", "v001", "light",
                                  frame_start=1001, frame_end=1002,
                                  project_root=root, dry_run=True)
        self.assertTrue(r["ok"], r)
        self.assertIn(f"-r {utils.FPS}", r["cmd"])


if __name__ == "__main__":
    # 不能用 unittest.main()：Blender 传进来的是它自己的 argv
    _suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    _result = unittest.TextTestRunner(verbosity=2).run(_suite)
    sys.exit(0 if _result.wasSuccessful() else 1)
