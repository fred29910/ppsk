# 资产库

## 目录结构

```
05_assets/
├── chr/        # 角色
│   └── hero/
│       ├── wip/
│       └── publish/
├── env/        # 环境
├── prp/        # 道具
├── veh/        # 载具
└── lib/        # 共享材质、HDRI、节点组、GN 生成器
```

## 命名规范

资产：`<类型>_<名称>_<变体>`

- `chr_hero_default`
- `prp_car01_damaged`
- `env_cityStreetA`

## 发布流程

1. 在 `wip/` 中完成资产
2. 运行发布脚本（检查命名、缩放、贴图路径、ROM 测试、LookDev 审阅）
3. 自动复制到 `publish/v###/`
4. 写入元数据：版本号、作者、时间、变更说明

## Asset Browser

- Asset Library 指向 `05_assets/` 下的发布目录
- 分类：Characters、Environment、Props、Vehicles、FX、Materials、Node Groups、HDRI、Poses

## 检查清单

- [ ] 命名符合规范
- [ ] Scale = 1，无未应用缩放
- [ ] 贴图路径为相对路径且在项目内
- [ ] 绑定通过 ROM 测试
- [ ] 材质通过 LookDev 转台审阅
- [ ] 元数据已写入
