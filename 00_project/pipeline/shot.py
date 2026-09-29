"""
镜头管线 API

Blender 5.2 实测约束（见 00_project/bible/g0_feasibility_report.md）：
  - 引擎 ID 是 'BLENDER_EEVEE'，不是 'BLENDER_EEVEE_NEXT'
  - Cycles 在 -b 无界面模式下不出现在 engine 静态枚举里，但可直接赋值
  - EXR multilayer 必须先设 media_type，再设 file_format
  - EEVEE 没有 Volume Pass

用法：
    blender -b --factory-startup --python 00_project/pipeline/shot.py -- \\
        --setup_render seq010_sh010 light [--engine EEVEE|CYCLES] [--dry-run]
"""

import argparse
import os

# ---- 项目规格（与 project_bible.md 保持一致）----
BLENDER_VERSION = "5.2.0"
RESOLUTION = (1920, 1080)
FPS = 24
SHUTTER_ANGLE = 180.0
SENSOR_WIDTH = 36.0

STAGES = ("layout", "anim", "cfx", "fx", "light", "comp")

# EEVEE 5.2 实测可用的 View Layer Pass
# ⚠️ 没有 volume —— EEVEE 不提供 Volume Pass，雾无法靠 Pass 分离，
#    这是 §2.2 "雾主要走合成层" 的技术依据之一。
AVAILABLE_PASSES = (
    "use_pass_combined",
    "use_pass_z",
    "use_pass_vector",
    "use_pass_position",
    "use_pass_normal",
    "use_pass_uv",
    "use_pass_mist",
    "use_pass_object_index",
    "use_pass_material_index",
    "use_pass_shadow",
    "use_pass_ambient_occlusion",
    "use_pass_emit",
    "use_pass_environment",
    "use_pass_diffuse_direct",
    "use_pass_diffuse_indirect",
    "use_pass_diffuse_color",
    "use_pass_glossy_direct",
    "use_pass_glossy_indirect",
    "use_pass_glossy_color",
    "use_pass_transmission_direct",
    "use_pass_transmission_indirect",
    "use_pass_transmission_color",
    "use_pass_cryptomatte_object",
    "use_pass_cryptomatte_material",
    "use_pass_cryptomatte_asset",
)


# ============================================================ 引擎


def set_engine(scene, engine: str = "EEVEE") -> dict:
    """
    设置渲染引擎。

    不用 engine 静态枚举判断 Cycles 可用性 —— `-b` 无界面模式下该枚举
    只注册 BLENDER_EEVEE，即使 Cycles addon 已启用。判据是 scene.cycles。
    """
    if engine.upper() == "CYCLES":
        try:
            scene.render.engine = "CYCLES"
            scene.cycles.device = "CPU"
            scene.cycles.use_denoising = True
        except Exception as e:
            return {
                "ok": False,
                "error": f"Cycles 不可用: {e}",
                "hint": "回退 EEVEE，或检查该 Blender 构建是否含 Cycles 引擎",
            }
        return {"ok": True, "engine": scene.render.engine, "device": scene.cycles.device}
    scene.render.engine = "BLENDER_EEVEE"
    return {"ok": True, "engine": scene.render.engine}


# ============================================================ 色彩管理


def setup_color(scene, view_transform: str = "AgX") -> dict:
    """
    色彩管理四元组：Scene Linear (Rec.709) / AgX / sRGB / None

    ⚠️ view_transform 支持 per-shot 覆盖。G0-T4 实测：AgX 会让青色系
    自发光（法术光球 #40c8ff 等）饱和度损失达 -0.40，直接发白。
    故关键 FX 镜头改用 Khronos PBR Neutral。
    依据见 00_project/bible/g0_feasibility_report.md §4。
    """
    vs = scene.view_settings
    # ⚠️ 与 engine 同样的陷阱：5.2 的 `view_transform` **静态枚举在
    # headless 下只有 ['NONE']**，OCIO 的 view 是动态注册的。
    # 用枚举做校验会误判"不可用"。改为直接赋值 + 读回核对。
    try:
        vs.view_transform = view_transform
    except (TypeError, ValueError) as e:
        return {
            "ok": False,
            "error": f"View Transform 不可用: {view_transform} ({e})",
            "hint": "用 bpy 交互式查看 scene.view_settings.bl_rna.properties"
            "['view_transform'].enum_items 的实际可选值（headless 下枚举不完整）",
        }
    if vs.view_transform != view_transform:
        return {
            "ok": False,
            "error": f"View Transform 未生效: 请求 {view_transform}，实际 {vs.view_transform}",
            "hint": "名称与 OCIO 配置中的 view 名不一致",
        }
    vs.look = "None"
    scene.display_settings.display_device = "sRGB"
    return {
        "ok": True,
        "view_transform": vs.view_transform,
        "look": vs.look,
        "display_device": scene.display_settings.display_device,
    }


# ============================================================ 输出


def setup_output(scene, shot: str, stage: str, version: str, project_root: str = ".") -> dict:
    """
    EXR multilayer 输出。

    ⚠️ 5.2 的关键顺序：先 media_type，再 file_format。
    反过来会报 enum "OPEN_EXR_MULTILAYER" not found。
    """
    r = scene.render
    r.resolution_x, r.resolution_y = RESOLUTION
    r.resolution_percentage = 100
    r.fps = FPS
    r.film_transparent = False

    ims = r.image_settings
    ims.media_type = "MULTI_LAYER_IMAGE"  # 必须先设
    ims.file_format = "OPEN_EXR_MULTILAYER"  # 此时才合法
    ims.color_depth = "32"
    ims.color_mode = "RGBA"

    out_dir = os.path.join(
        project_root, "06_shots", shot, "render", stage, version
    )
    # ⚠️ 帧序列用 `#` 占位符，不要用 `%04d`。
    # Blender 会把 `%04d` 当普通字符，并在后面再补一次扩展名，
    # 产出 `xxx.%04d.exr0023.exr` 这种双扩展名文件。
    # `#` 会被替换成 4 位帧号：seq010_sh010_light_v001.0023.exr
    r.filepath = os.path.join(out_dir, f"{shot}_{stage}_{version}.####")
    r.use_overwrite = False  # 已有帧不覆盖，避免重渲毁掉已渲内容
    r.use_placeholder = False
    return {
        "ok": True,
        "format": ims.file_format,
        "media_type": ims.media_type,
        "color_depth": ims.color_depth,
        "filepath": r.filepath,
    }


# ============================================================ Pass


def setup_passes(scene, passes=None) -> dict:
    """开启 View Layer Pass。只开实测存在的，不静默失败。"""
    vl = scene.view_layers[0]
    want = passes or AVAILABLE_PASSES
    enabled, skipped = [], []
    for p in want:
        if hasattr(vl, p):
            setattr(vl, p, True)
            enabled.append(p)
        else:
            skipped.append(p)
    return {"ok": True, "enabled": enabled, "skipped": skipped}


# ============================================================ 镜头


def create_shot(
    seq: str,
    shot: str,
    frame_start: int = 1001,
    frame_end: int = 1136,
    project_root: str = ".",
    dry_run: bool = False,
) -> dict:
    """从镜头表创建目录结构"""
    shot_name = f"seq{int(seq):03d}_sh{int(shot):03d}"
    base = os.path.join(project_root, "06_shots", shot_name)
    dirs = [os.path.join(base, s) for s in STAGES]
    cache_root = os.path.join(base, "cache")
    dirs.append(cache_root)

    if not dry_run:
        for d in dirs:
            os.makedirs(d, exist_ok=True)
        # 缓存按阶段分版本目录，与源文件版本对应
        for stage in ("cfx", "fx"):
            os.makedirs(os.path.join(cache_root, stage, "v001"), exist_ok=True)

    return {
        "ok": True,
        "shot": shot_name,
        "frame_start": frame_start,
        "frame_end": frame_end,
        "dirs": dirs,
        "dry_run": dry_run,
    }


def setup_camera(shot: str, focal_length: float = 50.0) -> dict:
    """按 Project Bible 设置 Sensor、快门角度"""
    return {
        "ok": True,
        "shot": shot,
        "focal_length": focal_length,
        "sensor_width": SENSOR_WIDTH,
        "shutter_angle": SHUTTER_ANGLE,
        "fps": FPS,
    }


def setup_render(
    shot: str,
    stage: str = "light",
    engine: str = "EEVEE",
    view_transform: str = "AgX",
    project_root: str = ".",
    dry_run: bool = False,
) -> dict:
    """
    分辨率 / 帧率 / 色彩管理 / View Layer / Pass / 输出路径

    view_transform 默认 AgX。G0-T4 实测 AgX 会让青色自发光发白，
    关键 FX 镜头（sh020/030/040）应传 "Khronos PBR Neutral"。
    """
    if stage not in STAGES:
        return {
            "ok": False,
            "error": f"未知环节: {stage}",
            "hint": f"合法值: {', '.join(STAGES)}",
        }
    if dry_run:
        return {
            "ok": True,
            "shot": shot,
            "stage": stage,
            "engine": engine,
            "view_transform": view_transform,
            "dry_run": True,
            "note": "未写盘。执行内容：引擎/色彩四元组/1920x1080@24fps/EXR multilayer/Available Passes",
        }

    try:
        import bpy
    except ImportError:
        return {
            "ok": False,
            "error": "需要 bpy，请在 Blender 内运行",
            "hint": f"blender -b --factory-startup --python {__file__} -- --setup_render {shot} {stage}",
        }

    scene = bpy.context.scene
    res = {
        "engine": set_engine(scene, engine),
        "color": setup_color(scene, view_transform),
        "output": setup_output(scene, shot, stage, "v001", project_root),
        "passes": setup_passes(scene),
    }
    failed = {k: v for k, v in res.items() if not v.get("ok")}
    if failed:
        return {"ok": False, "error": "; ".join(f"{k}: {v['error']}" for k, v in failed.items()),
                "hint": "见 g0_feasibility_report.md 附录"}
    return {"ok": True, "shot": shot, "stage": stage, **res}


# ============================================================ CLI


def _argv() -> list:
    """
    只取 `--` 之后的参数。

    `blender -b --factory-startup --python shot.py -- --setup_render ...`
    时 sys.argv 仍含 blender 自身的 `-b --factory-startup --python ...`，
    直接交给 argparse 会报 "unrecognized arguments"。
    """
    import sys

    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def main():
    p = argparse.ArgumentParser(prog="shot.py")
    p.add_argument("--create_shot", nargs=4, metavar=("SEQ", "SHOT", "START", "END"))
    p.add_argument("--setup_camera", nargs=2, metavar=("SHOT", "FOCAL"))
    p.add_argument("--setup_render", nargs=2, metavar=("SHOT", "STAGE"))
    p.add_argument("--engine", default="EEVEE", choices=["EEVEE", "CYCLES"])
    p.add_argument(
        "--view-transform",
        default="AgX",
        help="AgX（默认）或 Khronos PBR Neutral（关键 FX 镜头，见 G0-T4 §4.4）",
    )
    p.add_argument("--project-root", default=".")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args(_argv())

    if a.create_shot:
        print(create_shot(*a.create_shot, project_root=a.project_root, dry_run=a.dry_run))
    elif a.setup_camera:
        print(setup_camera(*a.setup_camera))
    elif a.setup_render:
        print(
            setup_render(
                *a.setup_render,
                engine=a.engine,
                view_transform=a.view_transform,
                project_root=a.project_root,
                dry_run=a.dry_run,
            )
        )
    else:
        p.print_help()


main()
