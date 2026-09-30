import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import utils

BIBLE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "bible", "project_bible.md",
)


def bible_text() -> str:
    with open(BIBLE, encoding="utf-8") as f:
        return f.read()


def bible_body() -> str:
    """只取「## 修订记录」之前的正文。

    修订记录里合法地提到历史版本号（如 5.2.1），拿全文做版本断言会被它喂饱。
    """
    return bible_text().split("## 修订记录")[0]


class TestBibleMatchesUtils(unittest.TestCase):
    """spec §9.1：Bible 人工维护，但数值必须与 utils.py 一致。

    只抓数值，不抓格式 —— 格式漂移不管，这是该方案已知的代价。
    """

    def test_blender_version_and_hash(self):
        t = bible_body()
        self.assertIn(utils.BLENDER_VERSION, t)
        self.assertIn(utils.BLENDER_BUILD_HASH, t)

    def test_resolution(self):
        self.assertIn(f"{utils.RESOLUTION[0]}×{utils.RESOLUTION[1]}", bible_text())

    def test_fps(self):
        self.assertIn(str(utils.FPS), bible_text())

    def test_shutter_angle_in_degrees(self):
        """Bible 记的是人读的度数，不是换算后的帧数"""
        self.assertIn(f"{int(utils.SHUTTER_ANGLE)}°", bible_text())

    def test_shutter_conversion_is_consistent(self):
        """180° 必须对应 0.5 帧 —— 两处都写进 Bible 才不会只改一处"""
        t = bible_text()
        self.assertIn("180°", t)
        self.assertIn("0.5 帧", t)
        self.assertEqual(0.5, utils.shutter_frames())

    def test_color_quadruple(self):
        t = bible_text()
        for v in (utils.VIEW_TRANSFORM, utils.LOOK, utils.DISPLAY_DEVICE):
            self.assertIn(v, t)

    def test_sensor_width(self):
        self.assertIn(str(int(utils.SENSOR_WIDTH)), bible_text())

    def test_frame_convention(self):
        t = bible_text()
        self.assertIn(str(utils.FRAME_START), t)
        self.assertIn(f"{utils.HANDLE_FRAMES} 帧 handles", t)

    def test_no_stale_blender_version(self):
        """5.2.1 只允许出现在「改为实测的 5.2.0」这类修订记录语境里"""
        self.assertNotIn("5.2.1", bible_body(), "正文里还有 5.2.1 —— 修订记录里的历史引用不算")


class TestTamperIsDetected(unittest.TestCase):
    """元测试：改坏 utils.py 的值后主断言必须变红，否则这些断言是装饰品"""

    def test_fps_change_would_break_fps_assertion(self):
        original = utils.FPS
        try:
            utils.FPS = 48
            # 主断言用的是 assertIn(str(utils.FPS), bible_text())，
            # 所以这里必须真的去跑它并断言它抛 AssertionError
            with self.assertRaises(AssertionError):
                self.assertIn(str(utils.FPS), bible_text())
        finally:
            utils.FPS = original
