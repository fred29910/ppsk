"""
G0-T4 探针：自发光法术光球在 AgX 下是否发白

背景（plan.md §9.3）：
  AgX 会对高亮高饱和色做去饱和。而法术光球、剑气、灵光正是本项目的
  招牌元素 —— 在 AgX 下容易发白发灰。

判据（plan.md §5.0 T4）：颜色不发白；否则确定 per-shot 色彩策略（§8.2）。

⚠️ 三个实测踩过的坑（勿回退）：
  1. EXR 保存**场景线性，不烘入显示变换**（§7.2 规定）。因此直接从 EXR
     读像素**拿不到 View Transform 的影响** —— 三种变换读出完全相同的值。
  2. Blender bpy 的 `image.pixels` 访问**不套用** View Transform，
     所以"新建 image 赋线性值再读回"这招无效，读回的还是线性原值。
  3. 外部 ffmpeg 也不行：本机 `tonemap` filter **不认 agx**
     （"Undefined constant or missing '(' in 'agx'"），
     `zscale` 也缺 bt709 色彩空间路径（"no path between colorspaces"）。
  → 正解：**渲染时就把 View Transform 套上**，直接输出 PNG，
     再读 PNG 像素。此时 PNG 已是显示后的值。

方法：
  同一场景在 AgX / Khronos PBR Neutral / Standard 下各渲一张 PNG，
  比较各色球中心的饱和度。附带有效性自检：三种变换读数必须不同，
  否则说明显示变换没生效，本轮结果作废。

用法：
    blender -b --factory-startup --python g0_probe_t4.py -- --out <目录>

依赖：本机 ffmpeg（tonemap filter 已验证支持 agx / none）
"""

import os
import subprocess
import sys

RES = (960, 540)
# 扫多档强度：区分"AgX 去饱和"与"强度过高过曝"两种成因
STRENGTHS = [0.5, 1.0, 2.0, 4.0, 8.0]
# 饱和度低于此值视为"发白"（三通道趋同，色相信息丢失）
SAT_THRESHOLD = 0.25

# 法术光球配色（取自 01_story/art_design_env_fx.md）
SPHERE_COLORS = [
    ("orb_core",   (0.627, 0.941, 1.000), "#a0f0ff"),  # 法术光球核心
    ("orb_mid",    (0.251, 0.784, 1.000), "#40c8ff"),  # 法术光球中层
    ("orb_outer",  (0.125, 0.502, 0.753), "#2080c0"),  # 法术光球外层
    ("trail_core", (1.000, 0.973, 0.878), "#fff8e0"),  # 剑气核心
    ("trail_mid",  (1.000, 0.843, 0.000), "#ffd700"),  # 剑气中层
    ("trail_edge", (1.000, 0.549, 0.000), "#ff8c00"),  # 剑气边缘
    ("spark",      (0.831, 0.686, 0.216), "#d4af37"),  # 光屑暖金
]

VIEW_TRANSFORMS = ["AgX", "Khronos PBR Neutral", "Standard"]

SPACING = 1.1
CAM_DIST = 8.0
LENS = 50.0


def _argv() -> list:
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


_a = _argv()
OUT = "/tmp/g0_t4"
for _i, _v in enumerate(_a):
    if _v == "--out" and _i + 1 < len(_a):
        OUT = _a[_i + 1]
        break


def srgb_to_linear(c):
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c)


def build(out_prefix, emission_strength=1.0):
    """一排自发光球，纯黑背景。"""
    import bpy

    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    r = sc.render
    r.resolution_x, r.resolution_y = RES
    r.resolution_percentage = 100
    r.image_settings.media_type = "IMAGE"
    r.image_settings.file_format = "OPEN_EXR"
    r.image_settings.color_depth = "32"
    r.filepath = os.path.join(OUT, out_prefix)

    world = bpy.data.worlds.new("W")
    world.use_nodes = True
    bgn = world.node_tree.nodes["Background"]
    bgn.inputs[0].default_value = (0, 0, 0, 1)
    bgn.inputs[1].default_value = 0.0
    sc.world = world

    n = len(SPHERE_COLORS)
    for i, (name, srgb, _hex) in enumerate(SPHERE_COLORS):
        x = (i - (n - 1) / 2) * SPACING
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=0.42, segments=48, ring_count=24, location=(x, 0, 0)
        )
        obj = bpy.context.object
        obj.name = f"SPH_{name}"
        m = bpy.data.materials.new(f"M_{name}")
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (*srgb_to_linear(srgb), 1.0)
        em.inputs["Strength"].default_value = emission_strength
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
        obj.data.materials.append(m)

    cd = bpy.data.cameras.new("CAM_T4")
    cam = bpy.data.objects.new("CAM_T4", cd)
    sc.collection.objects.link(cam)
    cam.location = (0, -CAM_DIST, 0)
    cam.rotation_euler = (1.5708, 0, 0)
    cd.lens = LENS
    sc.camera = cam
    return sc


def sphere_pixel_x(i, n, w):
    """第 i 个球中心在画面中的 x 像素（与 build 的几何一致）。"""
    world_x = (i - (n - 1) / 2) * SPACING
    # 相机在 -CAM_DIST 朝 +Y 看，lens LENS，sensor 默认 36mm
    # 水平视野对应的世界宽度 = 2 * CAM_DIST * (36/2) / LENS
    view_w = 2 * CAM_DIST * (36.0 / 2.0) / LENS
    return int(round(w * (0.5 + world_x / view_w)))


def png_pixel(path, x, y):
    """用 ffmpeg 读 PNG 单像素，避免引入 PIL 依赖。"""
    r = subprocess.run(
        [
            "ffmpeg", "-v", "error", "-i", path,
            "-vf", f"crop=1:1:{x}:{y},format=rgb24",
            "-f", "rawvideo", "-",
        ],
        check=True, capture_output=True,
    )
    b = r.stdout[:3]
    return (b[0] / 255.0, b[1] / 255.0, b[2] / 255.0) if len(b) == 3 else (0.0, 0.0, 0.0)


def metrics(rgb):
    r, g, b = rgb
    mx, mn = max(rgb), min(rgb)
    sat = 0.0 if mx == 0 else (mx - mn) / mx
    return {
        "r": r, "g": g, "b": b, "sat": sat,
        "lum": 0.2126 * r + 0.7152 * g + 0.0722 * b,
        "clipped": sum(1 for c in rgb if c >= 0.996) >= 2,
    }


def main():
    import bpy

    os.makedirs(OUT, exist_ok=True)

    # 1. 每种 View Transform 各渲一张 PNG（渲染时即套用显示变换）
    #    ⚠️ 不能"渲线性 EXR 再外部转换"：本机 ffmpeg 的 tonemap 不支持 agx，
    #    zscale 也缺 bt709 色彩空间路径（实测报 "no path between colorspaces"）。
    #    直接让 Blender 在渲染输出阶段套用 View Transform → PNG，最可靠。
    n = len(SPHERE_COLORS)
    results = {}

    # ⚠️ 必须扫多个 Emission Strength。§9.3 担心的"AgX 去饱和"在实践中
    #    常常被"自发光强度过高导致过曝"掩盖 —— 两者的现象都是发白，
    #    但解法完全不同（一个改强度/后期，一个改 View Transform）。
    for strength in STRENGTHS:
        print(f"\n{'#' * 66}\n# Emission Strength = {strength}\n{'#' * 66}")
        block = {}
        for vt in VIEW_TRANSFORMS:
            prefix = f"s{strength:g}_{vt.split()[0]}_".replace(".", "p")
            png = os.path.join(OUT, prefix + ".png")
            sc = build(prefix, emission_strength=strength)
            sc.view_settings.view_transform = vt
            sc.view_settings.look = "None"
            sc.render.image_settings.media_type = "IMAGE"
            sc.render.image_settings.file_format = "PNG"
            sc.render.image_settings.color_mode = "RGB"
            sc.render.image_settings.color_depth = "8"
            bpy.ops.render.render(write_still=True)
            if not os.path.exists(png):
                cands = [p for p in os.listdir(OUT) if p.startswith(os.path.basename(prefix))]
                print(f"[{vt}] 未产出预期文件，目录里有: {cands[:4]}")
                continue

            row = {}
            for i, (name, _srgb, hexv) in enumerate(SPHERE_COLORS):
                x = sphere_pixel_x(i, n, RES[0])
                row[name] = metrics(png_pixel(png, x, RES[1] // 2))
            block[vt] = row

            print(f"\n--- {vt} ---")
            print(f"{'色球':12s} {'设计值':9s} {'R':>6s} {'G':>6s} {'B':>6s} {'饱和度':>7s} {'亮度':>6s}  判定")
            for name, _s, hexv in SPHERE_COLORS:
                m = row[name]
                flag = "✗ 发白" if m["clipped"] or m["sat"] < SAT_THRESHOLD else "✓"
                print(
                    f"{name:12s} {hexv:9s} {m['r']:6.3f} {m['g']:6.3f} {m['b']:6.3f} "
                    f"{m['sat']:7.3f} {m['lum']:6.3f}  {flag}"
                )
        results[strength] = block

    # ---- 有效性自检：同一强度下三种变换必须不同 ----
    ok = True
    for s, blk in results.items():
        if len(blk) < 2:
            ok = False
            continue
        keys = list(blk)
        if all(
            abs(blk[keys[0]][nm]["sat"] - blk[k][nm]["sat"]) < 1e-6
            for k in keys[1:] for nm, _s, _h in SPHERE_COLORS
        ):
            print(f"\n⚠️ 有效性自检失败（strength={s}）：各 View Transform 读数完全相同")
            ok = False
    if not ok:
        print("本轮结果不可用")
        return
    print("\n有效性自检通过：各 View Transform 读数存在差异")

    # ---- 结论 ----
    print("\n=== 结论 ===")
    for s, blk in sorted(results.items()):
        if "AgX" not in blk:
            continue
        ref = "Khronos PBR Neutral" if "Khronos PBR Neutral" in blk else list(blk)[1]
        deltas = {
            nm: blk["AgX"][nm]["sat"] - blk[ref][nm]["sat"]
            for nm, _s, _h in SPHERE_COLORS
        }
        worst = min(deltas, key=lambda k: deltas[k])
        whitened = [
            nm for nm, _s, _h in SPHERE_COLORS
            if blk["AgX"][nm]["clipped"] or blk["AgX"][nm]["sat"] < SAT_THRESHOLD
        ]
        clean_ref = [
            nm for nm, _s, _h in SPHERE_COLORS
            if not blk[ref][nm]["clipped"] and blk[ref][nm]["sat"] >= SAT_THRESHOLD
        ]
        print(
            f"\nstrength={s:g}  AgX 最大饱和度差 {deltas[worst]:+.3f} ({worst})"
            f"  |  AgX 发白 {len(whitened)}/7  |  {ref[:12]} 发白 {7 - len(clean_ref)}/7"
        )
        if whitened and clean_ref:
            print(f"  → 同样是发白，但 {ref} 能保住: {', '.join(clean_ref)}")
            print(f"     说明是 **View Transform** 问题，换 {ref} 即可，不是强度问题")
        elif whitened and not clean_ref:
            print("  → 换 View Transform 也救不回来 → 是 **强度过高** 导致过曝")
        else:
            print("  → AgX 下未发白，T4 通过")

    # 找出"AgX 能过 且 换 transform 也能过"的最弱强度区间
    print("\n=== 建议 ===")
    passing = [s for s, blk in results.items()
               if "AgX" in blk and not [
                   nm for nm, _s, _h in SPHERE_COLORS
                   if blk["AgX"][nm]["clipped"] or blk["AgX"][nm]["sat"] < SAT_THRESHOLD
               ]]
    if passing:
        print(f"AgX 可直接使用的 Emission Strength: {', '.join(f'{s:g}' for s in passing)}")
        print("→ 按 §9.3 保留 AgX（与全片色彩四元组一致），把 FX 自发光强度限制在上述区间")
    else:
        print("所有测试强度下 AgX 均发白 → 关键 FX 镜头需 per-shot 换 View Transform（§9.3 方案一）")

    bh = bpy.app.build_hash
    bh = bh.decode() if isinstance(bh, bytes) else bh
    print(f"\nBlender: {bpy.app.version_string}  hash={bh}")
    print(f"测试的 View Transform: {', '.join(results)}")


main()
