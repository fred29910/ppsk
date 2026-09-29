"""
缓存导出与检查示例
"""

import os


def export_cache(shot: str, stage: str, version: str = "v001") -> dict:
    """导出 Alembic / VDB 到版本化目录"""
    cache_dir = os.path.join("06_shots", shot, "cache", stage, version)
    # TODO: blender -b --python export_cache.py
    return {"shot": shot, "stage": stage, "version": version, "path": cache_dir}


def check_cache(shot: str, stage: str, version: str = "v001") -> dict:
    """检查缓存是否完整"""
    cache_dir = os.path.join("06_shots", shot, "cache", stage, version)
    # TODO: 检查文件是否存在、帧范围是否正确
    return {"shot": shot, "stage": stage, "version": version, "status": "checked"}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--export_cache", nargs=3, metavar=("SHOT", "STAGE", "VERSION"))
    parser.add_argument("--check_cache", nargs=3, metavar=("SHOT", "STAGE", "VERSION"))
    args = parser.parse_args()

    if args.export_cache:
        print(export_cache(*args.export_cache))
    elif args.check_cache:
        print(check_cache(*args.check_cache))
