# 环境资产

## 目录结构

按区块拆分，再组合：

```
env_city/
├── building_lib.blend   # 模块化建筑件
├── block_A.blend
├── block_B.blend
├── street_A.blend
├── street_B.blend
└── city_master.blend    # 只做 Link 和布局
```

## 组合手段

- Collection Instance
- Asset Browser
- Linked Data
- Library Override
- Geometry Nodes

## 程序化生成

- 路网是生成器起点
- 生成器封装成节点组放进 `05_assets/lib/`
- 生成结果稳定后固化（Realize，或导出缓存）

## 检查清单

- [ ] 模块化拆分合理
- [ ] 引用关系正确
- [ ] LOD 已准备
- [ ] 生成器已封装
