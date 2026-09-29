# MCP 工具封装

把管线 API 暴露为 MCP 工具，供 AI Agent 调用。

## 推荐架构

```
LLM / Agent → Blender MCP → 管线 API → bpy
```

## 已封装的工具

| 工具 | 对应函数 | 说明 |
|---|---|---|
| `create_shot` | `shot.create_shot` | 按镜头表创建镜头文件 |
| `load_asset` | `asset.load_asset` | 链接已发布资产 |
| `setup_camera` | `shot.setup_camera` | 设置相机参数 |
| `setup_render` | `shot.setup_render` | 设置渲染参数 |
| `export_cache` | `cache.export_cache` | 导出缓存 |
| `create_preview` | `review.create_preview` | 生成审阅片 |

## 风险与约束

| 风险 | 对策 |
|---|---|
| LLM 生成的代码不确定 | 优先调用管线 API；生成脚本要存档 |
| MCP 可执行任意代码 | 只在本机或受信任环境运行；限制工具 |
| 误改已发布资产 | Agent 只对 wip/ 和自己镜头有写权限 |
| 创作决策被稀释 | Agent 负责搭建，创作决策留给人 |

## 适合交给 Agent 的任务

- "按镜头表创建 seq040 的全部镜头文件。"
- "把 Hero 放到 seq040_sh020 的街道中央，并加载已发布的最新版本。"
- "用城市生成器生成一条 500 米街道，放置 20 栋建筑。"
- "给这场戏套用 Night_Rain 灯光模板。"
- "检查 seq040 所有镜头的贴图缺失和帧范围，并生成报告。"
- "提交 seq040_sh020 灯光 v003 的渲染，帧范围 1001–1136。"
