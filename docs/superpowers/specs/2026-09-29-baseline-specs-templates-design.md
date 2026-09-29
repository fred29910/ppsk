# 规范与模板基线 —— 设计文档

| 项 | 值 |
|---|---|
| 日期 | 2026-09-29 |
| 对应计划章节 | `docs/plan.md` §22.3（规范与模板） |
| 状态 | 待评审 |
| 范围声明 | 本段只做"规范与模板"。管线 API 补齐（§22.5）、资产（§22.4）不在本段 |

---

## 1. 背景

`docs/plan.md` §19.3（Kill Criteria）规定：**G0 未通过则不进入资产制作**。本次开工前的环境实测显示，plan §5.0 的 6 项 G0 测试在本机**无法通过**，原因见 §2.2。

因此开工顺序从 plan §22 的 W0 调整为：先做**不依赖 GPU 的部分**——§22.3 规范与模板。这一段是 W1/W2 的前置（Project Bible 定稿、目录结构、镜头模板），且其中的代码（`spec.py` / `scaffold.py` / `check_spec.py`）可以在系统 Python 下测试，不受无 GPU 环境影响。

G0 的实测结论与差距报告**不在本段**产出，另开一段处理。

---

## 2. 开工前的环境实测

### 2.1 已验证事实

以下均为本机实际执行命令得到的结果，非推断：

| 项 | 实测值 | 验证方式 |
|---|---|---|
| Blender 版本 | **5.2.0 LTS** | `blender --version` |
| build hash | `fbe6228777e7`，built 2026-07-14 01:32:04 | 同上 |
| 安装路径 | `/opt/data/dev/blender-5.2.0-linux-x64/`（`~/.local/bin/blender` 符号链接） | `readlink` |
| 引擎枚举 | **仅 `BLENDER_EEVEE`**（无 Cycles，无 Workbench） | `bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items` |
| GPU | **无**（`nvidia-smi` 不存在） | `nvidia-smi` |
| 无头 EEVEE 渲染 | 可运行。640×360 空场景 4.1 秒，输出 100 KB EXR（Linear Rec.709，4 通道，像素 min 0.041 / max 1.0，100% 非零） | `blender -b` 实渲 |
| 磁盘 | `/mnt/data` 剩余 **121 GB** | `df -h` |
| 系统 Python | 3.13.5，**无 `bpy` 模块** | `python3 -c "import bpy"` |
| Blender 内置 Python | 3.13.13 | `blender -b` 内打印 |
| OCIO 配置 | 存在（`5.2/datafiles/colormanagement/config.ocio`），`AgX` / `Standard` / `Khronos PBR Neutral` / `Filmic` 均可设置成功 | 逐个赋值测试 |
| 快门属性 | `motion_blur_shutter` / `motion_blur_position` / `motion_blur_shutter_curve` / `use_motion_blur` 均存在 | 枚举 |
| 图像格式 | 含 `OPEN_EXR` / `OPEN_EXR_MULTILAYER`；`color_depth` 枚举含 8/10/12/16/32 | 枚举 |
| 阴影池 | `shadow_pool_size` 枚举 16…2048（MB） | 枚举 |
| 资产标记 | `bpy.ops.asset.mark` 存在 | 属性检查 |
| Light probe 类型 | `SPHERE` / `PLANE` / `VOLUME` | enum 枚举 |
| View Layer Pass | 含 `use_pass_z` / `use_pass_mist` / `use_pass_vector` / `use_pass_normal` / `use_pass_position` / cryptomatte 系列 | 枚举 |
| 色彩管理 enum | **动态 RNA，`enum_items` 只返回 `['NONE']`**，不可用于校验 | 实例级枚举 + 赋值测试 |

### 2.2 与 plan.md 的冲突

| plan.md 要求 | 实测 | 结论 |
|---|---|---|
| 锁定 Blender **5.2.1** LTS（§7.1、§12.1） | 5.2.0 | 严格锁 5.2.1 会使全部管线脚本无法启动 → 见 §3 决策 D2 |
| §2.2 / §5.0 T2 / §7.1 / §19.1 依赖 **Cycles** 作降级路径 | 本机构建无 Cycles | 路径存在但本机不可验证 → 决策 D4 |
| 渲染期峰值空闲 **≥ 300 GB**（§14.5） | 121 GB | 不满足，不在本段解决 |
| §5.0 T3「10k 竹子单帧 < 90 秒」 | 无 GPU，软件 GL 渲染 | 该测试在本机不可能通过 |
| §12.1「管线 API 骨架 5 模块 201 行已实现」 | 236 行，**全部为 `# TODO` 空壳**，无任何 `bpy` 调用 | §22.1 该勾选项失实 → 决策 D6 |
| §22.1「镜头目录骨架 `seq040/sh020/`」 | `06_shots/` 下只有 `README.md`，`seq040` 不存在 | 勾选项失实 → 决策 D6 |

### 2.3 会话中途出现的文件

`00_project/bible/scope_lock.md`（5 KB，mtime 2026-09-29 16:19）在本设计讨论开始后出现，且未被 Git 跟踪。其内容为方案 S 的范围锁定决策记录，其中「渲染器」行锁定 `Blender 5.2.1 LTS`。

该文件 §3.1 规定锁定项变更须走四步流程（提出 → 评审 → 更新文档 → 通知），且结尾「签署」栏为空、自称「自签署之日起生效」。因此本次版本锁变更**受该文件管辖**，必须以变更记录（CR-001）形式落地，而非直接改数字。详见 §8.2。

---

## 3. 决策记录

| # | 决策 | 选择 | 理由 |
|---|---|---|---|
| **D1** | 第一段实施范围 | **§22.3 规范与模板** | G0 在本机无法通过，资产/镜头制作被 Kill Criteria 挡住；§22.3 不依赖 GPU 且是 W1/W2 前置 |
| **D2** | Blender 版本锁 | **改为锁定 5.2.0** | 严格锁 5.2.1 会使全部脚本无法启动、本段无法验收。代价（错过 5.2.1 的 patch 修复）由 CR-001 明确承担 |
| **D3** | 模板产出形态 | **全部用 bpy 脚本真实生成** | `.blend` 保存不需要 GPU，可本机验收；只写文档则无法验证 |
| **D4** | Cycles 的地位 | **保留但标注本机未验证** | 本机是定制构建，官方 5.2.0 发行版自带 Cycles；仅凭一台开发机就永久删除该工程选项不合理 |
| **D5** | FX 预设目录 | **提升到 `05_assets/fx/`**，与 chr/env/prp/veh/lib 平级 | plan §3.1 与 dls.md §6.6 冲突；dls.md 声明"只用一套目录"，`05_assets/lib/fx/` 提升后与 §3.4 Asset Browser 分类一致 |
| **D6** | 规格的机器可读来源 | **`spec.py` 单一来源 + `check_spec.py` 校验** | 规格同时出现在 Bible 和代码里必然漂移；不做单一来源，本段"把规格定死"的目的落空 |
| **D7** | 运动模糊 vs Vector Pass | **`use_motion_blur=False` + `use_pass_vector=True`** | plan §7.4 规定二者互斥；plan §6.2 Comp DoD 要求运动模糊在合成层可控；无 GPU 时渲染器运动模糊也慢 |
| **D8** | 9:16 竖屏版 | **只渲染 16:9，9:16 后期裁切** | 渲染阶段出两套会重算 View Layer 预算（§11 上限 4）；Layout 已留安全框，Comp 裁切即可 |

---

## 4. 范围

### 4.1 本段交付

**新增文件（进 Git）**

```
00_project/pipeline/spec.py              规格唯一机器可读来源（纯数据，不 import bpy）
00_project/pipeline/check_spec.py        校验 Bible 生成区块与 spec.py 一致
00_project/pipeline/scaffold.py          目录结构生成器（不 import bpy）
00_project/pipeline/render_preset.py     渲染设置预设（函数式，import bpy）
00_project/pipeline/build_templates.py   .blend 模板生成器（import bpy）
00_project/pipeline/tests/               两套测试（见 §10）
```

**本地产物（不进 Git）**

```
00_project/templates/tpl_layout_v001.blend
00_project/templates/tpl_anim_v001.blend
00_project/templates/tpl_cfx_v001.blend
00_project/templates/tpl_fx_v001.blend
00_project/templates/tpl_light_v001.blend
00_project/templates/tpl_lookdev_v001.blend
```

**改动文档**：`project_bible.md`（定稿）、`scope_lock.md`（CR-001）、`docs/dls.md`（§3.1 + §6.6）、`docs/plan.md`（8 处 + 勾选修正）、`README.md`（同步）

### 4.2 本段不做

| 项 | 归属 |
|---|---|
| 管线 API 补齐（`audit_shot` / `get_dependencies` / `read_shotlist` / `write_status` / `collect_render` / `upgrade_asset`） | plan §22.5 |
| 追踪表 `shotlist.csv` 与镜头目录创建 | plan §22.5 |
| G0 可行性报告与差距分析 | 另开一段 |
| Asset Library 注册（`preferences.filepaths.asset_libraries`，用户级偏好不属于项目文件） | plan §22.4 |
| FX 预设 `asset_mark` 打包、竹林 GN 生成器、灯光模板 `Cloud_Day`/`Night_Moon`/`Hall_Mystic` | plan §22.4 |
| LookDev 的 HDRI 文件本身 | plan §22.4 / §16 授权登记 |

---

## 5. 架构

```text
                    spec.py  ← 唯一机器可读来源（纯数据）
                    ├─→ check_spec.py    （校验 Bible 生成区块；默认只读）
                    │      └─→ --sync 写回区块
                    ├─→ scaffold.py      （目录树，声明式，不 import bpy）
                    └─→ render_preset.py （apply(scene) 函数）
                           └─→ build_templates.py（写 6 个 .blend）
                                    └─→ tests/test_blend_roundtrip.py（重开断言）
```

关键约束：

- `spec.py` / `check_spec.py` / `scaffold.py` **不得 import bpy**，以保证能在系统 Python 下测试
- 上述三个模块之外，任何模块**不得硬编码** `spec.py` 里的数值
- 目录树声明放在 `scaffold.py`，不放 `spec.py`（目录树是结构，与 dls.md §3.1 一一对应；混入数值规格会污染两边）

### 5.1 `spec.py` 契约

```python
"""项目规格 —— 唯一机器可读来源。
不 import bpy：本模块必须能被系统 Python 直接导入。
所有数值与 00_project/bible/project_bible.md 的生成区块保持一致，
由 check_spec.py 校验。禁止在其他模块硬编码这些值。"""

BLENDER_VERSION      = "5.2.0"
BLENDER_BUILD_HASH   = "fbe6228777e7"    # 本机 dev build，2026-07-14 01:32:04
BLENDER_BUILD_FLAVOR = "dev"             # 非官方发行版：无 Cycles / Workbench
CYCLES_AVAILABLE     = False

SPEC = {
    "resolution": (1920, 1080),
    "resolution_fallback": (1600, 900),   # 降级 L3
    "fps": 24,
    "shutter_deg": 180.0,                 # 0.5 帧运动模糊
    "safe_frames": {"main": (16, 9), "vertical": (9, 16)},
    "frame": {"first": 1001, "handles": 8},   # 有效 1009–1128，渲染 1001–1136
    "unit": {"system": "METRIC", "scale_length": 1.0},
}

COLOR = {
    "display_device":   "sRGB",
    "view_transform":   "AgX",
    "look":             "None",
    "work_space":       "scene_linear",   # Scene Linear (Rec.709 primaries)
    "delivery_gamut":   "Rec.709",
    "view_transform_fx_fallback": "Khronos PBR Neutral",  # plan §9.3 per-shot 策略
}

EXR = {
    "format":         "OPEN_EXR_MULTILAYER",
    "color_depth":    "16",    # 颜色 Pass Half
    "data_depth":     "32",    # Depth / Position / Vector / Cryptomatte 的要求精度
    "scene_linear":   True,    # 不烘入显示变换
    "motion_blur":    False,   # D7：后期做
    "vector_pass":    True,
    "path": "{stage_dir}/{shot}_{stage}_v{version}.{frame:04d}.exr",
}

EEVEE = {
    "engine": "BLENDER_EEVEE",
    "shadow_pool_size": "1024",     # Large Shadow Pool（plan §7.4）
    "max_probe_sphere": 128,        # EEVEE 硬上限
    "max_probe_plane":  16,         # 视锥内硬上限
    "volumetric_samples": None,     # T1/G0 实测后填，不猜
    "taa_render_samples": None,     # 同上
    "passes_required": ["combined", "z", "mist", "vector",
                        "normal", "diffuse_color", "diffuse_direct",
                        "diffuse_indirect", "glossy_direct", "glossy_indirect",
                        "emit", "shadow", "environment", "ambient_occlusion"],
    "passes_data": ["z", "mist", "vector", "normal", "position", "cryptomatte_object"],
}

# plan §11 性能与场景规模预算 —— 下一段的 audit_shot 直接读
BUDGET = {
    "chars_per_shot": 2, "fx_instances_per_shot": 5,
    "tris_per_shot": 1_500_000, "materials": 60, "lights": 20,
    "vdb_resolution": 128, "gn_instances": 10_000,
    "vram_gb": 20, "alembic_gb_per_shot": 2, "view_layers": 4,
}
```

`passes_required` / `passes_data` 是**要求**，不是已验证的事实。列表中每个属性名都已实测存在于 `bpy.types.ViewLayer`（§2.1），但"属性存在"与"EEVEE 真的会渲染出这个 Pass"是两回事——后者只有真渲一帧才能确认。

因此 `build_templates.py` 的行为是：设完后**读回** `view_layer.use_pass_*`，把实际勾选的清单写入返回值的 `passes_effective`；与 `passes_required` 有差异时报警告。**读回只证明勾选状态，不证明 Pass 里有正确数据**（见 §10.2 的边界声明）。

### 5.2 版本校验规则（两级）

| 检查 | 规则 | 违反时 |
|---|---|---|
| 版本号前两段 | 必须等于 `5.2` | 退出码非 0，打印实际版本 |
| build hash | 与 `spec.py` 记录不符 | **警告**，实际 hash 写入报告，继续 |

比"前两段"而非三段的原因：官方 5.2.0 发行版与本机 5.2.0 dev build 应视为同一锁定版本，build hash 必然不同（§2.1）；而 5.2.0 ↔ 5.2.1 的 patch 漂移才是要拦的风险。

---

## 6. `scaffold.py` — 目录结构

目标结构（dls.md §3.1 + D5 的提升 + plan §3.1 的 veh 保留）：

```text
00_project/{bible,ocio,pipeline,templates}/
01_story/  02_storyboard/  03_editorial/  04_audio/
05_assets/
├── chr/hero/{wip,publish}/   # dls.md §3.1 只对 chr/hero 给出 wip/publish
├── env/                      # 其余分类不擅自推广 wip/publish
├── prp/
├── fx/                       # D5：新增，与 chr/env/prp/veh/lib 平级
├── veh/                      # 保留但空（plan §3.1 明示）
└── lib/
06_shots/                     # 只建空骨架，不建 seq###/sh###
07_review/  08_delivery/  09_archive/
```

> **为什么只有 `chr/hero` 有 `wip/publish`。** dls.md §3.1 的目录树只对 `chr/hero` 画了 `{wip, publish}`，`env/` / `prp/` / `veh/` / `lib/` 都是平铺。本段不把 `wip/publish` 推广到其他分类——那属于对权威规范的扩展，应在 dls.md 里显式决定，而不是由脚手架默认。`fx/` 的内部结构同理：只建 `05_assets/fx/` 本身，内容结构由下一段的资产工作按需建立。

三个硬性行为：

| 行为 | 规则 |
|---|---|
| 幂等 | 已存在则跳过，只新建缺失项。跑第 10 次与跑第 1 次结果相同 |
| 只增不删 | 绝不 `rm` / `rmdir`。目录内有用户文件一律跳过（plan §12.3） |
| `--dry-run` | 默认打印计划，`--apply` 才创建 |

**不建 `seq###/sh###/`**：镜头目录依赖 §13 镜头表，属于下一段 `create_shot` 的职责。

---

## 7. `build_templates.py` — .blend 生成

### 7.1 六个模板的内容

| 文件 | 内容 |
|---|---|
| `tpl_layout_v001.blend` | 相机 `CAM_cam` + `CHR_` / `ENV_` / `PRP_` collection + `GUIDE_` 安全框线框 |
| `tpl_anim_v001.blend` | `CHR_` collection + 代理占位，不含相机灯光 |
| `tpl_cfx_v001.blend` | `CHR_` collection + `CHR_cloth` 布料工作区 |
| `tpl_fx_v001.blend` | `FX_` collection + 特效工作区 |
| `tpl_light_v001.blend` | `LGT_` collection + 完整渲染设置 + View Layer 分层 + 输出路径 |
| `tpl_lookdev_v001.blend` | 转台相机 + 灰球 + ColorChecker 24 色卡 + HDRI 槽位 |

全部模板共享：公制单位、24 fps、帧范围 1001–1136、`frame_current = 1009`、色彩管理四元组，以及同一套 collection 骨架（`CHR_` / `ENV_` / `PRP_` / `FX_` / `LGT_` / `GUIDE_`）。

**两处需要显式记录的偏离**：

| 偏离 | 说明 |
|---|---|
| 文件名用 `tpl_<环节>_v001.blend` | plan §3.2 的命名规则覆盖"镜头或资产"，模板两者都不是。故引入 `tpl_` 前缀 + 沿用三位版本号。这是一处**新造约定**，需在 Bible 命名规范表中补一行 |
| 帧范围 1001–1136 | 这是 plan §7.1 给的 6 秒单镜示例值。模板必须有一个默认值，但**不是**所有镜头的范围；实际范围由下一段从 `shotlist.csv` 读取（§13） |

### 7.2 渲染设置预设：函数而非独立 `.blend`

`render_preset.py` 提供 `apply(scene, project_root)`。`build_templates.py` 烘进 `tpl_light`，下一段的 `setup_render` 也调它。一份实现两个消费者，不会漂移。满足 plan §22.3「渲染设置预设」这一项，但不在磁盘上多存一份需要同步的副本。

### 7.3 View Layer 分层

`tpl_light` 预置两个：`VL_beauty`（合并）+ `VL_char`（角色，排除环境）。这是 plan §21.1「只重渲 `VL_char` 不重渲 `VL_env`」技术指标的落地起点；plan §11 上限为 ≤4，留有余量。

### 7.4 9:16 安全框

Blender 无原生第二画幅遮罩。实现为 `GUIDE_` collection 中的 9:16 线框对象，`hide_render = True`，Layout 阶段开可视。渲染输出**只出 16:9**（D8）。

### 7.5 相机默认值

Bible 未锁 sensor 尺寸，plan §13 也把 `focal_length` 定为**逐镜记录**字段。因此模板只固定"不随镜头变化"的部分：

| 属性 | 模板默认 | 理由 |
|---|---|---|
| `sensor_width` | 36 mm | Blender 默认值；16:9 下自动横向适配 |
| `sensor_fit` | `AUTO` | 随分辨率变化，居中 |
| `lens` | 35 mm | **占位值**，逐镜由 `shotlist.csv` 覆盖（plan §13） |
| `shift_x` / `shift_y` | 0.0 | 9:16 用安全框 + 后期裁切，不靠 shift（D8） |
| `clip_start` / `clip_end` | 0.1 / 1000 m | 公制场景常规值 |

### 7.6 快门的换算

`spec.py` 存的是 `shutter_deg = 180.0`（人读、plan §7.1 的表述）。写入 Blender 时必须换算：

```python
scene.render.motion_blur_shutter = spec.SPEC["shutter_deg"] / 360.0   # → 0.5
```

Blender 的 `motion_blur_shutter` 单位是"帧"（0.5 = 0.5 帧），不是角度。直接写 `180.0` 会得到 180 帧的运动模糊且**不报错**——属于典型的静默错误，往返测试必须断言 `== 0.5`。

---

## 8. 文档改动

### 8.1 `project_bible.md` — 定稿

现状是**通用模板**（3840×2160、1.85:1、ACEScg 等均为模板建议值），不是本项目锁定值。定稿后结构：

| 节 | 内容 | 来源 |
|---|---|---|
| 技术规格 | 5.2.0 + build hash、1920×1080、24 fps、180° 快门、公制 1 u = 1 m、1001 起 + 8 帧 handles | plan §7.1 |
| 色彩管理 | 四元组 Scene Linear / **AgX** / sRGB / **None**；+ per-shot `Khronos PBR Neutral` 例外条款 | plan §7.2 §9.3 |
| EEVEE 约束 | probe ≤128 sphere / ≤16 plane、shadow pool、运动模糊/Vector 互斥（D7） | plan §7.4 |
| 性能预算 | plan §11 全表 | plan §11 |
| 命名规范 | 保留原表 + 新增对象名 vs 资产 ID 规则（§9.3） | dls.md + §9.3 |
| **规格生成区块** | 哨兵标记，内容由 `check_spec.py --sync` 从 `spec.py` 渲染 | §9.1 |
| **本机环境记录** | build hash、dev build flavor、无 GPU、Cycles 不可用、磁盘 121 GB < 300 GB | §2.1 |

### 8.2 `scope_lock.md` — 追加 CR-001

D2 变更受该文件 §3.1 的四步流程管辖（且该文件尚未签署、其"自签署之日起生效"条款当前不成立）。追加：

```markdown
## 6. 变更记录

### CR-001 锁定版本 5.2.1 → 5.2.0
| 项目 | 内容 |
|---|---|
| 变更日期 | 2026-09-29 |
| 变更项 | 锁定版本：Blender 5.2.1 LTS → **5.2.0 LTS**（build hash `fbe6228777e7`，dev build） |
| 原因 | 开发机实际可用版本为 5.2.0；严格锁 5.2.1 会使全部管线脚本无法启动（plan §12.1） |
| 影响 | plan §7.1 / §12.1 同步更新 |
| 未承担的风险 | 5.2.1 仍是最新 patch，本项目将错过其修复；**升到 5.2.1 需另开 CR** |
| 决策人 | 待签 |
```

同时补一句现状声明：本文件签署栏为空，签署前不构成生效基准。

### 8.3 `docs/dls.md` — 两处

| 位置 | 改动 |
|---|---|
| §3.1 目录树（line 192–199） | `05_assets/` 下加 `fx/`，与 chr/env/prp/veh/lib 平级（**不加** `wip/publish`，与 env/prp/veh 保持一致，见 §6） |
| §6.6（line 692） | `05_assets/lib/fx/` → `05_assets/fx/`，并写明划分规则：`fx/` 放可发布 FX 预设，`lib/` 放节点组与 GN 生成器 |

### 8.4 `docs/plan.md` — 反向更新

| 位置 | 改动 |
|---|---|
| line 5 头部锁定版本 | 5.2.1 → **5.2.0** + build hash；注明 5.2.1 为最新 patch，本项目因开发机可用性锁 5.2.0（CR-001） |
| line 355 §7.1 | 同上 |
| line 583 §12.1 | `== 5.2.1` → 版本号严格 / build hash 仅警告（§5.2 两级规则） |
| line 777 §16.3、line 825 §18.1、line 945 §22.2 | 版本号同步 |
| line 863 §19.1 patch 漂移风险 | 改写为"dev build ↔ 官方发行版"漂移，仍是同类风险 |
| line 1073 附录 C | **保留**"5.2.1 已于 2026-08-25 发布"这条外部事实（它是真的），结论"→ 必须锁 patch"改为"→ 本项目锁 5.2.0，理由见 CR-001" |
| §2.2 line 97、§5.0 T2 line 197、§7.1 line 362、§19.1 line 856 | Cycles 四处**就地标注**：本机引擎枚举仅 `BLENDER_EEVEE`，该降级路径未验证，需在渲染机复核（D4） |
| §22.1 | 修正两处失实勾选：管线 API 骨架实为全 TODO 空壳；镜头目录骨架 `seq040/sh020/` 不存在 |
| §22.3 | 本段完成项打勾 |

改 plan.md 的性质是"用实际情况反向更新计划"，不是降低标准：附录 C 的外部事实全部保留，锁 5.2.0 的代价在 CR-001 中明确写出，由签署人承担。

### 8.5 `README.md` — 同步

line 3 / 9 / 44 版本号；落地清单按 §22.3 更新勾选；新增一句指向 `spec.py`：「规格以 `00_project/pipeline/spec.py` 为机器可读来源，改规格改它再跑 `check_spec.py --sync`」。

---

## 9. 实现约束

### 9.1 Bible 生成区块

不写表格解析器。`project_bible.md` 中放一个带哨兵标记的区块，内容由 `check_spec.py --sync` 从 `spec.py` 渲染写入；`check_spec.py` 默认**只比对不写**，发现不一致即报错退出。Markdown 中该段是给人读的权威展示，`spec.py` 是唯一来源，区块过期可被自动抓到。

### 9.2 统一返回约定（plan §12.1）

```python
# 成功
{"ok": True, "created": [...], "skipped": [...], "blends": [...],
 "passes_effective": [...], "warnings": [...]}
# 失败
{"ok": False, "error": "…", "hint": "…"}
```

- 所有函数接受 `project_root` 参数，无硬编码路径
- **只读函数绝不写盘**：`check_spec.py` 默认只比对
- 写盘函数均有 `--dry-run`

### 9.3 命名：对象名 vs 资产 ID

`utils.normalize_name` 现有实现会转小写：

```python
return name.strip("_").lower()          # utils.py 现有一行
```

而 dls.md 规定对象名用**大写前缀**（`GEO_` / `RIG_` / `CTRL_` / `CAM_` / `LGT_`）。若直接用它处理对象名，会生成 `geo_grayball`，违反命名规范。

处理：新增 `make_object_name(prefix, name)` 保留大写前缀供**对象名**使用；`normalize_name` 保持原样（不破坏现有调用方），仅在文档中写明适用边界——**资产 ID 用 `normalize_name`，对象名用 `make_object_name`**。

---

## 10. 验证

### 10.1 两套运行环境

| 模块 | 依赖 | 跑在哪 |
|---|---|---|
| `spec.py` | 无 | 系统 `python3` |
| `check_spec.py` | 无 | 系统 `python3` |
| `scaffold.py` | 无（仅 `os`） | 系统 `python3` |
| `render_preset.py` | `bpy` | `blender -b` |
| `build_templates.py` | `bpy` | `blender -b` |

不 import bpy 的硬约束（§5）直接换来"约 60% 的代码无需开 Blender 即可测试"。

### 10.2 `.blend` 往返测试（核心）

只测"脚本没抛异常"是空的。已实测证明存在静默失效的可能：色彩管理的 view transform 是动态 RNA enum，`enum_items` 只返回 `['NONE']`，若用枚举校验则任何检查都会假通过。因此验收必须是往返：

```text
build_templates.py  →  写 6 个 .blend
                         ↓
test_blend_roundtrip.py  →  blender -b 重新打开每个 .blend
                         ↓
                    逐项断言：分辨率 / fps / shutter / 单位 /
                    view_transform=AgX / look=None / display=sRGB /
                    帧范围 1001–1136 / engine=BLENDER_EEVEE /
                    EXR 格式与位深 / 色彩管理四元组 / collection 齐全
                         ↓
                    全对 → 退出 0；任一项不符 → 打印实际值并退出 1
```

**本段只验证"设置落进了文件"，不验证"渲染出来对"。** `use_pass_z is True` 能断言，Depth pass 内数据是否正确只有真渲一帧才知道；无 GPU 环境下那次渲染（640×360 / 4.1 秒）不构成可信证据。

### 10.3 元测试：证明校验器不是摆设

```text
1. 跑 check_spec.py                 → 期望退出 0
2. 手动改错 spec.py 里一个分辨率数字   → 期望退出非 0，并指出该字段
3. 改回来                          → 期望退出 0
```

若第 2 步不报错，说明校验器是装饰品，后续所有"已校验"声明均不成立。

### 10.4 错误处理

| 情况 | 行为 | 理由 |
|---|---|---|
| Blender 版本号前两段 ≠ `5.2` | 退出码非 0，打印实际版本 | plan §12.1 |
| build hash 与记录不符 | 警告，实际 hash 写入报告，继续 | dev build ↔ 官方版必然不同 |
| 目标 `.blend` 已存在 | **跳过并报 `skipped`**，不覆盖；覆盖需显式 `--overwrite` | 模板会被人在 GUI 里改，生成器不能默默吃掉手工工作 |
| HDRI 文件缺失（LookDev） | 警告，**不伪造**纯色环境，报告标注"HDRI 未安装" | 假环境会让 LookDev 审阅结论失真 |
| `--project-root` 下无 `00_project/` | 退出码非 0 + 提示 | 防止在错误目录建出空壳 |
| 目录树中已有非空目录 | 跳过，不删 | plan §12.3 |

### 10.5 验收清单

- [ ] 6 个 `.blend` 生成，**重新打开后**规格逐项断言通过（含 `motion_blur_shutter == 0.5`，§7.6）
- [ ] `scaffold.py` 第二次运行零新建（幂等）
- [ ] `scaffold.py` 不删任何已有文件（用带内容的目录验证）
- [ ] `scaffold.py` 只在 `chr/hero` 下建 `wip`/`publish`（§6）
- [ ] `check_spec.py` 退出 0；改错一个值后退出非 0（§10.3 元测试）
- [ ] Bible 规格生成区块与 `spec.py` 一致；`--sync` 后再校验仍退出 0（往返幂等）
- [ ] 5 份文档改动落地，`CR-001` 写入 `scope_lock.md` 并标注**待签署**
- [ ] Bible 命名规范表已补 `tpl_` 前缀一行（§7.1 偏离记录）
- [ ] plan §22.1 两处失实勾选已修正
- [ ] 所有生成器 `--dry-run` 不写盘（以 mtime 验证）

---

## 11. 明确不在本段验证

| 项 | 原因 |
|---|---|
| EEVEE 实际渲染画质与单帧耗时 | 无 GPU；实测 640×360 空场景已 4.1 秒，不构成可信性能证据 |
| `volumetric_samples` / `taa_render_samples` 取值 | 无 GPU 时定的采样数无意义 → `spec.py` 中留 `None` |
| Cycles 局部渲染路径 | 本机构建无 Cycles（D4） |
| Pass 内容正确性 | 需真渲一帧；本段只验证设置落地 |
| HDRI 成片效果 | HDRI 文件本身属 §22.4 / §16 授权登记 |

前四项顺延到有渲染机时的 G0。

---

## 12. 风险

| 风险 | 应对 |
|---|---|
| `volumetric_samples` / `taa_render_samples` 长期为 `None`，导致下游 `setup_render` 拿到空值 | 下一段实现 `setup_render` 时必须显式处理 `None`：报 `ok=False` 并提示"该值待 G0 实测后填入 spec.py"，不得静默用默认值 |
| 动态 RNA enum 陷阱再次出现（其他属性也可能只返回 `['NONE']`） | 所有 enum 设置一律"赋值 + 读回验证"，不使用 `enum_items` 做前置校验 |
| 改 plan.md 降低了自己刚立的"锁 patch"标准 | 附录 C 外部事实全部保留；代价写入 CR-001 并需签署 |
| `scope_lock.md` 始终未签署 | 本段在文件中显式声明"签署前不构成生效基准" |
| 磁盘 121 GB < §14.5 要求的 300 GB 峰值 | 不在本段解决；但渲染相关产物落盘前需重新检查 |

---

## 13. 术语与引用

| 缩写 | 含义 |
|---|---|
| D1–D8 | §3 的八项决策 |
| CR-001 | `scope_lock.md` 的第 001 号变更记录 |
| G0 | plan §5.0 技术可行性门禁 |
| VL | View Layer |
| 往返测试 | 生成 → 重新打开 → 读回断言（§10.2） |
