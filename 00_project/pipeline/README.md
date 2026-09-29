# Pipeline 脚本

项目管线 Python 代码，纳入 Git 管理。

## 模块

| 文件 | 职责 |
|---|---|
| `asset.py` | 资产创建、发布、加载 |
| `shot.py` | 镜头创建、相机设置、渲染设置 |
| `cache.py` | 缓存导出与检查 |
| `review.py` | 审阅片生成 |
| `utils.py` | 通用工具函数 |

## 命令行示例

```bash
# 创建镜头
blender -b --python pipeline/shot.py -- create_shot --seq 040 --shot 020 --frame_start 1001 --frame_end 1136

# 发布资产
blender -b --python pipeline/asset.py -- publish_asset --asset chr_hero_default --version v003 --notes "修复肘部穿插"

# 导出缓存
blender -b --python pipeline/cache.py -- export_cache --shot seq040_sh020 --stage anim --version v002

# 生成审阅片
blender -b --python pipeline/review.py -- create_preview --shot seq040_sh020 --version v003
```

## 注意事项

- 所有路径使用项目根目录为基准的相对路径。
- 无界面渲染使用 `blender -b`，不要依赖交互式界面状态。
- 脚本输入必须可复现，输出必须幂等。
