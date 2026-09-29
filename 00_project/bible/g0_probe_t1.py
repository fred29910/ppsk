"""
G0-T1 探针：验证 EEVEE 体积雾是否真的参与渲染

⚠️ 第一版探针的测量方法是错的，勿回退。
   旧方法：太阳正对镜头，比较"有雾/无雾"的 Combined mean。
   失败原因：基线已过曝（mean≈0.72, max≈2.34，画面饱和），
             雾的散射贡献被淹没；同时雾盒遮挡直射光使 max 反而下降。
             结论错误地判为"体积无贡献"。

   正确方法（decisive）：场景中不放任何几何体，唯一的像素来源就是雾本身。
   这样雾的贡献无法被其他光遮蔽。

用法：
    blender -b --factory-startup --python g0_probe_t1.py -- --out <目录> [--res 320 180]

判读：DIFF mean > 1e-4 → 体积正常工作（T1 通过）
"""

import os
import sys
import time

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "/tmp/g0_t1"
RES = (int(argv[1]), int(argv[2])) if len(argv) >= 3 else (320, 180)


def build(use_volume: bool):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene

    # 5.2 的引擎 ID 是 BLENDER_EEVEE；-b 无界面模式下枚举里只有它，
    # Cycles 需直接赋值（见 g0_probe_engines.py）
    sc.render.engine = "BLENDER_EEVEE"

    ev = sc.eevee
    ev.use_raytracing = True
    if hasattr(ev, "use_volume_custom_range"):
        ev.use_volume_custom_range = True
    ev.volumetric_start = 0.1
    ev.volumetric_end = 60.0
    ev.volumetric_samples = 96
    ev.volumetric_tile_size = "2"

    r = sc.render
    r.resolution_x, r.resolution_y = RES
    r.image_settings.media_type = "IMAGE"
    r.image_settings.file_format = "OPEN_EXR"
    r.image_settings.color_depth = "32"
    r.filepath = f"{OUT}/t1_"

    # 唯一光源。场景中不放地面/物体，避免遮挡干扰。
    l = bpy.data.lights.new("LGT_Sun", "SUN")
    lo = bpy.data.objects.new("LGT_Sun", l)
    sc.collection.objects.link(lo)
    lo.location = (0, -10, 3)
    lo.rotation_euler = (1.3, 0, 0)
    l.energy = 10

    if use_volume:
        m = bpy.data.materials.new("M_Fog")
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        vp = nt.nodes.new("ShaderNodeVolumePrincipled")
        vp.inputs["Color"].default_value = (0.9, 0.92, 0.95, 1)
        vp.inputs["Density"].default_value = 0.25
        nt.links.new(vp.outputs["Volume"], out.inputs["Volume"])
        # 雾盒完全在画面内，且不包含相机
        bpy.ops.mesh.primitive_cube_add(size=10, location=(0, -3, 2))
        bpy.context.object.data.materials.append(m)

    c = bpy.data.cameras.new("CAM_Test")
    o = bpy.data.objects.new("CAM_Test", c)
    sc.collection.objects.link(o)
    o.location = (0, -14, 1.8)
    o.rotation_euler = (1.35, 0, 0)
    sc.camera = o
    c.lens = 45
    return sc


def run(use_volume: bool):
    build(use_volume)
    t = time.time()
    bpy.ops.render.render(write_still=True)
    el = time.time() - t
    im = bpy.data.images.load(f"{OUT}/t1_.exr")
    im.reload()
    px = list(im.pixels[: RES[0] * RES[1] * 4])
    mean = sum(px) / len(px)
    print(
        f"T1 {'有雾' if use_volume else '无雾':6s} mean={mean:.6f} "
        f"max={max(px):.4f} nonzero={sum(1 for p in px if p > 1e-4)}/{len(px)} elapsed={el:.1f}s"
    )
    return mean


def main():
    os.makedirs(OUT, exist_ok=True)
    base = run(False)
    fog = run(True)
    d = fog - base
    print(f"\nDIFF mean={d:+.6f}")
    print("VERDICT:", "体积正常工作（T1 通过）" if d > 1e-4 else "体积无贡献（T1 不通过）")

    bh = bpy.app.build_hash
    bh = bh.decode() if isinstance(bh, bytes) else bh
    print(f"\nBlender: {bpy.app.version_string}  hash={bh}")


main()
