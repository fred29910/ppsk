"""
镜头管线 API 示例（确定性函数）
实际实现需根据项目需求补充 bpy 操作。
"""

def create_shot(seq: str, shot: str, frame_start: int = 1001, frame_end: int = 1136) -> dict:
    """从镜头表创建目录和各环节 .blend"""
    shot_name = f"seq{seq}_sh{shot}"
    # TODO: 创建目录结构
    # TODO: 从模板创建 layout.blend / anim.blend / cfx.blend / fx.blend / light.blend / comp.blend
    return {
        "shot": shot_name,
        "frame_start": frame_start,
        "frame_end": frame_end,
        "status": "created",
    }


def setup_camera(shot: str) -> dict:
    """按 Project Bible 设置 Sensor、画幅遮罩"""
    # TODO: 设置相机参数
    return {"shot": shot, "status": "camera_setup"}


def setup_render(shot: str, stage: str) -> dict:
    """分辨率 / 帧率 / 色彩管理 / View Layer / Pass / 输出路径"""
    # TODO: 设置渲染参数
    return {"shot": shot, "stage": stage, "status": "render_setup"}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--create_shot", nargs=4, metavar=("SEQ", "SHOT", "START", "END"))
    parser.add_argument("--setup_camera", nargs=1, metavar=("SHOT",))
    parser.add_argument("--setup_render", nargs=2, metavar=("SHOT", "STAGE"))
    args = parser.parse_args()

    if args.create_shot:
        print(create_shot(*args.create_shot))
    elif args.setup_camera:
        print(setup_camera(args.setup_camera[0]))
    elif args.setup_render:
        print(setup_render(*args.setup_render))
