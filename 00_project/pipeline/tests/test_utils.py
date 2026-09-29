import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import utils


class TestImportIsSideEffectFree(unittest.TestCase):
    """Review Focus 的根因测试：模块层跑 CLI 会污染 import。"""

    def test_importing_shot_prints_nothing(self):
        import subprocess
        r = subprocess.run(
            [sys.executable, "-c", "import shot"],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            capture_output=True, text=True,
        )
        self.assertEqual(0, r.returncode, r.stderr)
        self.assertEqual("", r.stdout, "import shot 打印了内容 —— CLI 没收进 __main__")

    def test_importing_review_prints_nothing(self):
        import subprocess
        r = subprocess.run(
            [sys.executable, "-c", "import review"],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            capture_output=True, text=True,
        )
        self.assertEqual(0, r.returncode, r.stderr)
        self.assertEqual("", r.stdout, "import review 打印了内容 —— CLI 没收进 __main__")


class TestSpecIsSingleSource(unittest.TestCase):
    """规格值只在 utils.py 定义。别的模块硬编码就是漂移。"""

    def test_shot_does_not_define_spec_constants(self):
        import shot
        for name in ("BLENDER_VERSION", "RESOLUTION", "FPS", "SHUTTER_ANGLE", "SENSOR_WIDTH"):
            self.assertFalse(
                hasattr(shot, name) or name in vars(shot),
                f"shot.py 仍自己定义 {name} —— 应改为读 utils.{name}",
            )

    def test_review_does_not_define_fps(self):
        import review
        self.assertNotIn("FPS", vars(review), "review.py 仍自己定义 FPS")

    def test_shutter_and_sensor_live_in_utils(self):
        """这两个原本只在 shot.py；utils 必须齐全才算唯一来源。"""
        self.assertEqual(180.0, utils.SHUTTER_ANGLE)
        self.assertEqual(36.0, utils.SENSOR_WIDTH)


class TestShutter(unittest.TestCase):
    def test_shutter_deg_converts_to_frames(self):
        """180° = 0.5 帧。直接写 180.0 会得到 180 帧模糊且不报错。"""
        self.assertEqual(0.5, utils.shutter_frames())


class TestLocks(unittest.TestCase):
    def test_version_prefix_is_first_two_segments(self):
        self.assertEqual("5.2", utils.REQUIRED_VERSION_PREFIX)
        self.assertEqual(
            utils.REQUIRED_VERSION_PREFIX,
            ".".join(utils.BLENDER_VERSION.split(".")[:2]),
        )


class TestObjectName(unittest.TestCase):
    def test_keeps_uppercase_prefix(self):
        """normalize_name 会转小写，违反 dls.md 的 GEO_/CAM_/LGT_ 前缀规范"""
        self.assertEqual("CAM_cam", utils.make_object_name("CAM", "cam"))
        self.assertEqual("GEO_grayball", utils.make_object_name("GEO", "grayball"))
        self.assertEqual("LGT_key", utils.make_object_name("LGT", "key"))

    def test_normalize_name_is_for_asset_ids(self):
        """资产 ID 走 normalize_name（小写下划线），与对象名划清边界"""
        self.assertEqual("chr_hero", utils.normalize_name("CHR-Hero"))

    def test_strips_illegal_chars(self):
        # `-` 和空格各换成一个 `_`，两个不同字符之间不会合并
        self.assertEqual("GEO_a_b_c", utils.make_object_name("GEO", "a-b c"))

    def test_empty_name_returns_prefix(self):
        self.assertEqual("GEO", utils.make_object_name("GEO", "---"))
