# 镜头目录

## 目录结构

```
06_shots/
└── seq040/
    └── sh020/
        ├── layout/      # Layout / Previs
        ├── anim/        # 角色动画
        ├── cfx/         # 布料 / 毛发
        ├── fx/          # 特效
        ├── light/       # 灯光与渲染
        ├── comp/        # 合成
        ├── cache/       # abc / usd / vdb / 点缓存
        │   └── <阶段>/v<版本>/
        └── render/      # EXR 序列
            └── <阶段>/v<版本>/
```

## 命名规范

- 镜头：`seq040_sh020`
- 文件：`seq040_sh020_anim_v012.blend`
- 渲染帧：`seq040_sh020_light_v003.1001.exr`

## 流程

1. Layout 使用代理或粗模尽早开工
2. 动画使用 Link + Library Override 引用已发布资产
3. 动画输出 Alembic 缓存
4. CFX / FX / Light 读取缓存，不依赖绑定
5. 灯光文件只负责灯光和渲染设置

## 版本控制

- 每个环节独立版本号，只增不减
- 缓存版本号与源文件版本对应
- 每次提交生成审阅片（MP4），放入 `07_review/`

## 检查清单

- [ ] 帧范围正确（1001 ± 8 frames handles）
- [ ] 资产引用已发布版本
- [ ] 缓存路径使用相对路径
- [ ] 输出路径正确
- [ ] 审阅片已生成
