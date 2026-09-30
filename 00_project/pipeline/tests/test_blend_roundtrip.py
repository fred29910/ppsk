import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    import bpy
except ImportError:  # 纯 Python 环境（系统 python3）没有 bpy，整模块跳过
    raise unittest.SkipTest("需要 bpy，请在 Blender 内运行")
import utils
import build_templates

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
TPL_DIR = os.path.join(ROOT, "00_project", "templates")


def open_blend(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    return bpy.context.scene


def tmp_root():
    root = tempfile.mkdtemp()
    os.makedirs(os.path.join(root, "00_project", "templates"))
    return root


class TestTemplatesExist(unittest.TestCase):
    def test_six_templates_present(self):
        for name, _ in build_templates.TEMPLATES:
            self.assertTrue(os.path.exists(os.path.join(TPL_DIR, name)), name)

    def test_templates_count_is_six(self):
        self.assertEqual(6, len(build_templates.TEMPLATES))


class TestSharedSettings(unittest.TestCase):
    """spec §10.2：每个模板重开后都要满足的规格项"""

    def test_all_templates_carry_shared_settings(self):
        for name, _ in build_templates.TEMPLATES:
            with self.subTest(template=name):
                sc = open_blend(os.path.join(TPL_DIR, name))
                self.assertEqual(list(utils.RESOLUTION),
                                 [sc.render.resolution_x, sc.render.resolution_y])
                self.assertEqual(utils.FPS, sc.render.fps)
                self.assertEqual("METRIC", sc.unit_settings.system)
                self.assertEqual("BLENDER_EEVEE", sc.render.engine)
                self.assertEqual(utils.VIEW_TRANSFORM, sc.view_settings.view_transform)
                self.assertEqual(utils.LOOK, sc.view_settings.look)
                self.assertEqual(utils.DISPLAY_DEVICE, sc.display_settings.display_device)
                # ⚠️ 全仓库从未被执行过的断言
                self.assertAlmostEqual(0.5, sc.render.motion_blur_shutter, places=5)
                self.assertEqual(utils.FRAME_START, sc.frame_start)


class TestStageSpecific(unittest.TestCase):
    def test_layout_has_camera_and_guides(self):
        open_blend(os.path.join(TPL_DIR, "tpl_layout_v001.blend"))
        self.assertTrue(any(o.type == "CAMERA" for o in bpy.data.objects))
        self.assertIn("GUIDE_", bpy.data.collections)

    def test_guides_never_render(self):
        """9:16 参考线只在 Layout 阶段可见，绝不能进渲染（spec §7.3）"""
        open_blend(os.path.join(TPL_DIR, "tpl_layout_v001.blend"))
        guides = [o for o in bpy.data.objects if "guide" in o.name.lower()]
        self.assertTrue(guides, "缺少 9:16 参考线对象")
        for g in guides:
            self.assertTrue(g.hide_render, f"{g.name} 的 hide_render 必须为 True")

    def test_camera_defaults(self):
        open_blend(os.path.join(TPL_DIR, "tpl_layout_v001.blend"))
        cam_obj = [o for o in bpy.data.objects if o.type == "CAMERA"][0]
        self.assertEqual("CAM_cam", cam_obj.name)
        self.assertEqual(utils.SENSOR_WIDTH, cam_obj.data.sensor_width)
        self.assertEqual(35.0, cam_obj.data.lens)      # 占位值，逐镜由镜头表覆盖
        self.assertEqual(0.0, cam_obj.data.shift_x)    # 9:16 靠安全框 + 后期裁切
        self.assertEqual(0.0, cam_obj.data.shift_y)

    def test_light_has_exr_and_view_layers(self):
        sc = open_blend(os.path.join(TPL_DIR, "tpl_light_v001.blend"))
        self.assertEqual("OPEN_EXR_MULTILAYER", sc.render.image_settings.file_format)
        self.assertTrue(any(vl.name.startswith("VL_") for vl in sc.view_layers))
        self.assertTrue(any(o.type == "LIGHT" for o in bpy.data.objects))

    def test_anim_has_no_camera(self):
        open_blend(os.path.join(TPL_DIR, "tpl_anim_v001.blend"))
        self.assertFalse([o for o in bpy.data.objects if o.type == "CAMERA"])

    def test_lookdev_has_turntable_grayballs_colorchecker(self):
        open_blend(os.path.join(TPL_DIR, "tpl_lookdev_v001.blend"))
        names = [o.name for o in bpy.data.objects]
        self.assertGreaterEqual(len([n for n in names if "grayball" in n]), 3)
        self.assertTrue(any("colorchecker" in n for n in names), "缺少 ColorChecker 色卡")


class TestBuildBehavior(unittest.TestCase):
    def test_missing_hdri_is_warning_not_fake(self):
        """Review Focus #5：HDRI 缺失要警告，不伪造纯色环境"""
        r = build_templates.build(tmp_root(), apply=True, overwrite=False)
        self.assertTrue(r["ok"], r)
        self.assertTrue(any("HDRI" in w for w in r["warnings"]),
                        f"HDRI 缺失未进 warnings: {r['warnings']}")

    def test_wrong_project_root_errors_without_writing(self):
        """Review Focus #2：无 00_project/ 的目录必须拒绝且不建任何东西"""
        empty = tempfile.mkdtemp()
        r = build_templates.build(empty, apply=True, overwrite=False)
        self.assertFalse(r["ok"])
        self.assertIn("00_project", r["hint"])
        self.assertEqual([], os.listdir(empty))

    def test_dry_run_does_not_touch_disk(self):
        """Review Focus #4：用 mtime 验证，不信返回值"""
        root = tmp_root()
        r = build_templates.build(root, apply=False, overwrite=False)
        self.assertTrue(r["ok"])
        self.assertEqual(6, len(r["written"]))       # 报告说要写
        self.assertEqual([], os.listdir(os.path.join(root, "00_project", "templates")))

    def test_existing_file_is_skipped_without_overwrite(self):
        """Review Focus #1：GUI 里的手工修改不能被吃掉"""
        root = tmp_root()
        target = os.path.join(root, "00_project", "templates", "tpl_anim_v001.blend")
        with open(target, "wb") as f:
            f.write(b"hand edited in gui")
        r = build_templates.build(root, apply=True, overwrite=False)
        self.assertIn("tpl_anim_v001.blend", r["skipped"])
        with open(target, "rb") as f:
            self.assertEqual(b"hand edited in gui", f.read())

    def test_overwrite_flag_actually_rewrites(self):
        """反向：显式 --overwrite 必须真的写，否则保护逻辑是死代码"""
        root = tmp_root()
        target = os.path.join(root, "00_project", "templates", "tpl_anim_v001.blend")
        with open(target, "wb") as f:
            f.write(b"hand edited in gui")
        r = build_templates.build(root, apply=True, overwrite=True)
        self.assertIn("tpl_anim_v001.blend", r["written"])
        with open(target, "rb") as f:
            self.assertNotEqual(b"hand edited in gui", f.read())


if __name__ == "__main__":
    _suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    _result = unittest.TextTestRunner(verbosity=2).run(_suite)
    sys.exit(0 if _result.wasSuccessful() else 1)
