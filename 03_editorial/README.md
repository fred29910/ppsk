# 剪辑

## 内容

- 剪辑工程
- Animatic
- EDL / OTIO

## 工具

- Blender VSE
- DaVinci Resolve

## 流程

1. Animatic 阶段配上临时对白、临时音乐
2. 输出镜头清单（Shot List）
3. 故事锁定（Story Lock）后，Layout 替代 Animatic
4. 每个环节的新版本都替换回剪辑时间线
5. 画面锁定（Picture Lock）后 Conform

## 命名规范

```
03_editorial/
├── animatic/
│   └── mymovie_animatic_v003.blend
├── editorial/
│   └── mymovie_edit_v012.blend
└── exports/
    └── mymovie_edit_v012.xml
```

## 检查清单

- [ ] 镜头列表已输出
- [ ] 时长与 Animatic 一致
- [ ] 对白时间码正确
- [ ] EDL / OTIO 已导出
