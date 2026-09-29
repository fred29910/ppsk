# FX 模板说明

## 类型与方案

| 类型 | Blender 方案 |
|---|---|
| 烟、火 | Mantaflow Gas |
| 液体 | Mantaflow Liquid / Ocean Modifier |
| 爆炸、破碎 | Rigid Body + Cell Fracture |
| 雨、雪、灰尘、碎屑、魔法 | Geometry Nodes（含 Simulation Zone）/ 粒子系统 |
| 体积雾 | 体积材质 / VDB |

## 使用方式

1. 从 `05_assets/lib/fx/` 加载预设
2. 在镜头中调参数
3. 运行模拟
4. 输出 VDB 缓存

## 检查清单

- [ ] 预设已加载
- [ ] 参数已调整
- [ ] 模拟已运行
- [ ] 缓存已输出
- [ ] 缓存路径正确
