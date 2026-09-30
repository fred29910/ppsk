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


# 规格值硬编码的收紧验收（I-2）：
#   grep -rn '1920\|1080\|"24"\|1001\|1136' 00_project/pipeline/*.py \
#     | grep -v '^00_project/pipeline/utils.py'
# 必须零命中。逐任务审查用的 `^FPS\|^RESOLUTION` 只查行首模块常量，
# 会被 `"-r", "24"` 这种参数位置与默认参数值绕过 —— review.py 的 ffmpeg
# 帧率就是这么漏出去的，且漏出去后时码与编码帧率会静默漂移。
class TestNoHardcodedSpecValues(unittest.TestCase):
    """规格值只能在 utils.py 定义（spec §5.1）"""

    FORBIDDEN = ("1920", "1080", '"24"', "1001", "1136", "36.0")

    def _pipeline_sources(self):
        import glob
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        out = []
        for path in sorted(glob.glob(os.path.join(here, "*.py"))):
            if os.path.basename(path) == "utils.py":
                continue
            with open(path, encoding="utf-8") as f:
                out.append((os.path.basename(path), f.read().splitlines()))
        return out

    def test_no_spec_literals_outside_utils(self):
        offenders = []
        for fname, lines in self._pipeline_sources():
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                # 注释与文档串不算代码字面量（那里写「1001 起」是人读的说明）
                if stripped.startswith("#"):
                    continue
                for bad in self.FORBIDDEN:
                    if bad in line:
                        offenders.append(f"{fname}:{i}: {bad} → {stripped[:70]}")
        self.assertEqual([], offenders,
                         "规格值硬编码漏网（应改为 utils.XXX）:\n" + "\n".join(offenders))

    def test_utils_still_defines_them(self):
        """反向：不能为了通过上一条把规格值从 utils.py 删掉"""
        self.assertEqual(24, utils.FPS)
        self.assertEqual((1920, 1080), utils.RESOLUTION)
        self.assertEqual(1001, utils.FRAME_START)
        self.assertEqual(36.0, utils.SENSOR_WIDTH)


if __name__ == "__main__":
    # ⚠️ 不能用 unittest.main()：Blender 传进来的是它自己的 argv，
    #    失败用例不会让命令失败。本分支的整个动机就是消灭「静默通过」。
    _suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    _result = unittest.TextTestRunner(verbosity=2).run(_suite)
    sys.exit(0 if _result.wasSuccessful() else 1)
