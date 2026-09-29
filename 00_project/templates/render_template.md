# 渲染设置预设

## View Layer 分层

| View Layer | 用途 |
|---|---|
| `VL_char` | 角色（其余物体 Holdout / Indirect Only） |
| `VL_env` | 环境 |
| `VL_fx` | 特效 |
| `VL_fog` | 体积雾 |
| `VL_shadow` | 投影（Shadow Catcher） |

## Pass

- Combined（Beauty）
- Diffuse / Glossy / Transmission（Direct / Indirect / Color）
- Emission / Environment / Volume
- Shadow Catcher
- Depth（Z）/ Mist
- Normal / Position
- Cryptomatte（Object / Material / Asset）
- Denoising Data

## EXR 输出

- 格式：OpenEXR Multilayer
- 位深：颜色 16-bit Half Float；数据 32-bit
- 压缩：DWAA（颜色）/ ZIP（数据）
- 色彩：场景线性，不烘入显示变换
- 命名：`render/<stage>/v<版本>/<shot>_<stage>_v<版本>.<帧号>.exr`

## 检查清单

- [ ] 帧率 24 fps
- [ ] 分辨率正确
- [ ] 色彩管理统一
- [ ] 输出路径使用相对路径
- [ ] 采样设置合理
- [ ] 降噪设置已启用
