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

## 色彩管理（四元组，锁定 + per-shot 例外）

| 项 | 值 |
|---|---|
| 工作色彩空间 | **Scene Linear（Rec.709 primaries）** |
| 显示变换（默认） | **AgX** |
| 显示变换（**关键 FX 镜头**） | **Khronos PBR Neutral** —— 见下 |
| 显示设备 | **sRGB** |
| Look | **None**（per-shot 风格化另开记录，不全局改） |
| 渲染输出 | EXR 保存场景线性，**不烘入显示变换** |
| 交付色域 | Rec.709 |

### per-shot View Transform（G0-T4 实测结论）

**AgX 会让青色系自发光发白。** 实测数据（strength=1.0，`orb_mid` `#40c8ff`）：

| View Transform | R | G | B | 饱和度 | 判定 |
|---|---|---|---|---|---|
| **AgX** | 0.643 | 0.749 | 0.773 | **0.168** | ✗ 发白 |
| Khronos PBR Neutral | 0.573 | 0.878 | 0.937 | **0.389** | ✓ |

5 档 Emission Strength（0.5/1/2/4/8）× 3 种 View Transform 实测：
AgX 全部档位发白 2–6/7，Khronos PBR Neutral 同强度只发白 1–3/7。
**同强度换 transform 就能救回来 → 是 View Transform 问题，不是强度问题。**

| 镜头 | FX | View Transform |
|---|---|---|
| sh010 | fx_dust_sparkle（暖金） | AgX |
| **sh020** | **fx_magic_orb（青）** | **Khronos PBR Neutral** |
| **sh030** | **fx_sword_trail（黄/橙）** | **Khronos PBR Neutral** |
| **sh040** | **fx_sword_trail** | **Khronos PBR Neutral** |
| sh050 | fx_dust_sparkle（暖金） | AgX |

已落到 `00_project/pipeline/shotlist.csv` 的 `view_transform` 列，
`setup_render` 支持 `--view-transform` 覆盖。

**代价与对策**：FX 镜头与相邻镜头色调会不连续，**调色阶段（§8.2 Grade）
必须把 FX 镜头往 AgX 基准靠**。这是本项目"同一场内两种显示变换"的已知代价。

> 详细数据见 `g0_feasibility_report.md` §4。


## Blender 5.2 API 约束（G0 实测，务必遵守）

| 约束 | 说明 |
|---|---|
| 引擎 ID 是 `BLENDER_EEVEE` | 不是 `BLENDER_EEVEE_NEXT` |
| **不要用 `engine` 静态枚举判断 Cycles 可用性** | `-b` 无界面模式下枚举只注册 EEVEE，即使 Cycles addon 已启用。直接赋值 `'CYCLES'`，判据是 `hasattr(scene,'cycles')` |
| **不要用 `view_transform` 静态枚举做校验** | 同样陷阱：headless 下枚举只有 `['NONE']`。直接赋值 + 读回核对 |
| **EXR multilayer 必须先设 `media_type`** | `media_type='MULTI_LAYER_IMAGE'` → 再 `file_format='OPEN_EXR_MULTILAYER'`。反了报枚举不存在 |
| **帧序列占位符用 `#` 不是 `%04d`** | `%04d` 会被当普通字符，产出 `xxx.%04d.exr0023.exr` 双扩展名 |
| **EEVEE 没有 Volume Pass** | 无 `use_pass_volume`。雾无法靠 Pass 分离 → 支持 §2.2 "雾主要走合成层" |
| **合成器在 headless 下会崩** | `CompositorNodeImage` 渲染即崩（连 pass-through 也崩）。`scene.node_tree` → `compositing_node_group`；`CompositorNodeComposite` 节点已不存在。烧录改走 VSE |
| VSE：`sequences` → `strips` | `new_effect` 参数是 `length` 不是 `frame_end`；文字 `location` 原点在**左下** |
| `bpy.data.images.load` 读不了 multilayer EXR | 返回 size (0,0)。用 Blender 自带 `OpenImageIO`（3.1.13.1），通道名形如 `ViewLayer.Combined.R` |
| EXR 不含显示变换 | 评 View Transform 必须在**渲染时**套上再读 PNG；读 EXR 拿不到。且 bpy 的 `image.pixels` 也不套用 |
| 本机 ffmpeg 无 `drawtext` | 静态构建无 libfreetype。烧录走 Blender VSE（§6.1 要求） |
| Workbench 在 `-b` 下全黑 | 无 GL 上下文，不可用于自动化检查 |

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
- [ ] 渲染机补做 T3（10k 实例 GN 散布 + 计时）、T5（色彩全链路，需 Resolve）
- [ ] 调色阶段把 FX 镜头（Khronos）往 AgX 基准靠，保色调连续
- [ ] 色彩脚本补记 per-shot View Transform 决策（§9.3 要求）
- [ ] 美术设定补图（W1 要求的是图，当前只有文字描述）

## 修订记录

| 日期 | 变更 |
|---|---|
| 2026-09-29 | 锁定版本由 plan.md 的 5.2.1 改为实测的 **5.2.0**；写入 build hash；填入色彩四元组、帧号推导、5.2 API 约束、本机工具现状 |
| 2026-09-29 | G0-T4 补测完成：**AgX 让青色自发光发白**（饱和度 -0.40），关键 FX 镜头 per-shot 换 Khronos PBR Neutral。已落 shotlist `view_transform` 列 + `setup_render --view-transform`。补充合成器崩溃、VSE API、OIIO 读 EXR 等 5.2 约束 |
