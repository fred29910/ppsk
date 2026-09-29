# Project Bible

> 在打开 Blender 之前定稿，项目中途改规格代价极高。
> 锁定值已按 G0 实测结果填写；实测依据见 `g0_feasibility_report.md`。

## 技术规格

| 项目 | 设定值 | 说明 |
|---|---|---|
| Blender 版本 | **5.2.0 LTS** | 锁 patch。所有成员、所有渲染节点使用同一版本 |
| Blender build hash | **`fbe6228777e7`** | 首次部署实测值；不跨 patch 混用 |
| Blender 路径（本机） | `/opt/data/dev/blender-5.2.0-linux-x64/blender` | 渲染机需同版本同 hash |
| 分辨率 | **1920×1080**（16:9） | 降级档 1600×900（L3 触发时） |
| 画幅比 | 16:9（主）/ 9:16（Layout 留裁切安全框） | |
| 帧率 | **24 fps** | 一旦定下不可更改 |
| 场景单位 | 公制，1 unit = 1 m | 影响模拟、景深、灯光衰减 |
| 帧号约定 | 镜头从 **1001** 开始，前后各留 **8 帧 handles** | 有效帧 1009 起；6 秒镜 = 有效 1009–1152 / 渲染 1001–1160 |
| 快门角度 | **180°**（0.5 帧运动模糊） | |
| 渲染器 | **EEVEE**（默认）/ Cycles（仅 T2 反射雾等局部高精，CPU only） | Cycles 实测可用，见 g0 报告 §2.1 |
| 渲染输出 | **OpenEXR Multilayer** | 颜色 16-bit Half；数据 Pass 32-bit |
| 传感器宽度 | 36 mm（全片统一） | 否则焦距含义会变 |

## 色彩管理（四元组，锁定）

| 项 | 值 |
|---|---|
| 工作色彩空间 | **Scene Linear（Rec.709 primaries）** |
| 显示变换 | **AgX** |
| 显示设备 | **sRGB** |
| Look | **None**（per-shot 风格化另开记录，不全局改） |
| 渲染输出 | EXR 保存场景线性，**不烘入显示变换** |
| 交付色域 | Rec.709 |

> AgX 会对高亮高饱和色去饱和，法术自发光易发白 → per-shot 换 View Transform
> 或后期提饱和。见 `g0_feasibility_report.md` §5（T4 未完成，风险未排除）。

## Blender 5.2 API 约束（G0 实测，务必遵守）

| 约束 | 说明 |
|---|---|
| 引擎 ID 是 `BLENDER_EEVEE` | 不是 `BLENDER_EEVEE_NEXT` |
| **不要用 `engine` 静态枚举判断 Cycles 可用性** | `-b` 无界面模式下枚举只注册 EEVEE，即使 Cycles addon 已启用。直接赋值 `'CYCLES'`，判据是 `hasattr(scene,'cycles')` |
| **EXR multilayer 必须先设 `media_type`** | `media_type='MULTI_LAYER_IMAGE'` → 再 `file_format='OPEN_EXR_MULTILAYER'`。反了报枚举不存在 |
| **EEVEE 没有 Volume Pass** | 无 `use_pass_volume`。雾无法靠 Pass 分离 → 支持 §2.2 "雾主要走合成层" |
| Workbench 在 `-b` 下全黑 | 无 GL 上下文，不可用于自动化检查 |
| ffmpeg 读不了 multilayer EXR | `create_preview` 必须先 `exr_extract_layer()` 抽层 |
| Python OpenEXR 绑定缺失 | 逐像素读 EXR 走 Blender bpy |

## 云雾双轨方案（沿用 plan.md §2.2）

| 轨 | 用途 | 实现 |
|---|---|---|
| 渲染器体积 | 近景、人物周围的仙气、可见光柱 | EEVEE Volumetrics |
| 合成雾 | 远景山岚、云海、大气透视 | Depth + Mist + Fog Glow（Compositor / Resolve） |

G0 实测确认 §2.2 限制成立：EEVEE 的雾**不进入反射/折射**（EEVEE 雾贡献 +0.178
反而大于 Cycles 的 +0.058，说明反射中确实没有雾）。水面/古镜中的雾若必须存在，
走 Cycles 局部渲染。

## 命名规范

| 类别 | 规则 | 示例 |
|---|---|---|
| 资产 | `<类型>_<名称>_<变体>`（类型 ∈ chr/env/prp/veh/fx） | `chr_hero_meditation` |
| 镜头 | `seq<三位>_sh<三位>`，**sh 从 010 开始，不用 001/005** | `seq010_sh010` |
| 文件 | `<镜头或资产>_<环节>_v<三位>.blend` | `seq010_sh010_anim_v012.blend` |
| 渲染帧 | `<镜头>_<环节>_v<三位>.<四位帧号>.exr` | `seq010_sh010_light_v003.1001.exr` |
| 缓存 | `cache/<阶段>/v<三位>/` | `cache/cfx/v002/cloth_hero.abc` |
| 渲染目录 | `render/<阶段>/v<三位>/` | `render/light/v003/` |
| 审阅片 | `<镜头>_<阶段>_v<三位>_burn.mp4` | `seq010_sh010_light_v003_burn.mp4` |
| 对象 | 前缀区分用途 | `GEO_` `RIG_` `CTRL_` `DEF_` `MCH_` `CAM_` `LGT_` |

资产类型前缀：`chr` 角色、`env` 环境、`prp` 道具、`veh` 载具、`fx` 特效。

**禁止**使用 `final`、`final2`、`new` 这类名字。"定稿"是审批状态，不是文件名。

## 本机工具现状（G0 实测）

| 工具 | 状态 |
|---|---|
| Blender 5.2.0 | ✅ `/opt/data/dev/blender-5.2.0-linux-x64/blender` |
| Cycles | ✅ 可用（**CPU only**，`compute_device_type` 枚举为空） |
| EEVEE headless | ✅ 可用 |
| ffmpeg / ffprobe | ✅ 可用（需先抽 EXR 层） |
| GPU | 🔴 **无**（`nvidia-smi` 不存在）→ 本机不是渲染机 |
| CPU | 20 核 |
| DaVinci Resolve | 🔴 **缺失** → T5 色彩全链路阻塞 |
| Python OpenEXR | 🔴 缺失 → 走 bpy 读回 |

## 待办

- [ ] 渲染机确认同版本同 build hash
- [ ] 渲染机补做 T3 / T4 / T5 / T6 Pass 齐全性
- [ ] `project_bible.md` 与 `docs/plan.md` 的 5.2.1 表述同步（本文件为准）

## 修订记录

| 日期 | 变更 |
|---|---|
| 2026-09-29 | 锁定版本由 plan.md 的 5.2.1 改为实测的 **5.2.0**；写入 build hash；填入色彩四元组、帧号推导、5.2 API 约束、本机工具现状 |
