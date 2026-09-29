"""
审阅片生成

Blender 5.2 实测约束（见 00_project/bible/g0_feasibility_report.md §6.3）：
  ffmpeg / ffprobe **无法直接解码 multilayer EXR**：
      [exr @ ...] Missing red channel / green / blue
      codec_name=exr  width=0  height=0
      ffmpeg → PNG: Nothing was written into output file

  因此必须先抽 Combined 层为单层图像，再交给 ffmpeg 烧录。
  本模块的 exr_extract_layer() 用 Blender bpy 完成抽取（不依赖
  Python OpenEXR 绑定 —— 本机该绑定缺失）。

用法：
    blender -b --factory-startup --python 00_project/pipeline/review.py -- \\
        --create_preview seq010_sh010 v001 light [--project-root .] [--dry-run]
"""

import argparse
import os
import subprocess
import sys

FPS = 24


def exr_extract_layer(
    exr_path: str,
    out_path: str,
    layer: str = "Combined",
    project_root: str = ".",
    dry_run: bool = False,
) -> dict:
    """
    从 multilayer EXR 抽指定层为单层 EXR（ffmpeg 可读）。

    返回 {"ok": False, "error", "hint"} 表示失败。
    """
    if not os.path.exists(exr_path):
        return {
            "ok": False,
            "error": f"EXR 不存在: {exr_path}",
            "hint": "先跑 collect_render 检查帧范围与渲染输出路径",
        }
    if dry_run:
        return {"ok": True, "src": exr_path, "dst": out_path, "layer": layer, "dry_run": True}

    try:
        import OpenImageIO as oiio
    except ImportError:
        return {
            "ok": False,
            "error": "需要 OpenImageIO（Blender 自带，须在 Blender 内运行）",
            "hint": f"blender -b --factory-startup --python {__file__} -- ...",
        }

    # 不用 bpy.data.images.load —— 5.2 的 bpy 绑定读 multilayer EXR
    # 会返回 size=(0,0) channels=0，pixels 为空。OpenImageIO 能正确解析。
    inp = None
    out = None
    try:
        inp = oiio.ImageInput.open(exr_path)
        if inp is None:
            return {
                "ok": False,
                "error": f"OIIO 打不开: {exr_path}",
                "hint": "确认文件完整（非渲染中断产物）",
            }
        spec = inp.spec()
        names = list(spec.channelnames)
        # 通道名形如 ViewLayer.Combined.R
        want = [f"ViewLayer.{layer}.{c}" for c in ("R", "G", "B")]
        if not all(w in names for w in want):
            # 退而求其次：任何含 .R/.G/.B 且以 Combined 结尾的通道
            alt = [n for n in names if n.endswith((".R", ".G", ".B"))]
            if not alt:
                return {
                    "ok": False,
                    "error": f"找不到 Combined 层，通道为: {names}",
                    "hint": "确认该 EXR 是 multilayer 且含 Combined",
                }
            return {
                "ok": False,
                "error": f"层名不匹配：期望 ViewLayer.{layer}，实际通道 {names[:6]}",
                "hint": "多层命名可能带 ViewLayer 前缀差异，检查 render/view layer 命名",
            }

        # read_image 返回 numpy 数组，shape = (h, w, nchannels)。
        # 多层 EXR 的第一个 subimage 就是 Combined，通道名形如
        # ViewLayer.Combined.R / .G / .B / .A —— 已是 RGB(A) 顺序，无需重排。
        pixels = inp.read_image(format=oiio.FLOAT)
        if pixels is None:
            return {"ok": False, "error": "OIIO 读像素失败", "hint": "文件可能损坏"}
        h, w, nch = pixels.shape
        if nch not in (3, 4):
            return {
                "ok": False,
                "error": f"Combined 层通道数异常: {nch}（期望 3 或 4）",
                "hint": f"实际通道: {list(spec.channelnames)}",
            }
        if nch == 3:
            import numpy as np

            pixels = np.concatenate(
                [pixels, np.ones((h, w, 1), dtype=pixels.dtype)], axis=2
            )

        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        out = oiio.ImageOutput.create(out_path)
        if out is None:
            return {
                "ok": False,
                "error": f"无法创建输出: {out_path}",
                "hint": "检查目录权限与磁盘空间",
            }
        # 写单层 EXR：ffmpeg 无法读 multilayer，但能读单层
        single = oiio.ImageSpec(w, h, 4, oiio.FLOAT)
        out.open(out_path, single)
        out.write_image(pixels.astype("float32").reshape(-1))
        out.close()
        out = None
        return {
            "ok": True,
            "src": exr_path,
            "dst": out_path,
            "layer": layer,
            "size": [spec.width, spec.height],
        }
    except Exception as e:
        return {
            "ok": False,
            "error": f"抽层失败: {type(e).__name__}: {e}",
            "hint": "确认 EXR 是 multilayer 且含 Combined 层",
        }
    finally:
        if inp is not None:
            inp.close()
        if out is not None:
            out.close()


def burn_in_frame(src_exr: str, dst_exr: str, text: str, dry_run: bool = False) -> dict:
    """
    用 Blender VSE 的 Text strip 把审阅信息烧进画面。

    为什么不用 ffmpeg drawtext：本机 ffmpeg 静态构建未编译 libfreetype，
    无 drawtext filter（字体文件本身齐全）。而 §6.1 强制要求烧录
    镜号+阶段+版本+帧号+时码。Blender VSE 自带字体渲染，不依赖外部 filter。

    为什么不用合成器：实测 Blender 5.2 headless 下 CompositorNodeImage
    → 渲染会崩溃（连纯 pass-through 也崩），故走 VSE。VSE 路线实测可用。
    """
    if dry_run:
        return {"ok": True, "src": src_exr, "dst": dst_exr, "text": text, "dry_run": True}
    if not os.path.exists(src_exr):
        return {"ok": False, "error": f"源文件不存在: {src_exr}", "hint": "先抽层"}

    try:
        import bpy
    except ImportError:
        return {
            "ok": False,
            "error": "需要 bpy",
            "hint": f"blender -b --factory-startup --python {__file__} -- ...",
        }

    try:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        sc = bpy.context.scene
        img = bpy.data.images.load(src_exr)
        if img.size[0] == 0:
            return {"ok": False, "error": f"源 EXR 无法加载: {src_exr}", "hint": "重抽层"}

        sc.sequence_editor_create()
        se = sc.sequence_editor
        se.strips.new_image("plate", src_exr, channel=1, frame_start=1)
        txt = se.strips.new_effect("burn", type="TEXT", channel=2, frame_start=1, length=1)
        txt.text = text
        txt.font_size = max(12, int(img.size[1] * 0.10))
        # ⚠️ VSE 文字 location 原点在**左下**，不是左上。设 0.02/0.05 才是左下角。
        txt.location = (0.02, 0.05)
        txt.color = (1.0, 1.0, 1.0, 1.0)
        txt.use_shadow = True

        sc.render.use_sequencer = True
        sc.render.use_compositing = False
        sc.frame_start = 1
        sc.frame_end = 1
        r = sc.render
        r.resolution_x, r.resolution_y = img.size[0], img.size[1]
        r.resolution_percentage = 100
        r.image_settings.media_type = "IMAGE"
        r.image_settings.file_format = "OPEN_EXR"
        r.image_settings.color_depth = "32"
        # 动画渲染会补帧号+扩展名，用 # 占位符避免双扩展名
        base = dst_exr[:-4] if dst_exr.endswith(".exr") else dst_exr
        r.filepath = f"{base}.####"

        bpy.ops.render.render(animation=True, write_still=True)

        d = os.path.dirname(dst_exr) or "."
        cands = sorted(p for p in os.listdir(d) if p.startswith(os.path.basename(base)))
        if not cands:
            return {"ok": False, "error": "烧录未产出文件", "hint": "检查 VSE strip 配置"}
        produced = os.path.join(d, cands[0])
        if os.path.abspath(produced) != os.path.abspath(dst_exr):
            os.replace(produced, dst_exr)
        return {"ok": True, "src": src_exr, "dst": dst_exr, "text": text}
    except Exception as e:
        return {
            "ok": False,
            "error": f"烧录失败: {type(e).__name__}: {e}",
            "hint": "VSE Text strip 路线；渲染机上可改用带 libfreetype 的 ffmpeg drawtext",
        }


def _timecode(frame: int, fps: int = FPS) -> str:
    """帧号 → 时码 HH:MM:SS:FF"""
    f = frame - 1
    ff = f % fps
    total_s = f // fps
    return f"{total_s // 3600:02d}:{(total_s // 60) % 60:02d}:{total_s % 60:02d}:{ff:02d}"


def create_preview(
    shot: str,
    version: str,
    stage: str = "light",
    frame_start: int = 1001,
    frame_end: int = 1136,
    project_root: str = ".",
    dry_run: bool = False,
) -> dict:
    """
    生成带烧录信息的审阅片（镜号 + 阶段 + 版本 + 帧号 + 时码）。

    三步：
      1. exr_extract_layer: multilayer EXR → 单层 EXR（ffmpeg 读不了 multilayer）
      2. burn_in_frame: Blender VSE Text strip 烧录信息（本机 ffmpeg 无 drawtext）
      3. ffmpeg: 序列帧 → H.264 mp4
    """
    render_dir = os.path.join(project_root, "06_shots", shot, "render", stage, version)
    review_dir = os.path.join(project_root, "07_review", shot)
    out_path = os.path.join(review_dir, f"{shot}_{stage}_{version}_burn.mp4")
    staging = os.path.join(review_dir, "_staging")

    # 与 shot.py 的 `####` 占位符对应
    frames = [
        os.path.join(render_dir, f"{shot}_{stage}_{version}.{f:04d}.exr")
        for f in range(frame_start, frame_end + 1)
    ]
    missing = [f for f in frames if not os.path.exists(f)]
    if missing:
        return {
            "ok": False,
            "error": f"缺 {len(missing)} 帧（示例: {os.path.basename(missing[0])}）",
            "hint": "跑 collect_render 定位缺口；重跑渲染只补缺失帧",
        }

    cmd = [
        "ffmpeg",
        "-y",
        "-start_number", str(frame_start),
        "-i", os.path.join(staging, f"{shot}_%04d.exr"),
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "slow",
        "-pix_fmt", "yuv420p",
        "-r", "24",
        out_path,
    ]

    if dry_run:
        return {
            "ok": True,
            "shot": shot,
            "stage": stage,
            "version": version,
            "frames": len(frames),
            "steps": ["exr_extract_layer × N", "burn_in_frame × N", "ffmpeg encode"],
            "burn_sample": f"{shot} {stage} {version}  frame={frame_start}  tc={_timecode(frame_start)}",
            "output": out_path,
            "cmd": " ".join(cmd),
            "dry_run": True,
        }

    try:
        subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return {
            "ok": False,
            "error": "找不到可用的 ffmpeg",
            "hint": "安装 ffmpeg，或在 PATH 中提供",
        }

    if not os.path.isdir(staging):
        os.makedirs(staging, exist_ok=True)
    extracted = []
    try:
        for src in frames:
            # ⚠️ staging 里的文件名必须与 ffmpeg 的 -i 模式严格对应
            #    （cmd 里是 {shot}_%04d.exr）。若沿用源文件名
            #    {shot}_{stage}_{version}.{frame}.exr 则两者不匹配，
            #    ffmpeg 报 "Could find no file with path"。
            n = int(os.path.basename(src).rsplit(".", 2)[-2])
            dst = os.path.join(staging, f"{shot}_{n:04d}.exr")
            r = exr_extract_layer(src, dst, "Combined", project_root)
            if not r["ok"]:
                return r
            # 逐帧烧录：帧号与时码随帧变化
            r = burn_in_frame(
                dst,
                dst,
                f"{shot} {stage} {version}  frame={n}  tc={_timecode(n)}",
            )
            if not r["ok"]:
                return r
            extracted.append(dst)

        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        err = e.stderr.decode() if e.stderr else str(e)
        # ffmpeg 报序列找不到时，把 staging 实际内容带出来，省一次往返
        if "Could find no file" in err or "No such file" in err:
            have = sorted(os.listdir(staging)) if os.path.isdir(staging) else []
            err += f" | staging 期望 {shot}_%04d.exr（从 {frame_start} 起），实际有: {have[:6]}"
        return {
            "ok": False,
            "error": f"ffmpeg 失败: {err[:500]}",
            "hint": "检查 staging 文件名是否与 -i 的 %04d 模式一致、序列是否连续、磁盘空间",
        }
    finally:
        for p in extracted:
            try:
                os.remove(p)
            except OSError:
                pass
        if os.environ.get("REVIEW_KEEP_STAGING"):
            pass
        elif os.path.isdir(staging):
            try:
                os.rmdir(staging)
            except OSError:
                pass

    return {
        "ok": True,
        "shot": shot,
        "stage": stage,
        "version": version,
        "frames": len(frames),
        "output": out_path,
    }


def _argv() -> list:
    """
    只取 `--` 之后的参数。

    `blender -b --factory-startup --python review.py -- --create_preview ...`
    时 sys.argv 仍含 blender 自身的参数，直接交给 argparse 会报
    "unrecognized arguments"。
    """
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


p = argparse.ArgumentParser(prog="review.py")
p.add_argument("--create_preview", nargs=3, metavar=("SHOT", "VERSION", "STAGE"))
p.add_argument("--frame-range", nargs=2, type=int, metavar=("START", "END"))
p.add_argument("--project-root", default=".")
p.add_argument("--dry-run", action="store_true")
_a = p.parse_args(_argv())

if _a.create_preview:
    fs, fe = _a.frame_range if _a.frame_range else (1001, 1136)
    print(
        create_preview(
            *_a.create_preview,
            frame_start=fs,
            frame_end=fe,
            project_root=_a.project_root,
            dry_run=_a.dry_run,
        )
    )
else:
    p.print_help()
