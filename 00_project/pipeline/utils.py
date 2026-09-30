"""
通用工具函数

项目规格常量也放在这里，pipeline 各模块与 project_bible.md 保持一致。
"""

import os
import re
import sys

# ---- 锁定规格（Blender 5.2.0，build fbe6228777e7）----
BLENDER_VERSION = "5.2.0"
BLENDER_BUILD_HASH = "fbe6228777e7"
FPS = 24
RESOLUTION = (1920, 1080)
HANDLE_FRAMES = 8
FRAME_START = 1001
SHUTTER_ANGLE = 180.0    # 度。写进 Blender 时必须过 shutter_frames() 换算
SENSOR_WIDTH = 36.0      # mm，全片统一（project_bible.md 锁定）

# 色彩管理四元组
VIEW_TRANSFORM = "AgX"
LOOK = "None"
DISPLAY_DEVICE = "sRGB"
COLOR_SPACE = "Scene Linear (Rec.709)"

_ASSET_TYPES = ("chr", "env", "prp", "veh", "fx")
_NAME_RE = re.compile(r"^(chr|env|prp|veh|fx)_[a-z0-9]+(_[a-z0-9]+)?$")


REQUIRED_VERSION_PREFIX = ".".join(BLENDER_VERSION.split(".")[:2])


def shutter_frames() -> float:
    """快门角度（度）→ Blender 的 motion_blur_shutter（帧）。180° → 0.5 帧。

    ⚠️ 单位是帧不是角度。直接写 180.0 会得到 180 帧的运动模糊且**不报错**。
    """
    return SHUTTER_ANGLE / 360.0


def check_blender_version(strict: bool = True) -> dict:
    """
    启动即校验 Blender 版本。

    project_bible.md 锁定 5.2.0 / build fbe6228777e7。
    版本不符时按 §12.1 约定直接退出。
    """
    try:
        import bpy
    except ImportError:
        return {
            "ok": False,
            "error": "不在 Blender 环境中",
            "hint": f"blender -b --factory-startup --python {sys.argv[0]} ...",
        }

    ver = bpy.app.version_string.split()[0]
    bh = bpy.app.build_hash
    bh = bh.decode() if isinstance(bh, bytes) else bh

    if not ver.startswith(REQUIRED_VERSION_PREFIX + "."):
        msg = f"Blender 版本不符: {ver} 需 {REQUIRED_VERSION_PREFIX}.x"
        if strict:
            raise SystemExit(f"[FATAL] {msg}\n  项目锁 {BLENDER_VERSION}，不跨 major.minor 混用")
        return {"ok": False, "error": msg, "hint": "改 BLENDER_VERSION 或用正确版本"}

    # build hash 不同**不失败**：本机是 dev build，官方 5.2.0 发行版 hash 必然不同
    warnings = []
    if bh != BLENDER_BUILD_HASH:
        warnings.append(
            f"build hash 与记录不符: 记录 {BLENDER_BUILD_HASH}，实际 {bh}；"
            f"继续执行但请确认渲染机一致"
        )
    return {"ok": True, "version": ver, "build_hash": bh, "warnings": warnings}


def normalize_name(name: str) -> str:
    """规范命名：小写、下划线分隔"""
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_").lower()


def validate_asset_name(name: str) -> dict:
    """资产命名：<类型>_<名称>_<变体>，类型限 chr/env/prp/veh/fx"""
    n = normalize_name(name)
    if not _NAME_RE.match(n):
        return {
            "ok": False,
            "error": f"命名不合规: {name}",
            "hint": f"应为 <类型>_<名称>_<变体>，类型 ∈ {_ASSET_TYPES}，例 chr_hero_meditation",
        }
    return {"ok": True, "name": n}


def next_version(publish_dir: str) -> str:
    """返回下一个版本号 v001, v002, ..."""
    if not os.path.exists(publish_dir):
        return "v001"
    versions = [d for d in os.listdir(publish_dir) if re.match(r"^v\d+$", d)]
    if not versions:
        return "v001"
    max_version = max(versions, key=lambda v: int(v[1:]))
    return f"v{int(max_version[1:]) + 1:03d}"


def ensure_relative_path(path: str, project_root: str) -> str:
    """确保路径是项目根目录下的相对路径"""
    return os.path.relpath(path, project_root)


def check_scale(obj) -> bool:
    """检查对象缩放是否为 1"""
    return all(abs(s - 1.0) < 1e-5 for s in obj.scale)


def frame_range(duration_s: float) -> dict:
    """
    帧号推导：镜头从 1001 起，前后各留 8 帧 handles。

    例：6 秒 → 有效帧 1009–1152，渲染帧 1001–1160
    """
    valid = int(round(duration_s * FPS))
    return {
        "shot_start": FRAME_START + HANDLE_FRAMES,
        "shot_end": FRAME_START + HANDLE_FRAMES + valid - 1,
        "frame_start": FRAME_START,
        "frame_end": FRAME_START + HANDLE_FRAMES + valid - 1 + HANDLE_FRAMES,
    }


def metadata_template(asset: str, version: str, author: str, notes: str = "") -> dict:
    """元数据模板"""
    return {
        "asset": asset,
        "version": version,
        "author": author,
        "notes": notes,
        "blender_version": BLENDER_VERSION,
        "blender_build_hash": BLENDER_BUILD_HASH,
    }


def make_object_name(prefix: str, name: str) -> str:
    """对象名：保留 dls.md 规定的大写前缀，如 CAM_cam / GEO_grayball。

    资产 ID 才用 normalize_name（小写下划线）。两者不可混用：
    normalize_name 会转小写，用它处理对象名会得到 geo_grayball，
    违反命名规范。
    """
    clean = re.sub(r"[^A-Za-z0-9_]", "_", name)
    clean = re.sub(r"_+", "_", clean).strip("_")
    return f"{prefix}_{clean}" if clean else prefix
