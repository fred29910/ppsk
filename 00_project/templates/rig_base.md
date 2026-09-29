# 角色绑定基础

## Rigify 元骨骼

使用 Rigify（Blender 自带）作为起点。

## 骨骼分层

| 前缀 | 用途 |
|---|---|
| `DEF-` | 变形骨，蒙皮权重只绑在这些骨骼上 |
| `ORG-` | 原始参考骨 |
| `MCH-` | 机制骨（约束、中间计算） |
| 无前缀 / `CTRL` | 动画师操作的控制器 |

## 基础层级

```
root
└── torso / hips
    └── spine
        └── chest
            ├── neck
            │   └── head
            ├── shoulder.L
            │   └── upper_arm.L
            │       └── forearm.L
            │           └── hand.L
            │               └── fingers.L
            └── shoulder.R（镜像）
    └── thigh.L
        └── shin.L
            └── foot.L
                └── toe.L
    └── thigh.R（镜像）
```

## 必备功能

- IK/FK 切换与对齐（Snap）
- Pole Target
- 空间切换（Space Switch）
- Drivers
- Custom Properties
- Bone Collections 分组

## 面部口型集（Visemes）

- A/I、E、O、U
- M/B/P、F/V、L、W/Q

## 检查清单

- [ ] 骨骼命名规范
- [ ] 层级结构稳定
- [ ] IK/FK 切换正常
- [ ] 口型集完整
- [ ] ROM 测试通过
