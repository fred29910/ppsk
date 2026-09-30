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

    def test_light_has_exr_and_named_view_layers(self):
        sc = open_blend(os.path.join(TPL_DIR, "tpl_light_v001.blend"))
        self.assertEqual("OPEN_EXR_MULTILAYER", sc.render.image_settings.file_format)
        # ⚠️ 原断言是 any(name.startswith("VL_")) —— 随便一个空层就绿。
        #    改为断言具体的两个层名，缺一个就是没建出来。
        self.assertEqual(["VL_beauty", "VL_char"],
                         [vl.name for vl in sc.view_layers])
        self.assertTrue(any(o.type == "LIGHT" for o in bpy.data.objects))

    def test_all_view_layers_have_the_same_passes(self):
        """C-1：VL_char 必须是 VL_beauty 的完整数据集，不是 combined 复制品。

        plan §2.2 的双轨雾（Depth + Mist）与 Vector Pass 都靠这些数据 pass。
        """
        sc = open_blend(os.path.join(TPL_DIR, "tpl_light_v001.blend"))
        per_vl = {}
        for vl in sc.view_layers:
            per_vl[vl.name] = sorted(
                p.identifier for p in vl.bl_rna.properties
                if p.identifier.startswith("use_pass_") and getattr(vl, p.identifier)
            )
        self.assertGreaterEqual(len(per_vl), 2, list(per_vl))
        names = list(per_vl)
        for other in names[1:]:
            self.assertEqual(per_vl[names[0]], per_vl[other],
                             f"{names[0]} 与 {other} 的 pass 集合不一致 —— "
                             "setup_passes 没覆盖到所有 view layer")
        # 双轨雾与 Vector 依赖的数据 pass，一个都不能少
        for need in ("use_pass_z", "use_pass_vector", "use_pass_mist",
                     "use_pass_diffuse_color", "use_pass_combined"):
            self.assertIn(need, per_vl[names[0]])

    def test_vl_char_really_excludes_a_collection(self):
        """C-1：排除必须真的可验证。

        原来 light 模板没有 ENV_，`children.get("ENV_")` 返回 None 被
        `if lc is not None` 静默吞掉，VL_char 零排除 —— 两层渲一样的内容。
        """
        sc = open_blend(os.path.join(TPL_DIR, "tpl_light_v001.blend"))
        vl_char = next(vl for vl in sc.view_layers if vl.name == "VL_char")
        excluded = [lc.name for lc in vl_char.layer_collection.children if lc.exclude]
        self.assertTrue(excluded, "VL_char 没有任何 collection 被排除")
        self.assertIn("ENV_", excluded)
        # 排除要在真正渲染时才起作用，所以被排除的层必须还在文件里
        self.assertIn("ENV_", bpy.data.collections)

    def test_anim_has_no_camera(self):
        open_blend(os.path.join(TPL_DIR, "tpl_anim_v001.blend"))
        self.assertFalse([o for o in bpy.data.objects if o.type == "CAMERA"])

    def test_lookdev_has_turntable_grayballs_colorchecker(self):
        open_blend(os.path.join(TPL_DIR, "tpl_lookdev_v001.blend"))
        names = [o.name for o in bpy.data.objects]
        self.assertGreaterEqual(len([n for n in names if "grayball" in n]), 3)
        self.assertTrue(any("colorchecker" in n for n in names), "缺少 ColorChecker 色卡")


class TestObjectsLiveInCollections(unittest.TestCase):
    """I-7：所有对象挂在 scene root 时，collection 骨架形同虚设。

    dls.md §3.2 的分环节工作流与 VL_char 的按 collection 排除都依赖
    对象真的在 collection 里。用 bpy.data.objects 扫描的测试结构上
    发现不了这个问题 —— 必须显式查 users_collection。
    """

    def _objects_by_collection(self):
        out = {}
        for c in bpy.data.collections:
            for o in c.objects:
                out.setdefault(o.name, []).append(c.name)
        return out

    def test_no_object_is_left_in_scene_root(self):
        for name, _ in build_templates.TEMPLATES:
            with self.subTest(template=name):
                sc = open_blend(os.path.join(TPL_DIR, name))
                self.assertEqual([], list(sc.collection.objects),
                                 "有对象挂在 scene root，没进任何 collection")

    def test_every_object_is_in_a_registered_collection(self):
        for name, _ in build_templates.TEMPLATES:
            with self.subTest(template=name):
                open_blend(os.path.join(TPL_DIR, name))
                for obj_name, colls in self._objects_by_collection().items():
                    self.assertTrue(
                        any(c in build_templates.COLLECTIONS for c in colls),
                        f"{obj_name} 在 {colls}，都不在 COLLECTIONS 登记册里")

    def test_layout_camera_and_guides_are_in_collections(self):
        sc = open_blend(os.path.join(TPL_DIR, "tpl_layout_v001.blend"))
        by_coll = self._objects_by_collection()
        self.assertIn("CAM_cam", by_coll)
        for obj_name in ("CAM_cam", "GEO_guide_vertical"):
            self.assertTrue(
                any(c in build_templates.COLLECTIONS for c in by_coll[obj_name]),
                f"{obj_name} 不属于任何 CHR_/ENV_/PRP_/GUIDE_ collection")
        self.assertIn("GUIDE_", by_coll["CAM_cam"])

    def test_lookdev_has_collections(self):
        """lookdev 原来一个 collection 都没有"""
        open_blend(os.path.join(TPL_DIR, "tpl_lookdev_v001.blend"))
        for c in build_templates.STAGE_COLLECTIONS["lookdev"]:
            self.assertIn(c, bpy.data.collections)
        self.assertTrue(build_templates.STAGE_COLLECTIONS["lookdev"])

    def test_stage_collection_prefixes_are_registered(self):
        """COLLECTIONS 从前是死常量。现在它约束 STAGE_COLLECTIONS。"""
        for kind, names in build_templates.STAGE_COLLECTIONS.items():
            for n in names:
                self.assertIn(n, build_templates.COLLECTIONS,
                              f"{kind} 用了未登记的前缀 {n}")

    def test_light_template_has_env_collection_to_exclude(self):
        """C-1 前置：没有 ENV_ 就没什么可排除的"""
        open_blend(os.path.join(TPL_DIR, "tpl_light_v001.blend"))
        self.assertIn("ENV_", bpy.data.collections)

    def test_cfx_cloth_is_nested_under_chr(self):
        open_blend(os.path.join(TPL_DIR, "tpl_cfx_v001.blend"))
        cloth = bpy.data.collections.get("CHR_cloth")
        self.assertIsNotNone(cloth, "缺少 CHR_cloth 工作区")
        parents = [c.name for c in bpy.data.collections if cloth.name in c.children]
        self.assertIn("CHR_", parents,
                      f"CHR_cloth 应嵌在 CHR_ 下，实际父级 {parents}")


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

    def test_apply_preset_failure_stops_build(self):
        """apply_preset 失败时不得存盘、不得记为 written、build 必须返回 ok=False"""
        from unittest import mock
        root = tmp_root()
        tpl_dir = os.path.join(root, "00_project", "templates")
        bad = {"ok": False, "error": "View Transform 未生效", "hint": "检查 OCIO 配置"}
        with mock.patch.object(build_templates.shot, "apply_preset", return_value=bad):
            r = build_templates.build(root, apply=True, overwrite=False)
        self.assertFalse(r["ok"])
        self.assertNotIn("tpl_layout_v001.blend", r.get("written", []))
        self.assertFalse(os.path.exists(os.path.join(tpl_dir, "tpl_layout_v001.blend")))


if __name__ == "__main__":
    _suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    _result = unittest.TextTestRunner(verbosity=2).run(_suite)
    sys.exit(0 if _result.wasSuccessful() else 1)
