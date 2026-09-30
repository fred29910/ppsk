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
        """⚠️ 断言必须带单位。只写 `assertIn("36")` 的话，把它改成 12 反而
        仍会通过 —— "12" 是 "1920" 的子串，元测试立刻暴露了这一点。"""
        self.assertIn(f"{int(utils.SENSOR_WIDTH)} mm", bible_text())

    def test_frame_convention(self):
        t = bible_text()
        self.assertIn(str(utils.FRAME_START), t)
        self.assertIn(f"{utils.HANDLE_FRAMES} 帧 handles", t)

    def test_no_stale_blender_version(self):
        """5.2.1 只允许出现在「改为实测的 5.2.0」这类修订记录语境里"""
        self.assertNotIn("5.2.1", bible_body(), "正文里还有 5.2.1 —— 修订记录里的历史引用不算")


class TestTamperIsDetected(unittest.TestCase):
    """元测试：改坏 utils.py 的值后**真实测试**必须变红，否则这些断言是装饰品

    spec §10.3 的要求是「改坏一个值 → 测试变红」。
    之前的版本把断言表达式在原地重抄一遍（`assertIn(str(utils.FPS), bible_text())`），
    并不调用 TestBibleMatchesUtils.test_fps —— 把整个 test_fps 删掉它照样全绿。
    所以这里必须用反射跑真实用例。
    """

    def _run_real(self, case_name, method_name):
        case = TestBibleMatchesUtils(case_name)
        if hasattr(case, "setUp"):
            case.setUp()
        return getattr(case, method_name)()

    def test_fps_test_is_green_before_tampering(self):
        """反向：没改坏时真实用例必须是绿的，否则下面那条「变红」没有意义"""
        self._run_real("test_fps", "test_fps")

    def test_fps_change_breaks_the_real_fps_test(self):
        original = utils.FPS
        try:
            utils.FPS = 48
            with self.assertRaises(AssertionError):
                self._run_real("test_fps", "test_fps")
        finally:
            utils.FPS = original

    def test_resolution_change_breaks_the_real_resolution_test(self):
        original = utils.RESOLUTION
        try:
            utils.RESOLUTION = (1280, 720)
            with self.assertRaises(AssertionError):
                self._run_real("test_resolution", "test_resolution")
        finally:
            utils.RESOLUTION = original

    def test_shutter_change_breaks_the_real_shutter_test(self):
        original = utils.SHUTTER_ANGLE
        try:
            utils.SHUTTER_ANGLE = 360.0
            with self.assertRaises(AssertionError):
                self._run_real(
                    "test_shutter_angle_in_degrees", "test_shutter_angle_in_degrees")
        finally:
            utils.SHUTTER_ANGLE = original

    def test_version_change_breaks_the_real_version_test(self):
        original = utils.BLENDER_VERSION
        try:
            utils.BLENDER_VERSION = "9.9.9"
            with self.assertRaises(AssertionError):
                self._run_real(
                    "test_blender_version_and_hash", "test_blender_version_and_hash")
        finally:
            utils.BLENDER_VERSION = original

    def test_sensor_width_change_breaks_the_real_sensor_test(self):
        original = utils.SENSOR_WIDTH
        try:
            utils.SENSOR_WIDTH = 12.0
            with self.assertRaises(AssertionError):
                self._run_real("test_sensor_width", "test_sensor_width")
        finally:
            utils.SENSOR_WIDTH = original

    def test_view_transform_change_breaks_the_real_color_test(self):
        original = utils.VIEW_TRANSFORM
        try:
            utils.VIEW_TRANSFORM = "Totally Not A View"
            with self.assertRaises(AssertionError):
                self._run_real("test_color_quadruple", "test_color_quadruple")
        finally:
            utils.VIEW_TRANSFORM = original

    def test_frame_start_change_breaks_the_real_frame_test(self):
        original = utils.FRAME_START
        try:
            utils.FRAME_START = 2001
            with self.assertRaises(AssertionError):
                self._run_real("test_frame_convention", "test_frame_convention")
        finally:
            utils.FRAME_START = original


if __name__ == "__main__":
    _suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    _result = unittest.TextTestRunner(verbosity=2).run(_suite)
    sys.exit(0 if _result.wasSuccessful() else 1)
