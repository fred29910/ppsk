"""生成 6 个环节模板 .blend。需要 bpy。

渲染设置全部走 shot.apply_preset()，不自己重设一遍。
绝不覆盖已存在的 .blend（除非显式 --overwrite）：模板会被人在 GUI 里改，
生成器不能默默吃掉手工工作。
"""

import argparse
import math
import os
import sys

# Blender 以 --python 运行时不会把脚本目录加入 sys.path，
# 同目录的 utils / shot 就 import 不到。手动补上。
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import bpy
import utils
import shot

COLLECTIONS = ("CHR_", "ENV_", "PRP_", "FX_", "LGT_", "GUIDE_")

TEMPLATES = (
    ("tpl_layout_v001.blend",   "layout"),
    ("tpl_anim_v001.blend",     "anim"),
    ("tpl_cfx_v001.blend",      "cfx"),
    ("tpl_fx_v001.blend",       "fx"),
    ("tpl_light_v001.blend",    "light"),
    ("tpl_lookdev_v001.blend",  "lookdev"),
)

# 每个模板建哪些 collection
STAGE_COLLECTIONS = {
    "layout":  ("CHR_", "ENV_", "PRP_", "GUIDE_"),
    "anim":    ("CHR_",),
    "cfx":     ("CHR_",),
    "fx":      ("FX_",),
    "light":   ("LGT_",),
    "lookdev": (),
}

# X-Rite ColorChecker Classic 24 色（sRGB 0-255 近似）
_COLORCHECKER_SRGB = (
    (115, 82, 68), (194, 150, 130), (98, 122, 157), (87, 108, 67),
    (133, 128, 177), (103, 189, 170), (214, 126, 44), (80, 91, 166),
    (193, 90, 99), (94, 60, 108), (157, 188, 64), (224, 163, 46),
    (56, 61, 150), (70, 148, 73), (175, 54, 60), (231, 199, 31),
    (187, 86, 149), (8, 133, 161), (243, 243, 242), (200, 200, 200),
    (160, 160, 160), (122, 122, 122), (85, 85, 85), (52, 52, 52),
)


def _new_collection(scene, name):
    coll = bpy.data.collections.new(name)
    scene.collection.children.link(coll)
    return coll


def _add_camera(name, location=(0.0, 0.0, 0.0), rotation=(0.0, 0.0, 0.0)):
    """占位相机：sensor 全片统一，35mm 占位焦距，逐镜由镜头表覆盖。"""
    cam_data = bpy.data.cameras.new(name)
    cam_data.sensor_width = utils.SENSOR_WIDTH
    cam_data.sensor_fit = "AUTO"
    cam_data.lens = 35.0        # 占位值，逐镜由镜头表覆盖
    cam_data.shift_x = 0.0      # 9:16 靠安全框 + 后期裁切
    cam_data.shift_y = 0.0
    cam_data.clip_start = 0.1
    cam_data.clip_end = 1000.0
    cam_obj = bpy.data.objects.new(name, cam_data)
    cam_obj.location = location
    cam_obj.rotation_euler = rotation
    return cam_obj


def _principled(mat):
    return next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def _uv_sphere_mesh(name, radius=1.0, segments=32, rings=16):
    """手动建 UV sphere mesh，不依赖 ops context（-b 模式下更稳）。"""
    verts, faces = [], []
    for r in range(rings + 1):
        phi = math.pi * r / rings
        for s in range(segments):
            theta = 2.0 * math.pi * s / segments
            verts.append((radius * math.sin(phi) * math.cos(theta),
                          radius * math.sin(phi) * math.sin(theta),
                          radius * math.cos(phi)))
    for r in range(rings):
        for s in range(segments):
            a = r * segments + s
            b = r * segments + (s + 1) % segments
            c = (r + 1) * segments + (s + 1) % segments
            d = (r + 1) * segments + s
            faces.append((a, b, c, d))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    return mesh


def _populate(scene, kind):
    """按环节补内容（对象类）。渲染设置不在这里碰，一律交给 apply_preset。"""
    if kind == "layout":
        cam = _add_camera(utils.make_object_name("CAM", "cam"))
        scene.collection.objects.link(cam)
        guides = bpy.data.collections.get("GUIDE_")
        for label in ("vertical", "horizontal"):
            obj = bpy.data.objects.new(
                utils.make_object_name("GEO", f"guide_{label}"), None)
            # ⚠️ Blender 5.2 的 empty_display_type 无 "WIRE"（实测 enum 仅
            # PLAIN_AXES/ARROWS/SINGLE_ARROW/CIRCLE/CUBE/SPHERE/CONE/IMAGE），
            # 用 PLAIN_AXES 占位；参考线靠 hide_render=True 保证不进渲染
            obj.empty_display_type = "PLAIN_AXES"
            obj.hide_render = True      # 9:16 参考线绝不能进渲染（spec §7.3）
            guides.objects.link(obj)
    elif kind == "cfx":
        # 空 collection 标记布料工作区
        _new_collection(scene, utils.make_object_name("CHR", "cloth"))
    elif kind == "lookdev":
        _add_lookdev_extras(scene)
    # anim / fx：不加对象


def _add_lookdev_extras(scene):
    # 转台 empty，相机 parent 上去
    turntable = bpy.data.objects.new(
        utils.make_object_name("GEO", "turntable"), None)
    turntable.empty_display_type = "PLAIN_AXES"
    scene.collection.objects.link(turntable)

    cam = _add_camera(utils.make_object_name("CAM", "cam"),
                      location=(0.0, -7.0, 1.6),
                      rotation=(1.5707963, 0.0, 0.0))
    scene.collection.objects.link(cam)
    cam.parent = turntable

    # 3 个灰球：roughness 0.2 / 0.5 / 0.9
    for i, rough in enumerate((0.2, 0.5, 0.9)):
        name = utils.make_object_name("GEO", f"grayball_rough{rough}")
        ball = bpy.data.objects.new(name, _uv_sphere_mesh(name))
        ball.location = ((i - 1) * 2.4, 0.0, 1.0)
        scene.collection.objects.link(ball)
        mat = bpy.data.materials.new(f"MAT_{name}")
        mat.use_nodes = True
        bsdf = _principled(mat)
        bsdf.inputs["Base Color"].default_value = (0.5, 0.5, 0.5, 1.0)
        bsdf.inputs["Roughness"].default_value = rough
        ball.data.materials.append(mat)

    # ColorChecker 24 色卡：1 个 mesh，24 面 24 材质
    name = utils.make_object_name("GEO", "colorchecker")
    w, h = 0.07, 0.05
    verts, faces = [], []
    for i in range(24):
        col, row = i % 6, i // 6
        x0, y0 = col * w, row * h
        b = len(verts)
        verts.extend([(x0, y0, 0.0), (x0 + w, y0, 0.0),
                      (x0 + w, y0 + h, 0.0), (x0, y0 + h, 0.0)])
        faces.append((b, b + 1, b + 2, b + 3))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    card = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(card)
    for i, (r, g, b) in enumerate(_COLORCHECKER_SRGB):
        mat = bpy.data.materials.new(f"MAT_cc_{i:02d}")
        mat.use_nodes = True
        bsdf = _principled(mat)
        bsdf.inputs["Base Color"].default_value = (
            r / 255.0, g / 255.0, b / 255.0, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.6
        mesh.materials.append(mat)
        mesh.polygons[i].material_index = i
    card.location = (0.0, 1.2, 0.005)


def _setup_light_view_layers(scene):
    """light 模板：apply_preset 之后建 VL_beauty / VL_char（排除 ENV_）+ 占位灯。"""
    scene.view_layers[0].name = "VL_beauty"
    vl_char = scene.view_layers.new("VL_char")
    lc = vl_char.layer_collection.children.get("ENV_")
    if lc is not None:
        lc.exclude = True

    key = bpy.data.lights.new(utils.make_object_name("LGT", "key"), type="AREA")
    key.energy = 800.0
    key.size = 3.0
    key_obj = bpy.data.objects.new(key.name, key)
    key_obj.location = (3.0, -3.0, 4.0)
    scene.collection.objects.link(key_obj)


def _hdri_installed(project_root):
    hdri_dir = os.path.join(project_root, "05_assets", "lib", "hdri")
    if not os.path.isdir(hdri_dir):
        return False
    return any(f.lower().endswith((".hdr", ".exr")) for f in os.listdir(hdri_dir))


def build(project_root, apply=False, overwrite=False):
    """生成（或只报告）6 个环节模板。返回 {"ok", "written", "skipped", "warnings"}。

    apply=False：只报告计划，不写盘。
    apply=True：写盘；已存在的 .blend 默认跳过，overwrite=True 才覆盖。
    """
    project_root = os.path.abspath(project_root)
    if not os.path.isdir(os.path.join(project_root, "00_project")):
        return {
            "ok": False,
            "error": "project root 缺少 00_project/",
            "hint": "用 --project-root 指向工程根目录（含 00_project/），不是它的子目录",
        }

    if not apply:
        return {
            "ok": True,
            "written": [name for name, _ in TEMPLATES],
            "skipped": [],
            "warnings": [],
        }

    warnings = []
    if not _hdri_installed(project_root):
        warnings.append(
            "HDRI 未安装：05_assets/lib/hdri/ 无 .hdr/.exr，"
            "LookDev 模板只留 World 槽位，不伪造纯色环境"
        )

    tpl_dir = os.path.join(project_root, "00_project", "templates")
    os.makedirs(tpl_dir, exist_ok=True)

    written, skipped = [], []
    for name, kind in TEMPLATES:
        path = os.path.join(tpl_dir, name)
        if os.path.exists(path) and not overwrite:
            skipped.append(name)
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        scene = bpy.context.scene
        for coll_name in STAGE_COLLECTIONS[kind]:
            _new_collection(scene, coll_name)
        _populate(scene, kind)
        r = shot.apply_preset(scene, shot=name[:-len(".blend")], stage="light",
                              project_root=project_root)
        if not r.get("ok"):
            return {"ok": False,
                    "error": f"模板 {name} 渲染设置失败: {r.get('error')}",
                    "hint": r.get("hint"),
                    "written": written, "skipped": skipped, "warnings": warnings}
        if kind == "light":
            _setup_light_view_layers(scene)
        bpy.ops.wm.save_as_mainfile(filepath=path)
        written.append(name)

    return {"ok": True, "written": written, "skipped": skipped, "warnings": warnings}


def _argv():
    """只取 `--` 之后的参数（同 shot.py）。"""
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def main(argv=None):
    if argv is None:
        argv = _argv()
    p = argparse.ArgumentParser(prog="build_templates.py")
    p.add_argument("--project-root", default=".",
                   help="工程根目录（含 00_project/）")
    p.add_argument("--apply", action="store_true",
                   help="实际写盘（默认只报告计划）")
    p.add_argument("--overwrite", action="store_true",
                   help="覆盖已存在的 .blend（默认跳过，保护 GUI 里的手工修改）")
    a = p.parse_args(argv)
    r = build(a.project_root, apply=a.apply, overwrite=a.overwrite)
    print(r)
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
