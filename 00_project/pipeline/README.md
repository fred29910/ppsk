# Pipeline 脚本

项目管线 Python 代码，纳入 Git 管理。

## 模块

| 文件 | 职责 |
|---|---|
| `asset.py` | 资产创建、发布、加载 |
| `shot.py` | 镜头创建、相机设置、渲染设置 |
| `cache.py` | 缓存导出与检查 |
| `review.py` | 审阅片生成 |
| `build_templates.py` | 生成 6 个环节模板 `.blend`（需 Blender；`asset.py` / `cache.py` 仍是 `# TODO` 空壳） |
| `utils.py` | 通用工具函数 + **规格值唯一来源** |
| `shotlist.csv` | 真实镜头表，帧范围与 per-shot View Transform 的数据来源（只读） |

## 命令行示例

⚠️ 参数一律写在 `--` 之后（Blender 自己的 argv 会被 argparse 拒收）。
帧范围取自 `shotlist.csv`，`--setup_render` / `--create_preview` **必填** ——
缺失会直接返回 `ok:False`，不会落回模板占位范围。

```bash
# 创建镜头目录骨架
blender -b --factory-startup --python pipeline/shot.py -- \
    --create_shot 010 010 1001 1160 --project-root ../..

# 套用渲染设置（帧范围必填）
blender -b --factory-startup --python pipeline/shot.py -- \
    --setup_render seq010_sh010 light --frame-range 1001 1160 --project-root ../..

# 关键 FX 镜头换 per-shot View Transform（shotlist.csv 的 view_transform 列）
blender -b --factory-startup --python pipeline/shot.py -- \
    --setup_render seq010_sh020 light --frame-range 1001 1136 \
    --view-transform "Khronos PBR Neutral" --project-root ../..

# 生成 6 个环节模板 .blend（需在 Blender 内；不加 --apply 只报告计划）
blender -b --factory-startup --python pipeline/build_templates.py -- \
    --project-root ../.. --apply

# 生成审阅片
blender -b --factory-startup --python pipeline/review.py -- \
    --create_preview seq010_sh010 v001 light --frame-range 1001 1160 --project-root ../..
```

## 退出码

`blender -b --python X.py` 抛未捕获异常时**退出码仍是 0**，只有显式
`sys.exit(N)` 才传播。所以三个入口脚本的 `main()` 都返回 `0` / `1`：
`ok:False` 一律退出 1。**验收看输出文本，不看退出码**（两边都看）。

## 注意事项

- 所有路径使用项目根目录为基准的相对路径。
- 无界面渲染使用 `blender -b`，不要依赖交互式界面状态。
- 脚本输入必须可复现，输出必须幂等。
