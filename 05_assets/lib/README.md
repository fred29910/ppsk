# 共享资产库

## 内容

- 共享材质
- HDRI
- 节点组
- GN 生成器
- FX 预设
- 灯光模板（Light Rig）

## 分类

- Materials
- Node Groups
- HDRI
- GN Generators
- FX Presets
- Light Rigs
- Poses

## 使用方式

1. 将资产放入对应分类目录
2. 在 Blender 中标记为 Asset
3. 通过 Asset Browser 拖入使用

## 示例

```
05_assets/lib/
├── materials/
│   ├── skin_base.blend
│   └── metal_paint.blend
├── hdri/
│   ├── studio_01.hdr
│   └── outdoor_02.hdr
├── node_groups/
│   ├── building_generator.blend
│   └── window_generator.blend
├── fx/
│   ├── smoke_preset.blend
│   └── rain_preset.blend
└── light_rigs/
    ├── Night_Rain.blend
    └── Day_Sunny.blend
```

## 检查清单

- [ ] 资产已标记为 Asset
- [ ] 命名符合规范
- [ ] 路径为相对路径
- [ ] 测试可正常加载
