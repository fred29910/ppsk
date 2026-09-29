# 仙侠类动画 Demo 开发计划

> **目标**：基于 `docs/dls.md` 管线规范，规划一部 **1–3 分钟仙侠题材 3D 动画短片（Demo）** 的开发计划。  
> **适用范围**：个人或 2–3 人小团队，以 Blender 为核心 DCC，优先纯 Blender 方案。  
> **锁定版本**：Blender **5.2 LTS**，项目中途不升级。

---

## 1. 项目定位与规模

| 项目 | 设定值 | 说明 |
|---|---|---|
| 片长 | **1–3 分钟** | Demo 级别，用于验证管线与风格 |
| 分辨率 | 1920×1080 | 网络发行，节省渲染预算 |
| 帧率 | 24 fps | 锁定，不可更改 |
| 渲染器 | **Eevee Next** | 仙侠风格化适合光栅化，预算有限时优先 Eevee；若需要体积雾精度可局部混用 Cycles |
| 色彩管理 | Linear Rec.709 + AgX | 全项目统一，不烘入显示变换 |
| 对白 | **无对白 / 仅环境音** | 省略口型与对白录制，把精力放在视觉表演上 |
| 主要角色 | **1–2 个** | 一位主角（仙师/侠客）+ 一位师父或灵兽，大量复用资产 |
| 场景 | **2–3 个** | 例如：竹林入门 → 云海山巅 → 古殿秘境 |

---

## 2. 题材拆解：仙侠核心视觉要素

| 要素 | 实现要点 | Blender 方案 |
|---|---|---|
| **古风角色** | 宽袖长袍、发髻束带、佩剑/拂尘 | Rigify 绑定 + Hair Curves 发型 + Cloth 布料模拟 |
| **法术特效** | 飞剑、剑气、光球、符纸、阵纹 | Geometry Nodes + Mantaflow（烟/雾）+ 粒子系统（光屑） |
| **云雾/大气** | 云海、山岚、仙气缭绕 | Volume / VDB + Mantaflow Gas + GN Simulation |
| **古风场景** | 山石、竹林、栈道、古殿、飞檐 | 程序化生成（GN）+ 现成资产库（Poly Haven / Quixel） |
| **武器/法宝** | 飞剑、古镜、葫芦、符纸 | 道具建模 + 简单绑定 + FX 动画 |
| **风格化光影** | 逆光剪影、月光、灵光、体积雾 | Eevee Next + Volumetrics + Light Linking |
| **表演风格** | 飘逸的轻功、御剑飞行、打坐、拂尘挥动 | 动作参考（实拍 / AI 单目动捕）+ 手动精修 |

---

## 3. 目录结构与命名规范

采用 `dls.md` 第 3 节统一目录，并扩展仙侠专用资产分类：

```text
XianxiaDemo/
├── 00_project/
│   ├── bible/
│   ├── ocio/
│   ├── pipeline/
│   └── templates/
├── 01_story/
├── 02_storyboard/
├── 03_editorial/
├── 04_audio/            # 环境音 / 音乐 / 无对白
├── 05_assets/
│   ├── chr/
│   │   └── hero/        # 主角 + 师父
│   ├── env/
│   │   ├── bamboo_forest/
│   │   ├── cloud_peak/
│   │   └── ancient_hall/
│   ├── prp/
│   │   ├── flying_sword/
│   │   ├── feather_fan/
│   │   └── talisman/
│   ├── fx/              # 可复用特效预设
│   │   ├── sword_trail/
│   │   ├── magic_orb/
│   │   ├── cloud_vol/
│   │   └── dust_sparkle/
│   └── lib/             # 共享材质、HDRI、GN 生成器
├── 06_shots/
│   └── seq010/           # 单场景，分 5–8 个镜头
│       ├── sh010_layout/
│       ├── sh010_anim/
│       ├── sh010_cfx/
│       ├── sh010_fx/
│       ├── sh010_light/
│       ├── sh010_comp/
│       └── cache/
├── 07_review/
├── 08_delivery/
└── 09_archive/
```

**命名规范**：
- 资产：`<类型>_<名称>_<变体>`，如 `chr_hero_meditation`、`prp_flying_sword_glow`
- 镜头：`seq<三位>_sh<三位>`，如 `seq010_sh010`
- 文件：`<镜头或资产>_<环节>_v<三位>.blend`
- 渲染帧：`<镜头>_<环节>_v<三位>.<四位帧号>.exr`

---

## 4. 分期计划（3 个月 Demo）

### 4.1 第一阶段：前期制作（第 1–4 周）

| 周次 | 任务 | 产出 | 负责人 |
|---|---|---|---|
| W1 | 剧本定稿 / 分镜脚本 / 情绪板 | 完整 Storyboard（5–8 镜头）、色彩脚本 | 导演 / 编剧 |
| W1–W2 | 美术设定 | 主角三视图、服装配色、场景气氛图、特效风格参考 | 原画 / 设定 |
| W2–W3 | Animatic + 剪辑 | Blender VSE 剪辑 + 临时音乐 + 镜头时码 | 剪辑 / 导演 |
| W3–W4 | 故事锁定 + 镜头表 | Shot List（镜头号、帧范围、角色、场景、FX、灯光方案） | 制片 / 导演 |

**关键里程碑**：Story Lock — 锁定分镜、时长和镜头表。

---

### 4.2 第二阶段：资产制作（第 3–8 周）

与前期后半程并行。每个资产走 `dls.md` 5.1 节流程。

#### 4.2.1 角色资产（第 3–6 周）

| 周次 | 任务 | 产出 |
|---|---|---|
| W3–W4 | 主角建模 + 雕刻 + 拓扑 | 动画模型（约 3–5 万面） |
| W4–W5 | UV + Bake + Texture | 基础材质贴图 |
| W5 | LookDev + 转台审阅 | 通过后发布 `publish/v001` |
| W5–W6 | Rigify 身体绑定 + 面部口型集 | ROM 测试通过 |
| W6 | Hair Curves + Cloth 资产设置 | 披风/发丝初始模拟参数 |

#### 4.2.2 环境资产（第 5–8 周）

| 周次 | 任务 | 产出 |
|---|---|---|
| W5–W6 | 竹林 / 云海 / 古殿 建模 | 按区块拆分的模块化资产 |
| W6–W7 | 程序化生成器（GN） | 竹子散布、山石阵列、建筑组合生成器 |
| W7–W8 | 灯光模板预设 | `Night_Moon`、`Cloud_Day`、`Hall_Mystic` |
| W8 | 环境全部发布 | `publish/v001` |

#### 4.2.3 道具与特效资产（第 4–7 周）

| 周次 | 任务 | 产出 |
|---|---|---|
| W4–W5 | 飞剑、拂尘、符纸建模 + 绑定 | 可动画道具 |
| W6–W7 | FX 预设开发 | 剑气轨迹、法术光球、云雾体积、光屑粒子 |
| W7 | FX 资产发布 | `05_assets/lib/fx/` 下全部预设 |

**关键里程碑**：所有核心资产发布并通过 LookDev / ROM 审阅。

---

### 4.3 第三阶段：镜头制作（第 6–10 周）

每个镜头按 `dls.md` 第 6 节核心循环推进，优先制作 3–5 个关键镜头验证全流程。

| 周次 | 任务 | 说明 |
|---|---|---|
| W6–W7 | Layout（全部镜头） | 用代理粗模确定构图、机位、时长 |
| W7–W9 | 动画（分阶段） | Blocking → Blocking Plus → Spline → Polish |
| W8–W9 | CFX + FX | 披风布料、发丝、法术特效、云雾 |
| W9 | 灯光 | 套用灯光模板 + 局部 Light Linking |
| W9–W10 | 渲染 + 合成 | Eevee Next + View Layer 分层 + Compositor |

**每个镜头的状态流转**：`todo → wip → review → retake → review → approved`。

---

### 4.4 第四阶段：后期与交付（第 10–12 周）

| 周次 | 任务 | 产出 |
|---|---|---|
| W10–W11 | 合成 + 调色 | 分层重组、雾/辉光/镜头效果、色彩统一 |
| W11 | 剪辑 Conform | 按最终镜头列表重新组装 |
| W11–W12 | 音效 + 混音 | 环境音、法术音效、音乐、最终混音 |
| W12 | QC + 交付 | MP4 审阅片 + ProRes / H.265 交付版 |
| W12 | 归档 | 工程文件、缓存、管线代码纳入归档 |

---

## 5. 技术规范速查表

| 项目 | 仙侠 Demo 设定值 |
|---|---|
| Blender 版本 | 5.2 LTS |
| 分辨率 | 1920×1080 |
| 帧率 | 24 fps |
| 场景单位 | 公制，1 unit = 1 m |
| 帧号约定 | 镜头从 1001 开始，前后各留 8 帧 handles |
| 渲染器 | Eevee Next（默认） / Cycles（局部高精度体积） |
| 色彩管理 | Linear Rec.709 + AgX |
| 输出格式 | EXR Multilayer（合成前） → MP4 / H.265（交付） |
| 缓存格式 | Alembic (.abc)（动画） / OpenVDB (.vdb)（体积） |
| 场景规模 | 单镜头角色 ≤ 2 个，同屏特效 ≤ 5 个预设实例 |
| 渲染预算 | 单镜头时长 ≤ 30 秒，单帧 Eevee < 5 分钟 |

---

## 6. 仙侠专属 FX 管线规划

### 6.1 核心特效清单

| 特效 | 复杂度 | 技术方案 | 复用性 |
|---|---|---|---|
| 剑气轨迹 | 中 | GN Curve + 粒子系统 + Glow 材质 | 高，可调参数生成不同招式 |
| 法术光球 | 低 | 球体 + Emission + Volumetrics + Lens Flare（Compositor） | 高 |
| 云雾体积 | 高 | Mantaflow Gas 或 VDB 缓存 + GN 散布 | 中，按场景预烘焙 |
| 光屑 / 尘雾 | 低 | GN Simulation Zone + Point Instance | 高 |
| 飞剑飞行 | 中 | Alembic 缓存 + 尾迹粒子 | 中，单镜头为主 |
| 符纸燃烧 | 中 | Cloth（纸张）+ Fire（Mantaflow / GN 粒子） | 低 |
| 阵纹发光 | 低 | 平面 + Texture + Glow + 动画 | 高 |

### 6.2 特效工作流

```mermaid
flowchart LR
  A["在 05_assets/lib/fx/ 开发预设"] --> B["镜头 cfx/fx.blend 中实例化"]
  B --> C["调参数适配镜头"]
  C --> D["Bake / 导出缓存到 cache/"]
  D --> E["light.blend 读取缓存并渲染"]
```

- 所有 FX 预设封装为 **Asset Library**，镜头里只调参数。
- 体积雾、火、烟等重计算特效**必须缓存**，不在渲染时重算。

---

## 7. 自动化与 AI Agent 规划

### 7.1 管线脚本（Python / bpy）

参考 `dls.md` 第 14 节，优先实现以下确定性函数：

```python
# 资产
create_asset(type, name)            # 创建 wip 目录和模板 .blend
publish_asset(asset, notes)         # 检查、复制到 publish/v###、写元数据
load_asset(shot, asset, version)    # Link + Library Override + 规范命名

# 镜头
create_shot(seq, shot, frame_range) # 生成各环节 .blend
setup_camera(shot)                  # Sensor / 画幅遮罩 / 快门角度
setup_render(shot, stage)           # Eevee / View Layer / Pass / 输出路径
export_cache(shot, stage)           # Alembic / VDB

# 渲染与审阅
submit_render(shot, stage, version) # 提交到 Flamenco / 无界面渲染
collect_render(shot)                # 检查缺帧 / 坏帧
create_preview(shot, version)       # FFmpeg 生成带烧录的 MP4
```

### 7.2 适合仙侠 Demo 的 AI Agent 任务

| 任务 | 说明 |
|---|---|
| "按镜头表创建 seq010 全部镜头文件" | 批量脚手架 |
| "在 sh020 的竹林里放置主角，加载最新已发布版本" | 资产装配 |
| "用云海生成器生成云海， baked 到 cache/fx/v001" | 程序化内容 |
| "给 seq010 全部镜头套用 Cloud_Day 灯光模板" | 标准化灯光 |
| "检查全部镜头的贴图缺失和帧范围，生成报告" | QA |
| "提交 sh005 灯光 v003 渲染，帧范围 1001–1128" | 渲染调度 |

**风险控制**：Agent 只对 `wip/` 和自己镜头有写权限；发布操作必须人工确认；创作决策（表演、构图）留给人。

---

## 8. 渲染预算与硬件估算

### 8.1 时长与帧数

| 参数 | 值 |
|---|---|
| 片长 | 90 秒（Demo 取中值） |
| 帧率 | 24 fps |
| 总帧数 | 2,160 帧 |
| 镜头数 | 8 个 |
| 平均单镜头帧数 | 270 帧 |

### 8.2 单帧耗时估算（Eevee Next）

| 场景 | 单帧耗时 | 说明 |
|---|---|---|
| 简单 Layout / 预览 | < 10 秒 | 代理模型，低采样 |
| 单角色 + 简单环境 | 30 秒 – 2 分钟 | 含基础 FX |
| 复杂场景 + 体积雾 + FX | 2 – 5 分钟 | 需缓存体积 |

### 8.3 总机时与工期

```
总机时 = 2,160 帧 × 平均 1.5 分钟 × 重渲系数 2.5 ≈ 13,500 分钟 ≈ 225 机时
```

| 方案 | 工期 | 说明 |
|---|---|---|
| 单台工作站（8 核 / RTX 4090） | ≈ 3–4 天 | 串行渲染，个人最可行 |
| 2 台机器 | ≈ 2 天 | 简单任务分发 |
| Flamenco 农场（4–8 节点） | ≈ 1 天 | 推荐，可覆盖临时峰值 |

**存储估算**：
- 1080p EXR 多层：约 30–50 MB/帧
- 总渲染输出：2,160 × 40 MB ≈ **85 GB**
- 缓存（Alembic + VDB）：约 **20–50 GB**
- 项目总存储：**< 200 GB**（不含资产库）

---

## 9. 推荐工具栈（仙侠 Demo 定制）

| 工作 | 纯 Blender 方案 | 仙侠 Demo 增强建议 |
|---|---|---|
| 建模 / 雕刻 | Blender | 基础角色用纯 Blender；高精度面部可考虑 ZBrush（可选） |
| 拓扑 | Blender + RetopoFlow | 免费足够 |
| UV | Blender | 简单角色 RizomUV 可加速（可选） |
| 贴图 | Texture Paint + 程序化节点 | 仙侠袍服可用程序化织纹 + 手绘高光 |
| 绑定 | **Rigify** | 必须，仙侠宽袍需要大量布料权重 |
| 动画 | Blender + 动作捕捉 | Rokoko / AI 单目动捕做参考，手动精修 |
| 毛发 / 布料 | Hair Curves / Cloth | 发髻、发带、披风、长袍下摆 |
| FX | GN Simulation + Mantaflow + 粒子 | 剑气、云雾、法术光效 |
| 环境 / 程序化 | Geometry Nodes | 竹林、山石、建筑组合、云雾散布 |
| 灯光 / 渲染 | **Eevee Next** | 仙侠风格化首选；局部高精度体积可混用 Cycles |
| 合成 | Blender Compositor | 辉光、体积、镜头效果 |
| 剪辑 | Blender VSE | 足够，可配合 DaVinci Resolve |
| 调色 | DaVinci Resolve | 色彩脚本匹配，统一仙侠色调 |
| 音频 | DaVinci Resolve Fairlight / Reaper | 环境音 + 古风音乐 + 法术音效 |
| 生产追踪 | 表格 + 脚本 | 个人 Demo 最低配置；可升级 Kitsu |
| 版本控制 | Git（代码） + SVN / 手动备份（资产） | 个人项目简化，定期整目录备份 |
| 渲染农场 | **Flamenco** | 开源，个人可部署，解决临时峰值 |
| 自动化 | Python（bpy） | 重点：create_shot / load_asset / setup_render / export_cache / create_preview |

---

## 10. 风险管理与应对

| 风险 | 影响 | 应对 |
|---|---|---|
| 毛发 / 布料模拟耗时过长 | 延误 CFX 环节 | 中远景用 Hair Cards / 简化裙摆；近景才用完整模拟 |
| 云雾体积渲染过慢 | 渲染爆炸 | Eevee Volumetrics 为主；预烘焙 VDB 缓存；必要时局部 Cycles 低采样 |
| FX 参数难以控制 | 反复返工 | 所有 FX 封装为 Asset 预设，参数面板化；先做 1–2 个镜头验证 |
| 绑定返工 | 权重丢失、动画白做 | 拓扑锁定后不动；ROM 测试自动化，每次修改后强制跑一遍 |
| 渲染农场调度复杂 | 个人精力分散 | 先用单机串行跑通；Flamenco 只做最后批量渲染 |
| 风格跑偏 | 后期调色救不回来 | 色彩脚本 + 关键帧概念图在前期锁定；灯光模板强制执行 |
| 范围蔓延 | Demo 变半年项目 | 严格按 1–3 分钟执行；特效清单只做核心 5–7 种 |

---

## 11. 里程碑与检查点

| 里程碑 | 时间 | 通过标准 |
|---|---|---|
| M1：Story Lock | 第 4 周末 | 分镜定稿、镜头表锁定、色彩脚本通过 |
| M2：资产发布 | 第 8 周末 | 主角、场景、道具全部发布并通过 LookDev / ROM |
| M3：动画通过 | 第 10 周末 | 全部镜头动画 Spline 阶段通过，进入 CFX/FX |
| M4：渲染通过 | 第 11 周末 | 全部镜头渲染完成，无缺帧坏帧 |
| M5：最终交付 | 第 12 周末 | 合成、调色、混音完成；MP4 + ProRes 母版交付；归档完成 |

---

## 12. 下一步行动（落地清单）

- [ ] **Project Bible 定稿**：分辨率、帧率、色彩管理、命名规范（见第 5 节）
- [ ] **目录模板生成**：一键生成第 3 节目录结构
- [ ] **模板 .blend**：Layout / Anim / CFX / FX / Light 各一个，预置单位、帧率、色彩管理、Collection 结构
- [ ] **LookDev 场景**：统一 HDRI、灰球、色卡、转台相机
- [ ] **主角绑定基础**：Rigify 元骨骼、面部口型集、ROM 测试动画
- [ ] **仙侠 FX 资产库**：剑气、光球、云雾、光屑预设封装为 Asset Library
- [ ] **灯光模板**：`Cloud_Day`、`Night_Moon`、`Hall_Mystic` 三个核心模板
- [ ] **镜头表 / 资产表**：表格 + 脚本自动化
- [ ] **管线 API**：`create_shot` / `load_asset` / `setup_render` / `export_cache` / `create_preview`
- [ ] **渲染设置预设**：Eevee Next View Layer、Pass、输出路径
- [ ] **Flamenco 部署**：本地渲染农场 + 提交前检查脚本
- [ ] **备份策略**：Git（代码）+ 定期整目录备份（资产）+ 3-2-1 原则
- [ ] **试验短片**：先跑通 1–2 个镜头的完整流程（分镜 → 交付），再扩展全片

---

## 附录：与 docs/dls.md 的对应关系

| 本计划章节 | 对应 dls.md 章节 |
|---|---|
| 项目定位 | 第 2、13 节 |
| 目录结构 | 第 3 节 |
| 前期制作 | 第 4 节 |
| 资产制作 | 第 5 节 |
| 镜头制作 | 第 6 节 |
| 渲染 | 第 7 节 |
| 后期制作 | 第 8 节 |
| 交付与归档 | 第 9 节 |
| 生产管理 | 第 10 节 |
| 性能与场景规模 | 第 11 节 |
| 工具栈 | 第 12 节 |
| 个人 / 小团队策略 | 第 13 节 |
| 自动化与 AI Agent | 第 14 节 |
| 落地清单 | 第 15 节 |
