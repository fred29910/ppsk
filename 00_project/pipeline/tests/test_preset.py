import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    import bpy
except ImportError:  # 纯 Python 环境（系统 python3）没有 bpy，整模块跳过
    raise unittest.SkipTest("需要 bpy，请在 Blender 内运行")
import utils
import shot


def fresh_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


class TestVersionCheck(unittest.TestCase):
    def test_hash_mismatch_is_warning_not_failure(self):
        """本机 dev build 与官方发行版 hash 必然不同 —— 只能警告。

        ⚠️ monkeypatch 记录常量来制造不符，而不是依赖本机 hash 恰好不同：
        后者在 hash 相同的机器上恒真，这条规则就一次都没被执行过。
        """
        from unittest import mock
        with mock.patch.object(utils, "BLENDER_BUILD_HASH", "ffffffffffff"):
            r = utils.check_blender_version(strict=False)
        self.assertTrue(r["ok"], r)
        self.assertTrue(any("build hash" in w for w in r.get("warnings", [])),
                        f"hash 不符未进 warnings: {r.get('warnings')}")

    def test_version_prefix_mismatch_fails(self):
        from unittest import mock
        with mock.patch.object(utils, "REQUIRED_VERSION_PREFIX", "9.9"):
            r = utils.check_blender_version(strict=False)
        self.assertFalse(r["ok"], "版本前缀不符却返回 ok=True")

    def test_strict_mismatch_raises_system_exit(self):
        """spec §10.4：版本号前两段 ≠ 5.2 → 退出码非 0"""
        from unittest import mock
        with mock.patch.object(utils, "REQUIRED_VERSION_PREFIX", "9.9"):
            with self.assertRaises(SystemExit):
                utils.check_blender_version(strict=True)


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

    def test_exr_multilayer_and_template_frame_range(self):
        ims = self.scene.render.image_settings
        self.assertEqual("MULTI_LAYER_IMAGE", ims.media_type)
        self.assertEqual("OPEN_EXR_MULTILAYER", ims.file_format)
        # ⚠️ 只在 frame_start/frame_end 都为 None 时才是占位范围。
        #    这个 17 帧值是**模板占位**，不是任何真实镜头的范围。
        self.assertEqual(utils.FRAME_START, self.scene.frame_start)
        self.assertEqual(utils.FRAME_START + 2 * utils.HANDLE_FRAMES, self.scene.frame_end)
        self.assertEqual(utils.FRAME_START + utils.HANDLE_FRAMES, self.scene.frame_current)

    def test_output_uses_hash_placeholder(self):
        """⚠️ %04d 会产出双扩展名（g0 报告 §6.6）"""
        self.assertIn("####", self.scene.render.filepath)
        self.assertNotIn("%04d", self.scene.render.filepath)

    def test_engine_is_eevee_by_default(self):
        self.assertEqual("BLENDER_EEVEE", self.scene.render.engine)

    def test_passes_apply_to_every_view_layer(self):
        """⚠️ C-1：只设 view_layers[0] 会让 VL_char 只剩 combined，
        z / vector / mist / diffuse_color 全缺 —— 渲出来是残缺数据集。"""
        sc = fresh_scene()
        sc.view_layers.new("VL_char")
        r = shot.setup_passes(sc)
        self.assertTrue(r["ok"], r)
        for vl in sc.view_layers:
            self.assertTrue(vl.use_pass_z, f"{vl.name} 缺 z")
            self.assertTrue(vl.use_pass_vector, f"{vl.name} 缺 vector")
            self.assertTrue(vl.use_pass_mist, f"{vl.name} 缺 mist")
            self.assertTrue(vl.use_pass_diffuse_color, f"{vl.name} 缺 diffuse_color")
            self.assertTrue(vl.use_pass_combined, f"{vl.name} 缺 combined")
        self.assertEqual(len(sc.view_layers), len(r["per_layer"]))


class TestFrameRangeIsNotFaked(unittest.TestCase):
    """C-2：帧范围是 per-shot 数据（shotlist.csv），不是模板占位常量。"""

    def test_explicit_frame_end_wins(self):
        sc = fresh_scene()
        r = shot.apply_preset(sc, shot="seq010_sh010", stage="light",
                              project_root="/tmp/opencode",
                              frame_start=1001, frame_end=1160)
        self.assertTrue(r["ok"], r)
        self.assertEqual(1001, sc.frame_start)
        self.assertEqual(1160, sc.frame_end)

    def test_explicit_frame_end_different_from_placeholder(self):
        """反向：占位值是 1017，若这条不成立说明传参根本没生效"""
        sc = fresh_scene()
        shot.apply_preset(sc, shot="seq010_sh010", stage="light",
                          project_root="/tmp/opencode",
                          frame_start=1001, frame_end=1160)
        self.assertNotEqual(utils.FRAME_START + 2 * utils.HANDLE_FRAMES, sc.frame_end)

    def test_both_none_uses_placeholder(self):
        """模板路径：两个参数都为 None 时才落到占位值"""
        sc = fresh_scene()
        shot.apply_preset(sc, shot="tpl_layout", stage="light", project_root="/tmp/opencode")
        self.assertEqual(utils.FRAME_START + 2 * utils.HANDLE_FRAMES, sc.frame_end)

    def test_frame_current_stays_in_range(self):
        """frame_current 不能落在 [start, end] 之外（Blender 会静默接受）"""
        sc = fresh_scene()
        shot.apply_preset(sc, shot="seq010_sh010", stage="light",
                          project_root="/tmp/opencode",
                          frame_start=1001, frame_end=1010)
        self.assertTrue(sc.frame_start <= sc.frame_current <= sc.frame_end,
                        f"{sc.frame_current} 不在 [{sc.frame_start}, {sc.frame_end}]")

    def test_inverted_range_rejected(self):
        sc = fresh_scene()
        r = shot.apply_preset(sc, shot="seq010_sh010", stage="light",
                              project_root="/tmp/opencode",
                              frame_start=1160, frame_end=1001)
        self.assertFalse(r["ok"], r)


class TestVersionGateIsWired(unittest.TestCase):
    """I-3：check_blender_version 原来只有测试调它，apply_preset 不调。"""

    def test_apply_preset_rejects_wrong_version(self):
        from unittest import mock
        sc = fresh_scene()
        with mock.patch.object(utils, "REQUIRED_VERSION_PREFIX", "9.9"):
            r = shot.apply_preset(sc, shot="seq010_sh010", stage="light",
                                  project_root="/tmp/opencode")
        self.assertFalse(r["ok"], "版本不符却返回 ok=True")
        self.assertIn("版本", r["error"])

    def test_wrong_version_leaves_scene_untouched(self):
        """不符时不得已写入任何设置 —— 否则「失败」也留下了半改过的场景"""
        from unittest import mock
        sc = fresh_scene()
        sc.render.resolution_x = 640
        sc.render.resolution_y = 360
        with mock.patch.object(utils, "REQUIRED_VERSION_PREFIX", "9.9"):
            shot.apply_preset(sc, shot="seq010_sh010", stage="light",
                              project_root="/tmp/opencode")
        self.assertEqual(640, sc.render.resolution_x)
        self.assertEqual(360, sc.render.resolution_y)

    def test_hash_mismatch_only_warns_through_apply_preset(self):
        """「hash 不符只警告」这条规则必须真的被执行过一次，
        否则它只是一句没人跑过的约定（原测试因本机 hash 恰好相同而恒真）。"""
        from unittest import mock
        sc = fresh_scene()
        with mock.patch.object(utils, "BLENDER_BUILD_HASH", "ffffffffffff"):
            r = shot.apply_preset(sc, shot="seq010_sh010", stage="light",
                                  project_root="/tmp/opencode")
        self.assertTrue(r["ok"], r)
        self.assertTrue(any("build hash" in w for w in r.get("warnings", [])),
                        f"warnings 未带上 hash 不符: {r.get('warnings')}")


class TestSetupRenderInBlender(unittest.TestCase):
    """I-8：setup_render 真正改 scene 的那条路（test_shot_api.py 覆盖不到）"""

    def test_view_transform_is_applied_to_scene(self):
        sc = fresh_scene()
        r = shot.setup_render("seq010_sh020", "light",
                              view_transform="Khronos PBR Neutral",
                              frame_start=1001, frame_end=1136,
                              project_root="/tmp/opencode")
        self.assertTrue(r["ok"], r)
        self.assertEqual("Khronos PBR Neutral", sc.view_settings.view_transform)

    def test_frame_range_reaches_scene_through_setup_render(self):
        """C-2 端到端：1170 不是占位的 1017"""
        sc = fresh_scene()
        r = shot.setup_render("seq010_sh010", "light", frame_start=1001,
                              frame_end=1160, project_root="/tmp/opencode")
        self.assertTrue(r["ok"], r)
        self.assertEqual(1001, sc.frame_start)
        self.assertEqual(1160, sc.frame_end)

    def test_missing_frame_range_leaves_scene_untouched(self):
        sc = fresh_scene()
        before = (sc.frame_start, sc.frame_end, sc.render.resolution_x)
        r = shot.setup_render("seq010_sh010", "light", project_root="/tmp/opencode")
        self.assertFalse(r["ok"], r)
        self.assertEqual(before, (sc.frame_start, sc.frame_end, sc.render.resolution_x))

    def test_output_path_uses_shot_and_stage(self):
        sc = fresh_scene()
        shot.setup_render("seq010_sh010", "light", frame_start=1001, frame_end=1160,
                          project_root="/tmp/opencode")
        self.assertIn(os.path.join("seq010_sh010", "render", "light", "v001"),
                      sc.render.filepath)
        self.assertIn("####", sc.render.filepath)


if __name__ == "__main__":
    _suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    _result = unittest.TextTestRunner(verbosity=2).run(_suite)
    sys.exit(0 if _result.wasSuccessful() else 1)
