"""
资产管线 API 示例（确定性函数）
实际实现需根据项目需求补充 bpy 操作。
"""

def create_asset(type_: str, name: str, variant: str = "default") -> dict:
    """按模板创建 wip 目录和文件"""
    asset_name = f"{type_}_{name}_{variant}"
    # TODO: 创建 wip/ 目录和 .blend 模板文件
    return {"asset": asset_name, "status": "created"}


def publish_asset(asset: str, notes: str = "") -> dict:
    """执行检查、复制到 publish/v###、写元数据"""
    # TODO: 检查命名、缩放、贴图路径、ROM 测试、LookDev 审阅
    # TODO: 复制到 publish/v###/
    # TODO: 写入元数据
    return {"asset": asset, "version": "v001", "status": "published"}


def load_asset(shot: str, asset: str, version: str = "latest") -> dict:
    """Link + Library Override + 规范命名"""
    # TODO: Link 资产文件
    # TODO: 创建 Library Override
    # TODO: 规范命名
    return {"shot": shot, "asset": asset, "version": version, "status": "loaded"}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--create_asset", nargs=3, metavar=("TYPE", "NAME", "VARIANT"))
    parser.add_argument("--publish_asset", nargs=1, metavar=("ASSET",))
    parser.add_argument("--load_asset", nargs=2, metavar=("SHOT", "ASSET"))
    args = parser.parse_args()

    if args.create_asset:
        print(create_asset(*args.create_asset))
    elif args.publish_asset:
        print(publish_asset(args.publish_asset[0]))
    elif args.load_asset:
        print(load_asset(*args.load_asset))
