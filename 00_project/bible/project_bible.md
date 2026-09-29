# Project Bible

> 在打开 Blender 之前定稿，项目中途改规格代价极高。

## 技术规格

| 项目 | 建议值 / 示例 | 说明 |
|---|---|---|
| Blender 版本 | 5.2 LTS | 所有成员、所有渲染节点使用同一版本 |
| 分辨率 | 1920×1080 或 3840×2160 | 长片院线可用 DCI 2K |
| 画幅比 | 16:9 / 1.85:1 / 2.39:1 | Layout 阶段启用画幅遮罩 |
| 帧率 | 24 fps | 一旦定下不可更改 |
| 场景单位 | 公制，1 unit = 1 m | 影响模拟、景深、灯光衰减 |
| 帧号约定 | 镜头从 1001 开始，前后各留 8 帧 handles | 例：有效帧 1009–1128，实际渲染 1001–1136 |
| 色彩管理 | Linear EXR + AgX / Filmic | 全项目统一 |
| 渲染输出 | OpenEXR Multilayer | 16-bit Half Float（颜色）+ 32-bit（数据） |

## 色彩管理

- 工作色彩空间：Linear Rec.709 / Linear sRGB；跨软件协作可考虑 ACEScg
- 显示变换：AgX 或 Filmic，全项目统一
- 贴图色彩空间：Base Color 用 sRGB；Roughness、Metallic、Normal、Displacement 等用 Non-Color
- 渲染输出：EXR 保存场景线性数据，不烘入显示变换
- 交付色域：网络和电视用 Rec.709（Gamma 2.4）；院线用 DCI-P3；HDR 另行规划
- 如需 ACES，使用统一 OCIO 配置，通过环境变量 `OCIO` 分发

## 命名规范

| 类别 | 规则 | 示例 |
|---|---|---|
| 资产 | `<类型>_<名称>_<变体>` | `chr_hero_default` / `prp_car01_damaged` |
| 镜头 | `seq<三位>_sh<三位>` | `seq040_sh020` |
| 文件 | `<镜头或资产>_<环节>_v<三位>.blend` | `seq040_sh020_anim_v012.blend` |
| 渲染帧 | `<镜头>_<环节>_v<三位>.<四位帧号>.exr` | `seq040_sh020_light_v003.1001.exr` |
| 对象 | 用前缀区分用途 | `GEO_` / `RIG_` / `CTRL_` / `DEF_` / `MCH_` / `CAM_` / `LGT_` |

资产类型前缀：`chr` 角色、`env` 环境、`prp` 道具、`veh` 载具、`fx` 特效。

禁止使用 `final`、`final2`、`new` 这类名字。"定稿"是审批状态，不是文件名。
