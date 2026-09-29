import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bpy
import utils
import shot


def fresh_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


class TestVersionCheck(unittest.TestCase):
    def test_hash_mismatch_is_warning_not_failure(self):
        """本机 dev build 与官方发行版 hash 必然不同 —— 只能警告"""
        r = utils.check_blender_version.__wrapped__() if hasattr(utils.check_blender_version, "__wrapped__") \
            else utils.check_blender_version(strict=False)
        self.assertTrue(r["ok"], r)
        self.assertIsInstance(r.get("warnings", []), list)


class TestApplyPreset(unittest.TestCase):
    def setUp(self):
        self.scene = fresh_scene()
        self.r = shot.apply_preset(self.scene, shot="seq010_sh010", stage="light",
                                   project_root="/tmp/opencode")

    def test_resolution_and_fps(self):
        self.assertEqual(list(utils.RESOLUTION),
                         [self.scene.render.resolution_x, self.scene.render.resolution_y])
        self.assertEqual(utils.FPS, self.scene.render.fps)

    def test_units_are_metric(self):
        """Bible 锁定公制 1u=1m，模板与实际渲染都要靠这一条"""
        self.assertEqual("METRIC", self.scene.unit_settings.system)
        self.assertEqual(1.0, self.scene.unit_settings.scale_length)

    def test_shutter_is_frames_not_degrees(self):
        """⚠️ Review Focus：直接写 180.0 会被当成 180 帧"""
        self.assertAlmostEqual(0.5, self.scene.render.motion_blur_shutter, places=5)
        self.assertNotAlmostEqual(utils.SHUTTER_ANGLE, self.scene.render.motion_blur_shutter)

    def test_motion_blur_off_vector_on(self):
        """D7：二者互斥，选 Vector"""
        self.assertFalse(self.scene.render.use_motion_blur)
        self.assertTrue(self.scene.view_layers[0].use_pass_vector)

    def test_color_readback(self):
        vs, ds = self.scene.view_settings, self.scene.display_settings
        self.assertEqual(utils.VIEW_TRANSFORM, vs.view_transform)
        self.assertEqual(utils.LOOK, vs.look)
        self.assertEqual(utils.DISPLAY_DEVICE, ds.display_device)

    def test_per_shot_view_transform(self):
        """G0-T4：关键 FX 镜头换 Khronos PBR Neutral（spec D9）"""
        sc = fresh_scene()
        shot.apply_preset(sc, shot="seq010_sh020", stage="light",
                          view_transform="Khronos PBR Neutral", project_root="/tmp/opencode")
        self.assertEqual("Khronos PBR Neutral", sc.view_settings.view_transform)

    def test_exr_multilayer_and_frame_range(self):
        ims = self.scene.render.image_settings
        self.assertEqual("MULTI_LAYER_IMAGE", ims.media_type)
        self.assertEqual("OPEN_EXR_MULTILAYER", ims.file_format)
        # 帧范围：1001 起 + 8 帧 handles
        self.assertEqual(utils.FRAME_START, self.scene.frame_start)
        self.assertEqual(utils.FRAME_START + 2 * utils.HANDLE_FRAMES, self.scene.frame_end)
        self.assertEqual(utils.FRAME_START + utils.HANDLE_FRAMES, self.scene.frame_current)

    def test_output_uses_hash_placeholder(self):
        """⚠️ %04d 会产出双扩展名（g0 报告 §6.6）"""
        self.assertIn("####", self.scene.render.filepath)
        self.assertNotIn("%04d", self.scene.render.filepath)

    def test_engine_is_eevee_by_default(self):
        self.assertEqual("BLENDER_EEVEE", self.scene.render.engine)


if __name__ == "__main__":
    _suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    _result = unittest.TextTestRunner(verbosity=2).run(_suite)
    sys.exit(0 if _result.wasSuccessful() else 1)
