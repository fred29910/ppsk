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
import sys

# Blender 以 --python 运行时不会把脚本目录加入 sys.path，
# 同目录的 utils 就 import 不到。手动补上。
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import utils

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
    r.resolution_x, r.resolution_y = utils.RESOLUTION
    r.resolution_percentage = 100
    r.fps = utils.FPS
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
    """开启 View Layer Pass。只开实测存在的，不静默失败。

    ⚠️ 作用于**所有** view layer。只设 view_layers[0] 会让 VL_char 只剩
    combined + cryptomatte，z / vector / mist / diffuse_color 全缺，
    渲出来是残缺数据集 —— plan §2.2 的双轨雾（Depth + Mist）与 Vector Pass
    都靠这些数据 pass；spec §5.2 把「无 View Layer 分层」列为必须补齐的缺口。
    """
    want = passes or AVAILABLE_PASSES
    per_layer, skipped = {}, set()
    for vl in scene.view_layers:
        enabled = []
        for p in want:
            if hasattr(vl, p):
                setattr(vl, p, True)
                enabled.append(p)
            else:
                skipped.add(p)
        per_layer[vl.name] = enabled
    return {
        "ok": True,
        "enabled": sorted(set().union(*per_layer.values()) if per_layer else set()),
        "per_layer": per_layer,
        "skipped": sorted(skipped),
    }


def template_frame_range() -> tuple[int, int]:
    """模板占位帧范围：FRAME_START 起，前后各 HANDLE_FRAMES。

    ⚠️ 这是**模板占位值**，不是任何真实镜头的范围。生产渲染必须显式传
    frame_start / frame_end —— setup_render 在拿不到时（**含半截**）直接失败，
    绝不静默渲 17 帧（静默渲错帧数比直接失败危险得多）。
    """
    return utils.FRAME_START, utils.FRAME_START + 2 * utils.HANDLE_FRAMES


def apply_preset(
    scene,
    *,
    shot: str,
    stage: str,
    version: str = "v001",
    view_transform: str | None = None,
    engine: str = "EEVEE",
    project_root: str = ".",
    frame_start: int | None = None,
    frame_end: int | None = None,
) -> dict:
    """
    渲染设置唯一入口。setup_render 与 build_templates 共用这一份实现。

    覆盖：分辨率 / fps / 公制单位 / 帧范围 / 快门 0.5 帧 /
    运动模糊关 + Vector 开 / 色彩四元组 / EXR multilayer /
    帧序列 #### 占位符 / 全部可用 View Layer Pass（**所有** layer）。

    帧范围：frame_start / frame_end **都为 None** 时用 template_frame_range()
    占位 —— 这是模板生成器的正当用途（模板是静态文件，不存在「漏传一半」）。
    任一为 None（半截）则直接失败：静默补成占位值就是 C-2 那个 17 帧 bug。
    生产渲染走 setup_render，它在到达这里之前就已经强制两个都给了。

    ⚠️ 不设 volumetric_samples / taa_render_samples：本机无 GPU，
    采样数由渲染机决定（spec §11）。
    """
    if stage not in STAGES:
        return {"ok": False, "error": f"未知环节: {stage}",
                "hint": f"合法值: {', '.join(STAGES)}"}

    # 版本闸门在任何设置写入之前。5.2 的场景序列化格式与 RNA 行为都可能被
    # 小版本改掉，跨版本写出的 .blend 是「打开就报错」的那种坏。
    # spec §10.4：版本号前两段 ≠ 5.2 → 退出码非 0。build hash 不同只警告
    # （本机是 dev build，官方发行版 hash 必然不同，硬失败等于永久挡住）。
    ver = utils.check_blender_version(strict=False)
    if not ver.get("ok"):
        return {"ok": False, "error": ver.get("error"), "hint": ver.get("hint")}

    half = [n for n, v in (("frame_start", frame_start), ("frame_end", frame_end))
            if v is None]
    if half and len(half) < 2:
        return {"ok": False,
                "error": f"未指定 {'/'.join(half)}（半截帧范围）",
                "hint": "两个一起给，或两个都不给（都不给 = 模板占位值）"}

    placeholder_fs, placeholder_fe = template_frame_range()
    fs = placeholder_fs if frame_start is None else frame_start
    fe = placeholder_fe if frame_end is None else frame_end
    if fe < fs:
        return {"ok": False,
                "error": f"帧范围非法: end({fe}) < start({fs})",
                "hint": "frame_start / frame_end 取自 00_project/pipeline/shotlist.csv"}

    # 引擎交给 set_engine 处理（"EEVEE"→"BLENDER_EEVEE" / "CYCLES" 分支）
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.frame_start = fs
    scene.frame_end = fe
    scene.frame_current = min(max(utils.FRAME_START + utils.HANDLE_FRAMES, fs), fe)
    # ⚠️ 单位是帧不是角度（utils.shutter_frames 已封装换算）
    scene.render.motion_blur_shutter = utils.shutter_frames()
    scene.render.use_motion_blur = False   # D7：与 Vector Pass 互斥，选后者

    res = {
        "engine": set_engine(scene, engine),
        "color": setup_color(scene, view_transform or utils.VIEW_TRANSFORM),
        "output": setup_output(scene, shot, stage, version, project_root),
        "passes": setup_passes(scene),
    }
    failed = {k: v for k, v in res.items() if not v.get("ok")}
    if failed:
        return {"ok": False,
                "error": "; ".join(f"{k}: {v['error']}" for k, v in failed.items()),
                "hint": "见 g0_feasibility_report.md 附录",
                **res}
    return {"ok": True, "warnings": list(ver.get("warnings") or []), **res}


# ============================================================ 镜头


def create_shot(
    seq: str,
    shot: str,
    frame_start: int | None = None,
    frame_end: int | None = None,
    project_root: str = ".",
    dry_run: bool = False,
) -> dict:
    """从镜头表创建目录结构。

    frame_start / frame_end 是 per-shot 数据（shotlist.csv），**只回显到返回值**，
    不写 scene 的帧范围 —— 帧范围由 setup_render / apply_preset 按传参设置。
    留空就回显 None，不猜：猜出来的占位范围没人能分辨真假。
    """
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
        "sensor_width": utils.SENSOR_WIDTH,
        "shutter_angle": utils.SHUTTER_ANGLE,
        "fps": utils.FPS,
    }


def setup_render(
    shot: str,
    stage: str = "light",
    engine: str = "EEVEE",
    view_transform: str | None = None,
    project_root: str = ".",
    dry_run: bool = False,
    frame_start: int | None = None,
    frame_end: int | None = None,
) -> dict:
    """
    分辨率 / 帧率 / 色彩管理 / View Layer / Pass / 输出路径

    view_transform 默认 None，由 apply_preset 兜底成 utils.VIEW_TRANSFORM
    （AgX）。G0-T4 实测 AgX 会让青色自发光发白，
    关键 FX 镜头（sh020/030/040）应传 "Khronos PBR Neutral"。

    frame_start / frame_end **两个都必须给**，任一为 None 就返回 ok:False。
    帧范围是 per-shot 数据（shotlist.csv），不是常量。
    ⚠️ 半截参数也拒绝：只给 frame_start 而漏了 frame_end，几乎总是
    调用方的疏忽（漏写参数、变量没赋值、参数名记错）。把它静默补成占位的
    `FRAME_START + 2*HANDLE_FRAMES`（17 帧）会渲出一段废片且**不报错** ——
    上一轮只拦「两个都 None」，这个窄口就是这么漏的。
    模板占位值是模板生成器（apply_preset）的正当用途，不是生产渲染的。
    """
    if stage not in STAGES:
        return {
            "ok": False,
            "error": f"未知环节: {stage}",
            "hint": f"合法值: {', '.join(STAGES)}",
        }
    # ⚠️ 任一缺失即失败，不落占位。apply_preset 落到模板占位（17 帧）会让
    #    6 秒镜只渲 17 帧且不报错 —— 这正是要消灭的静默失效。
    missing = [n for n, v in (("frame_start", frame_start), ("frame_end", frame_end))
               if v is None]
    if missing:
        return {
            "ok": False,
            "error": f"未指定 {'/'.join(missing)}",
            "hint": "从 00_project/pipeline/shotlist.csv 读该镜的 frame_start/frame_end，"
                    "或显式传参 / 用 CLI --frame-range START END",
        }
    if dry_run:
        return {
            "ok": True,
            "shot": shot,
            "stage": stage,
            "engine": engine,
            "view_transform": view_transform,
            "frame_start": frame_start,
            "frame_end": frame_end,
            "dry_run": True,
            "note": f"未写盘。执行内容：引擎/色彩四元组/"
                    f"{utils.RESOLUTION[0]}x{utils.RESOLUTION[1]}@{utils.FPS}fps/"
                    f"EXR multilayer/Available Passes",
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
    r = apply_preset(scene, shot=shot, stage=stage, engine=engine,
                     view_transform=view_transform, project_root=project_root,
                     frame_start=frame_start, frame_end=frame_end)
    if not r.get("ok"):
        return {"ok": False, "error": r.get("error"), "hint": r.get("hint")}
    return {"ok": True, "shot": shot, "stage": stage, **r}


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
    p.add_argument("--frame-range", nargs=2, type=int, metavar=("START", "END"),
                   help="该镜真实帧范围（shotlist.csv）。--setup_render 必填，"
                        "缺失直接失败，不落回模板占位 17 帧")
    p.add_argument("--engine", default="EEVEE", choices=["EEVEE", "CYCLES"])
    p.add_argument(
        "--view-transform",
        default=None,
        help="默认 utils.VIEW_TRANSFORM（AgX）；关键 FX 镜头用 Khronos PBR Neutral（G0-T4 §4.4）",
    )
    p.add_argument("--project-root", default=".")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args(_argv())

    if a.create_shot:
        r = create_shot(*a.create_shot, project_root=a.project_root, dry_run=a.dry_run)
    elif a.setup_camera:
        r = setup_camera(*a.setup_camera)
    elif a.setup_render:
        fs, fe = a.frame_range if a.frame_range else (None, None)
        r = setup_render(
            *a.setup_render,
            engine=a.engine,
            view_transform=a.view_transform,
            project_root=a.project_root,
            dry_run=a.dry_run,
            frame_start=fs,
            frame_end=fe,
        )
    else:
        p.print_help()
        return 0

    print(r)
    # ⚠️ Blender 抛未捕获异常时退出码仍是 0，只有显式 sys.exit(N) 才传播。
    #    失败路径必须返回非 0，否则 CI / 调度器看到的是「成功」。
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
