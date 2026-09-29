"""
审阅片生成示例
"""

import os
import subprocess


def create_preview(shot: str, version: str, stage: str = "light") -> dict:
    """FFmpeg 生成带烧录信息的审阅片"""
    review_dir = os.path.join("07_review", shot)
    os.makedirs(review_dir, exist_ok=True)

    input_pattern = os.path.join(
        "06_shots", shot, "render", stage, version, f"{shot}_{stage}_{version}.%04d.exr"
    )
    output_path = os.path.join(review_dir, f"{shot}_{stage}_{version}.mp4")

    # TODO: 实际调用 FFmpeg
    # cmd = [
    #     "ffmpeg", "-i", input_pattern,
    #     "-c:v", "libx264", "-crf", "18", "-preset", "slow",
    #     "-vf", f"drawtext=text='{shot} {stage} {version} %{{frame_num}}':...",
    #     output_path
    # ]
    # subprocess.run(cmd, check=True)

    return {"shot": shot, "stage": stage, "version": version, "path": output_path}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--create_preview", nargs=3, metavar=("SHOT", "VERSION", "STAGE"))
    args = parser.parse_args()

    if args.create_preview:
        print(create_preview(*args.create_preview))
