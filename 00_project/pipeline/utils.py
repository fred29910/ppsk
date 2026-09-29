"""
通用工具函数
"""

import os
import re


def normalize_name(name: str) -> str:
    """规范命名：小写、下划线分隔"""
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_").lower()


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


def metadata_template(asset: str, version: str, author: str, notes: str = "") -> dict:
    """元数据模板"""
    return {
        "asset": asset,
        "version": version,
        "author": author,
        "notes": notes,
        "timestamp": "",  # TODO: 写入实际时间
    }
