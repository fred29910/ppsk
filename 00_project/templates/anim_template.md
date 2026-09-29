# 动画模板说明

## 预置内容

- 帧率：24 fps
- 帧范围：按镜头表设定
- Collection 结构：
  - `GEO_` 场景
  - `RIG_` 角色绑定（Library Override）
  - `CTRL_` 动画控制器
  - `CAM_` 摄影机
- Action / NLA 管理可复用循环动作

## 使用方式

1. 从 Asset Browser 拖入场景和角色
2. 通过 `pipeline/asset.py` 的 `load_asset` 加载已发布资产
3. 按 Blocking → Blocking Plus → Spline → Polish 推进
4. 输出 Alembic 缓存

## 动画阶段

| 阶段 | 内容 | 审阅关注点 |
|---|---|---|
| Blocking | 关键姿势（Pose to Pose），Constant 插值 | 表演、构图、节奏 |
| Blocking Plus | 加细分帧（Breakdowns） | 动作逻辑 |
| Spline | Bezier 插值，调整 Timing、Spacing、Arcs、Overlap、Follow Through | 流畅度 |
| Polish | 手指、眼神、呼吸、微表情、衣服和头发次级动作 | 细节 |

## 检查清单

- [ ] 对白镜头先做口型（Visemes）
- [ ] 参考视频已放入镜头目录
- [ ] 缓存路径正确
- [ ] 输出 Alembic 缓存
