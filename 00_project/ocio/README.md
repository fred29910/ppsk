# OCIO 配置

将项目使用的 OCIO 配置文件放在此处，并通过环境变量 `OCIO` 分发给所有机器。

```
export OCIO=/path/to/project/00_project/ocio/config.ocio
```

## 建议结构

```
ocio/
├── config.ocio          # 主配置
├── luts/                # LUT 文件
└── colorspaces/         # 自定义色彩空间定义
```

## 检查清单

- [ ] 所有节点使用同一 OCIO 配置
- [ ] Blender 渲染节点和合成节点色彩空间一致
- [ ] 跨软件协作（如 Nuke、Houdini）已测试
