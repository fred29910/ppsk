# 规范与模板基线 —— 设计文档

| 项 | 值 |
|---|---|
| 日期 | 2026-09-29 |
| 版本 | **v2（活文档）** |
| 状态 | 待评审 |
| 对应计划章节 | `docs/plan.md` §22.3（规范与模板） |
| 事实快照 | commit **`8c06178`**，工作区干净，2026-09-29 17:48 |
| 范围声明 | 本段只做"规范与模板"。管线 API 补齐（§22.5）、资产（§22.4）不在本段 |
| 文档性质 | **活文档**。§2/§4/§8/§12 的事实随仓库演进，改规格先改本文档的复核命令再复核 |

> **引用约定**：本文档自身的小节用 `§N`。带 `v1` 前缀的（如 `v1 §5.2`）指**上一版本**
> 已被本版重写掉的小节，仅用于说明"v1 原本怎么写的"。
> 不带前缀的 `plan §N` / `dls.md §N` 指**其他文档**的章节。

> **本文档的每条环境事实都可以用 §2.4 的复核命令重新验证。**
> 仓库正在被并行会话改动，不要相信任何转述——先跑复核命令。

---

## 0. 修订说明（v2 对 v1 的更正）

v1 是一份**开工前的设计**，基于对仓库的一次快照。它有三类问题：一条**被实测推翻的测量**、
一批**从未执行**的交付物、一批**已被别人抢先做掉**的工作。

| v1 的说法 | 实际情况 | 处置 |
|---|---|---|
| 引擎枚举「仅 `BLENDER_EEVEE`」，**无 Cycles**，本机构建是去掉了 Cycles 的 dev build | **错**。枚举确实只有 `['BLENDER_EEVEE']`，但 `scene.render.engine='CYCLES'` **赋值成功**，`hasattr(scene,'cycles')` 为真，`device=CPU`。v1 和 G0 报告 v1 都把「`-b` 模式静态枚举不注册」误读成「引擎不存在」 | §2.1 订正；D4 推翻（§3） |
| G0 挡住开工，所以先做 §22.3 | **已过时**。G0 已执行完毕（`00_project/bible/g0_feasibility_report.md`，524 行），T1/T4 有结论、T6 部分通过 | §1 重写 |
| 交付 `spec.py` / `check_spec.py` / `scaffold.py` / `render_preset.py` / `build_templates.py` | **一个都没建**。实际走的是另一条路：直接写 `shot.py` / `review.py` / `utils.py`，并执行 G0 | §4.1 改为「已交付」，§5 架构重画 |
| D6：`spec.py` 是唯一机器可读来源 | 未建，且规格值现在在 `utils.py` 与 `shot.py` **各存一份**，`shot.py` 从不 import `utils` | **改案**：唯一来源定为现有 `utils.py`（§5.1） |
| D5：`05_assets/fx/` 提升到与 chr/env/prp/veh/lib 平级 | 未执行。目录不存在，`dls.md` §3.1/§6.6 未改 | §6 待修项 |
| D6 依据「`06_shots/seq040/sh020/` 不存在」 | 该目录**存在**，但 `seq040` 与真实镜头表 `SEQ010` 冲突——问题性质从"缺失"变成"不一致" | §6 待修项 |
| 磁盘 121 GB vs plan §14.5 要求的 300 GB | 数字没错，但 **plan 自相矛盾**：`docs/plan.md:710` 写 ≥300 GB，附录 B.4（`docs/plan.md:1057`）写 **≥600 GB** | §2.2 记录该矛盾 |
| 6 个 `.blend` 模板待生成 | 仍未生成。`00_project/templates/` 只有 9 份 `.md` | §7 保留设计 |
| 快门换算 `shutter_deg/360 → 0.5` 需断言 | 风险比 v1 判断的更严重：**`motion_blur_shutter` 全仓库从未被写入过一次** | §12 风险 R1 |
| `CR-001` 写入 `scope_lock.md` | 未写入。该文件仍锁 `5.2.1 LTS`，且**签署栏为空** | §8 第 5–7 项 + §8.1 |
| README / `licensing.csv` 同步 5.2.0 | 未做，三处仍写 5.2.1 | §8 第 1、2、4、8 项 |
| — | **v1 完全没有的事**：G0-T4 已补测完成，结论是 AgX 会让青色自发光发白，已落 `shotlist.csv` 的 `view_transform` 列 + `setup_render --view-transform` | 新增 D9（§3） |

**v1 仍然成立、值得保留的部分**：动态 RNA enum 不能用 `enum_items` 校验（现已扩到
`view_transform`）、`motion_blur_shutter` 单位是帧不是角度、`.blend` 往返测试而非"脚本没报错"、
单次散射不进反射的双轨方案、无 GPU 时不填采样数。这些结论被 G0 反复印证，全部保留。

---

## 1. 背景

`docs/plan.md` §19.3（Kill Criteria）规定 G0 未通过则不进入资产制作。v1 写这份文档时
G0 尚未执行，因此把"§22.3 规范与模板"当作绕开 G0 的先行段。

**现在 G0 已执行**（`00_project/bible/g0_feasibility_report.md`）：

| 测试 | 判定 | 与 Kill Criteria 的关系 |
|---|---|---|
| T1 体积雾 | ✅ 通过 | — |
| T2 反射中的体积 | 🟡 部分通过（§2.2 限制成立，Cycles 选项保留） | — |
| T3 10k 实例 GN | ⏸ 需 GPU | 环境问题，非方案问题 |
| T4 AgX 自发光 | 🔴 **不通过**（AgX 让青色发白） | 已定 per-shot 对策（D9） |
| T5 色彩全链路 | ⏸ 阻塞（本机无 DaVinci Resolve） | **色彩偏色风险未排除** |
| T6 EXR multilayer | 🟡 部分通过（多个 5.2 API 陷阱已定位并绕开） | — |

报告结论：G0 未完全通过，但**"技术路线不可行"已被推翻**；未完成项都是环境问题。
因此 §22.3 仍是合理的前置段——Project Bible 定稿、目录结构、镜头模板是 W1/W2 的输入。

T3/T4/T5 的收尾不在本段（§11）。

---

## 2. 实测现状（快照 `8c06178`）

### 2.1 环境事实

下表中带 ✓ 的是**本次由我独立复核**的，非转述：

| 项 | 实测值 | 验证方式 |
|---|---|---|
| Blender 版本 | **5.2.0 LTS** | ✓ `blender --version` |
| build hash | `fbe6228777e7`，built 2026-07-14 01:32:04 | ✓ 同上 |
| 安装路径 | `/opt/data/dev/blender-5.2.0-linux-x64/blender` | ✓ |
| 引擎静态枚举 | `['BLENDER_EEVEE']` | ✓ `bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items` |
| **Cycles 可用性** | **✓ 可用（CPU only）**。`scene.render.engine='CYCLES'` 赋值成功，`hasattr(scene,'cycles')=True`，`device='CPU'`。**枚举里看不到 ≠ 引擎不存在** | ✓ 直接赋值 + 读回 |
| GPU | **无**（`nvidia-smi` 不存在）→ 本机不是渲染机 | ✓ |
| CPU | 20 核 | ✓ |
| 磁盘 `/mnt/data` | 剩余 **121 GB**（147G 总量，已用 19G） | ✓ `df -h` |
| 系统 Python | 3.13，**无 `bpy`** | ✓ |
| DaVinci Resolve | **缺失** → T5 阻塞 | ✓ `command -v` |
| ffmpeg | 7.0.2 静态构建，**无 `drawtext` filter**（未编译 libfreetype） | ✓ |
| Blender 内置 OpenImageIO | 3.1.13.1 可导入（读 multilayer EXR 的唯一可用路径） | 报告 §6.4 |
| Blender 内置 Python | 3.13.13 | 报告 |

### 2.2 plan.md 的内部矛盾（本段无法解决，需另行决策）

| 位置 | 说法 |
|---|---|
| `docs/plan.md:710`（§14.5） | 渲染期峰值空闲 **≥ 300 GB** |
| `docs/plan.md:1057`（附录 B.4） | 渲染期峰值空闲 **≥ 600 GB**，稳态 ≈341 GB，建议渲染盘 2 TB |

实测剩余 121 GB。**两个数都不是本段能解决的**，但必须记录：按 600 GB 算，缺口是当前的 5 倍。
这直接决定"渲染产物能否落盘"，是 W1 之前的硬前置。

### 2.3 代码现状（`00_project/pipeline/`）

| 文件 | 行数 | 状态 |
|---|---|---|
| `utils.py` | 122 | 规格常量 + 11 个函数。**但无人 import 它**（见下） |
| `shot.py` | 334 | 引擎/色彩/输出/Pass/镜头。**模块层直接 `main()`** |
| `review.py` | 386 | 抽层 + VSE 烧录 + ffmpeg 封装。**模块层直接跑 argparse** |
| `asset.py` | 42 | **全是 `# TODO` 空壳**（`create_asset` / `publish_asset` / `load_asset`） |
| `cache.py` | 32 | **全是 `# TODO` 空壳**（`export_cache` / `check_cache`） |
| `shotlist.csv` | 5 行 | 真实镜头表 `SEQ010` sh010–sh050，**含 `view_transform` 列** |
| `tests/` | — | **不存在**。全仓库零 `unittest` / `pytest` |

### 2.4 复核命令

改动本文档的事实前先跑这些。任一条输出与本文档不符，以输出为准并更新本文档：

```bash
cd /mnt/data/dsv/ppsk
git log --oneline -1 && git status --short          # 快照是否还成立
B=/opt/data/dev/blender-5.2.0-linux-x64/blender

# Cycles 可用性（§2.1 最关键的一条，v1 在这里栽了）
$B -b --factory-startup --python-expr "
import bpy
print('ENUM', [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items])
bpy.context.scene.render.engine='CYCLES'
print('CYCLES', bpy.context.scene.render.engine, hasattr(bpy.context.scene,'cycles'), bpy.context.scene.cycles.device)"

# 规格值是否只定义在一处（§5.1 的核心断言）
grep -rn "^FPS\|^RESOLUTION\|^BLENDER_VERSION\|^SHUTTER\|^SENSOR_WIDTH" 00_project/pipeline/

# 快门是否真的被写入（§12 R1）
grep -rn "motion_blur" 00_project/pipeline/ 00_project/bible/*.py

# build hash 是否真的被比较（§12 R2）
sed -n '/def check_blender_version/,/^def /p' 00_project/pipeline/utils.py

# 5.2.1 残留
grep -rn "5\.2\.1" README.md 00_project/bible/scope_lock.md 00_project/bible/licensing.csv

# 目录缺口（§6）
ls 05_assets/ && ls 06_shots/ && df -h /mnt/data | tail -1

# --out/ 垃圾目录是否还在（§6.1）
ls -d -- "--out" 2>/dev/null && echo "BUG 未修"

# 模块层 CLI 是否已收口（§9.3）
python3 -c "import shot, review; print('IMPORT_OK')" 2>&1
```

---

## 3. 决策记录

| # | 决策 | 选择 | 状态 | 理由 |
|---|---|---|---|---|
| **D1** | 第一段实施范围 | §22.3 规范与模板 | **已过时** | G0 已执行，不再被 Kill Criteria 挡住；§22.3 仍是 W1/W2 前置 |
| **D2** | Blender 版本锁 | 锁 **5.2.0** | **已落地** | `utils.py:12` / `project_bible.md` / `plan.md`（9 处）均已改；但 `scope_lock.md` / `README.md` / `licensing.csv` 仍写 5.2.1（§8） |
| **D3** | 模板产出形态 | 全部用 bpy 脚本真实生成 | **未执行** | 结论仍成立，`.blend` 未建 |
| **D4** | Cycles 的地位 | ~~保留但标注本机未验证~~ → **可用（CPU only），双轨两轨都保留** | **被推翻** | v1 的「本机无 Cycles」是测量错误（§2.1）。正确判据是 `hasattr(scene,'cycles')` |
| **D5** | FX 预设目录 | 提升到 `05_assets/fx/` | **未执行** | 目录不存在，`dls.md` §3.1/§6.6 未改 |
| **D6** | 规格的机器可读来源 | ~~`spec.py` 单一来源~~ → **`utils.py` 单一来源** | **改案** | `spec.py` 从未建，而 `utils.py` 已在承担这个角色却无人 import（§5.1） |
| **D7** | 运动模糊 vs Vector Pass | `use_motion_blur=False` + `use_pass_vector=True` | **部分落地** | `setup_passes` 打开了全部可用 Pass（含 vector）；但 `use_motion_blur` 从未被显式写 `False`（靠默认值） |
| **D8** | 9:16 竖屏版 | 只渲染 16:9，后期裁切 | **未执行** | `GUIDE_` 安全框与模板一起待建 |
| **D9** | AgX 发白对策 | **关键 FX 镜头 per-shot 换 `Khronos PBR Neutral`** | **已落地**（G0-T4） | AgX 饱和度损失达 −0.40（`orb_mid`，strength=1.0）；Khronos 同强度只发白 1/7。已落 `shotlist.csv` 的 `view_transform` 列 + `setup_render --view-transform` |
| **D10** | 审阅片烧录路线 | **Blender VSE Text strip**，不用 ffmpeg `drawtext` | **已落地** | 本机 ffmpeg 无 `drawtext`；合成器路线在 5.2 headless 会崩。VSE 路线端到端实测通过 |
| **D11** | 读 multilayer EXR | **Blender 自带 OpenImageIO** | **已落地** | `bpy.data.images.load` 返回 `size=(0,0)`；ffmpeg 也读不了 multilayer。必须先抽层 |
| **D12** | 磁盘缺口 | **不在本段解决** | 待决策 | 121 GB vs plan 内部矛盾的 300/600 GB（§2.2） |

---

## 4. 范围

### 4.1 已交付（不在本段剩余工作里）

| 项 | 落点 |
|---|---|
| G0 技术可行性验证（T1–T6） | `00_project/bible/g0_feasibility_report.md` |
| 探针脚本（可复现） | `00_project/bible/g0_probe_{t1,t4,engines}.py` |
| 镜头表 + `view_transform` 列 | `00_project/pipeline/shotlist.csv` |
| 渲染设置主体（引擎/色彩/输出/Pass） | `shot.py` 的 `set_engine` / `setup_color` / `setup_output` / `setup_passes` |
| 审阅片三步链路 | `review.py` 的 `exr_extract_layer` / `burn_in_frame` / `create_preview` |
| 资产命名校验、版本推导、帧号推导 | `utils.py` |
| 锁定 5.2.0 + build hash 写入 Bible 与 plan | `project_bible.md` / `docs/plan.md` |
| 多个 5.2 API 陷阱的记录与绕开 | `project_bible.md`「Blender 5.2 API 约束」节 |

### 4.2 本段剩余交付

**新增文件**

```
00_project/pipeline/tests/                 两套测试（§10），当前完全不存在
00_project/pipeline/tests/_bootstrap.py
00_project/pipeline/tests/test_utils.py
00_project/pipeline/tests/test_shot.py
00_project/pipeline/tests/test_blend_roundtrip.py
00_project/templates/tpl_layout_v001.blend    ← 以下 6 个为本地产物，不进 Git
00_project/templates/tpl_anim_v001.blend
00_project/templates/tpl_cfx_v001.blend
00_project/templates/tpl_fx_v001.blend
00_project/templates/tpl_light_v001.blend
00_project/templates/tpl_lookdev_v001.blend
```

**改动代码**：`utils.py`（规格归并 + `shutter_frames` + `make_object_name`）、
`shot.py`（去重 + 补快门 + 收 CLI + `apply_preset`）、`review.py`（去重 + 收 CLI）、
`g0_probe_t1.py`（`--out` 改 argparse，§6.1）

**改动文档**：`project_bible.md`（性能预算 + 遗留待办）、`scope_lock.md`（+ CR-001）、
`dls.md`（§3.1 + §6.6）、`plan.md`（§22.1/22.2/22.3 勾选）、`README.md`、`licensing.csv`、`.gitignore`

### 4.3 本段不做

| 项 | 归属 |
|---|---|
| `asset.py` / `cache.py` 的 TODO 实现 | plan §22.5 |
| `audit_shot` / `get_dependencies` / `collect_render` / `upgrade_asset` | plan §22.5 |
| T3 / T5 收尾（需 GPU / 需 Resolve） | 渲染机 |
| Asset Library 注册（用户级偏好，不属项目文件） | plan §22.4 |
| FX 预设 `asset_mark` 打包、竹林 GN 生成器、灯光模板 | plan §22.4 |
| 磁盘缺口方案（§2.2） | 需另行决策（D12） |
| `05_assets/fx/` 的内部结构 | 只建目录本身，内容由 §22.4 按需建立 |

---

## 5. 架构

### 5.1 唯一来源定为 `utils.py`（D6 改案）

v1 设计了 `spec.py` 并让 `check_spec.py` 校验 Bible。它没被建，于是规格值现在**定义了两遍**：

| 常量 | `utils.py` | `shot.py` | `review.py` |
|---|---|---|---|
| `BLENDER_VERSION` | `:12` `"5.2.0"` | `:19` `"5.2.0"` | — |
| `RESOLUTION` | `:15` `(1920,1080)` | `:20` `(1920,1080)` | — |
| `FPS` | `:14` `24` | `:21` `24` | `:24` `24` |
| `SHUTTER_ANGLE` | — | `:22` `180.0` | — |
| `SENSOR_WIDTH` | — | `:23` `36.0` | — |
| 色彩四元组 | `:20-23` | — | — |

关键事实：**`shot.py` 只 `import argparse, os`，从不 import `utils`**。
所以 `utils.py` 里的规格常量除了 `metadata_template` / `frame_range` 之外**无人消费**——
它名义上是唯一来源，实际上是死代码。这正是 v1 的 D6 想消灭的漂移，只是形态不同。

**改法**：

1. `shot.py` 删掉 `:19-23` 五个常量，改 `import utils` 后读 `utils.RESOLUTION` 等
2. `shot.py` 的 `SHUTTER_ANGLE` / `SENSOR_WIDTH` **移入** `utils.py`（它们现在只在 shot.py，utils 不全）
3. `review.py` 删掉 `:24` 的 `FPS`，改读 `utils.FPS`
4. `utils.py` 增加派生函数，把「人读值 → Blender 值」的换算收在一处：

```python
def shutter_frames() -> float:
    """快门角度（度）→ Blender 的 motion_blur_shutter（帧）。180° → 0.5 帧。

    单位是帧不是角度：直接写 180.0 会得到 180 帧模糊且**不报错**。
    """
    return SHUTTER_ANGLE / 360.0
```

5. 加一条可执行的约束（写进 `README.md` 与本文档 §9）：
   **规格值只在 `utils.py` 定义；`grep -rn '^FPS \\|^RESOLUTION \\|^BLENDER_VERSION' 00_project/pipeline/` 应当只命中 `utils.py`。**

`check_spec.py` 不再另立。Bible 的一致性校验降级为 §9.1 描述的轻量做法。

### 5.2 渲染设置预设：不再另立模块

v1 规划了独立的 `render_preset.py`。现在 `shot.py` 的 `set_engine` / `setup_color` /
`setup_output` / `setup_passes` **已经就是**渲染设置预设，且已被 G0 实测验证过。
再立一个 `render_preset.py` 等于把同一套设置写两遍——正是 v1 §7.2 自己反对的事。

改为：给这四个函数加一个统一的 `apply_preset(scene, *, shot, stage, version, view_transform, project_root)`
入口，`setup_render` 与未来的模板生成器都调它。一份实现，两个消费者。

**它目前缺的**（模板化时必须补齐，否则往返测试会红）：

| 缺什么 | 后果 |
|---|---|
| `motion_blur_shutter` 从未写入 | 模板与实际渲染的快门都是 Blender 默认值，不是锁定的 0.5 帧 |
| `use_motion_blur` 未显式写 `False` | 靠默认值，D7 只是巧合成立 |
| 无 View Layer 分层 | 拿不到 plan §21.1「只重渲 `VL_char`」的能力 |
| `color_depth` 单值 `"32"` | 与 plan §7.3「颜色 16-bit Half；数据 32-bit」冲突（§12 R3） |
| `unit_settings` 未设 | 模板无法保证公制 1u=1m |
| 帧范围未设 | 模板无法保证 1001 起 + 8 帧 handles |

### 5.3 数据流

```text
utils.py（唯一规格来源，不 import bpy）
   ├─→ shot.py    set_engine / setup_color / setup_output / setup_passes
   │      └─→ apply_preset()  ← 模板生成器与 setup_render 共用
   ├─→ review.py  FPS / 帧号 → 时码
   └─→ shotlist.csv  view_transform 列（per-shot 数据，不是代码常量）
```

`shotlist.csv` 的 `view_transform` 列是**数据**，不是常量——它随镜头变（D9），
所以它属于镜头表而非 `utils.py`。不要把 per-shot 值硬编码进预设。

---

## 6. 目录结构

现状（快照 `8c06178`）：

```text
00_project/{bible,ocio,pipeline,templates}/     ✅ 齐
01_story/  02_storyboard/  03_editorial/  04_audio/  ✅ 齐
05_assets/
├── chr/hero/{wip,publish}/   ✅ 齐（只有 chr/hero 有 wip/publish，符合 dls.md §3.1）
├── env/  prp/  veh/  lib/    ✅ 齐
└── fx/                        ❌ 缺失（D5 未执行）
06_shots/
├── README.md
└── seq040/sh020/{anim,cache,cfx,comp,fx,layout,light,render}/   ⚠️ 存在但与镜头表冲突
07_review/  08_delivery/  09_archive/                            ✅ 齐
--out/                                                             🗑️ 垃圾目录（§6.1）
```

### 6.1 `--out/` 目录：路径解析 bug 的产物

仓库根有一个名为 `--out` 的目录，内含 `t1_.exr`（74 KB）与 `t4_.exr`（50 KB）。

根因：`00_project/bible/g0_probe_t1.py:26` 写的是

```python
OUT = argv[0] if argv else "/tmp/g0_t1"
```

按**位置**取第一个参数，但同一文件第 14 行的用法说明写的是 `-- --out <目录>`。
照说明调用时 `argv[0] == "--out"`，于是 `OUT` 变成字面量 `"--out"`，
`os.makedirs("--out")` 在仓库根建出目录。而 `g0_feasibility_report.md` §9.3 给出的
复现命令正是 `-- --out /tmp/g0` ——**报告里那条命令本身就会触发这个 bug**。

因为里面只有 `.exr` 而 `.gitignore` 有 `*.exr`，`git status` 看不见它——垃圾静默躺在根目录。

处置（属本段，因为它由规范/工具链产生）：改 `g0_probe_t1.py` 为 argparse 解析
`--out` / `--res`，删掉 `--out/` 目录，并在 §2.4 加一条断言。

### 6.2 `seq040/sh020/` 与镜头表冲突

`dls.md` §3.1 的目录树把 `06_shots/seq040/sh020/` 写成范例，`README.md` 的命名规范也拿
`seq040_sh020` 举例，而真实镜头表是 `SEQ010` 的 sh010–sh050（5 镜）。

这不是"目录缺失"，是**文档范例与真实数据不一致**。真实镜头由
`shot.py::create_shot` 从镜头表创建，编号必须来自镜头表，不得沿用 `seq040`。

处置：把 `dls.md` §3.1 与 `README.md` 的范例改成 `seq010_sh010`；
`seq040/sh020/` 目录保留为空骨架还是删除，由镜头表驱动的 `create_shot` 决定——本段不删目录（§9.2 只增不删）。

### 6.3 不建生成器

v1 规划 `scaffold.py`（幂等、只增不删的目录生成器）。**现在不写**：
目录树已经 95% 建好，缺的是 `05_assets/fx/` 一个目录和两处文档不一致。
为一个已存在的树写生成器是 YAGNI。

改为两步：`mkdir -p 05_assets/fx` + 改 `dls.md` 两处。
`shot.py::create_shot` 已经承担了镜头级目录创建，且有 `--dry-run`。

---

## 7. `.blend` 模板

六个模板的 v1 设计**全部保留**（未执行过，无须改）。补充三点与现状对齐。

### 7.1 共享设置必须补齐

全部模板共享：公制单位、24 fps、帧范围 1001 起 + 8 帧 handles、`frame_current`
落在有效帧起点、色彩管理（含 per-shot `view_transform` 能力）、同一套 collection 骨架。
这些当前**一个都没在代码里**（§5.2 表）。

### 7.2 per-shot View Transform（D9 的延伸）

`project_bible.md` 已锁定「默认 AgX，关键 FX 镜头 Khronos PBR Neutral」，且 `shotlist.csv`
已有 `view_transform` 列。因此：

- 模板 `tpl_light` 烘 **AgX**（默认）
- `apply_preset()` 必须接受 `view_transform` 参数，与 `setup_render` 同签名
- 模板不硬编码任何单镜的 transform 值——那是镜头表的事

### 7.3 9:16 安全框

Blender 无原生第二画幅遮罩。实现为 `GUIDE_` collection 中的 9:16 线框，`hide_render=True`。
渲染输出只出 16:9（D8）。

### 7.4 相机默认值

Bible 未锁 sensor 尺寸但已锁 36 mm（全片统一），plan §13 把 `focal_length` 定为逐镜记录。
模板只固定不随镜头变化的部分：`sensor_width=36`（utils）、`sensor_fit=AUTO`、`lens=35`（**占位值**，
逐镜由镜头表覆盖）、`shift_x/shift_y=0`、`clip_start/end=0.1/1000`。

注意镜头表里 sh010/sh040/sh050 的 `focal_length` 已是 35、sh020 是 50、sh030 是 24、sh050 是 40——
模板的 35 恰好与 sh010 一致纯属巧合，**不要**因此认为镜头表已被消费。

### 7.5 快门换算

v1 的警告仍然完全成立，且更严重：`motion_blur_shutter` 从未被写入过（§12 R1）。
写入时必须走 `utils.shutter_frames()`，往返测试必须断言 `== 0.5`。

---

## 8. 文档改动

只列**仍未落地**的部分。已落地的（`plan.md` 9 处版本号、`project_bible.md` 定稿主体）
不在此列。

| # | 文件 | 位置 | 改动 |
|---|---|---|---|
| 1 | `README.md` | `:9`、`:44` | 5.2.1 LTS → **5.2.0 LTS**（build `fbe6228777e7`） |
| 2 | `README.md` | 落地清单 | 按 plan §22.1/22.2/22.3 实际状态重写；G0 已完成应打勾 |
| 3 | `README.md` | 规范节 | 镜头编号范例 `seq040_sh020` → `seq010_sh010`（§6.2） |
| 4 | `README.md` | 新增一行 | 「规格以 `00_project/pipeline/utils.py` 为唯一来源，改规格改它」（§5.1） |
| 5 | `scope_lock.md` | `:25` | `Blender 5.2.1 LTS` → `Blender 5.2.0 LTS（build fbe6228777e7）` |
| 6 | `scope_lock.md` | 追加 | `## 6. 变更记录` + **CR-001**（模板见 §8.1） |
| 7 | `scope_lock.md` | `## 5. 签署` 前 | 加一句现状声明：**本文件签署栏为空，签署前不构成生效基准** |
| 8 | `licensing.csv` | `:2` | `Blender 5.2.1 LTS` → `5.2.0 LTS`（两处字段） |
| 9 | `dls.md` | §3.1 目录树 | `05_assets/` 下加 `fx/`，与 chr/env/prp/veh/lib 平级（**不加** `wip/publish`） |
| 10 | `dls.md` | §3.1 目录树 | 镜头范例 `seq040/sh020/` → `seq010/sh010/`（§6.2） |
| 11 | `dls.md` | §6.6 | `05_assets/lib/fx/` → `05_assets/fx/`，并写明划分规则：`fx/` 放可发布 FX 预设，`lib/` 放节点组与 GN 生成器 |
| 12 | `plan.md` | §22.1 | 修正两处失实勾选：**管线 API 骨架**——`asset.py` 与 `cache.py` 至今全是 `# TODO` 空壳；**镜头目录骨架**——`seq040/sh020/` 存在但与镜头表 `SEQ010` 冲突 |
| 13 | `plan.md` | §22.2 | G0 勾选并注明 T4 不通过 + 已有对策；「EEVEE 体积实测」勾选（报告 §1.2 已测），「probe 上限」**保持未勾**（只验过枚举存在，未实测上限行为） |
| 14 | `plan.md` | §22.3 | 本段完成项打勾 |
| 15 | `project_bible.md` | 缺失节 | 补 plan §11 性能预算全表（v1 §8.1 要求，至今未补） |
| 16 | `.gitignore` | 补 `*.blend` | 当前只有 `*.blend1` / `*.blend@` / `*.blend#`。plan §15 规定 `.blend` 不进 Git，模板 6 个 `.blend` 若不加规则会被跟踪 |

### 8.1 CR-001 模板

D2 的版本变更实际已经落地（`utils.py`、`project_bible.md`、`plan.md` 都改了），
但 `scope_lock.md` §3.1 规定的四步流程**没走完**——该文件仍锁 5.2.1，且从未签署。
本段补的 CR-001 是**追认**，不是申请：

```markdown
## 6. 变更记录

### CR-001 锁定版本 5.2.1 → 5.2.0（追认）
| 项目 | 内容 |
|---|---|
| 变更日期 | 2026-09-29 |
| 变更项 | 锁定版本：Blender 5.2.1 LTS → **5.2.0 LTS**（build hash `fbe6228777e7`） |
| 原因 | G0 实测本机可用版本为 5.2.0；严格锁 5.2.1 会使全部管线函数无法运行（plan §12.1） |
| 已发生的实际改动 | `utils.py` / `project_bible.md` / `plan.md` 已先行改为 5.2.0，本 CR 为追认 |
| 影响 | plan §7.1 / §12.1 已同步；`README.md` / `licensing.csv` 待本段同步 |
| 未承担的风险 | 5.2.1 若为更新的 patch，本项目将错过其修复；**升级需另开 CR** |
| 决策人 | 待签 |
```

追认而非申请，是因为事实已经改了。不补这个 CR，`scope_lock.md` 就与仓库其余部分互相矛盾。

---

## 9. 实现约束

### 9.1 Bible 规格区块

v1 设计了 `check_spec.py` + 哨兵标记的生成区块。现在不建这个工具（`utils.py` 已是唯一来源，
再加一层同步机制收益不抵复杂度）。降级为：

- `project_bible.md` 的技术规格表**人工维护**，但值必须与 `utils.py` 一致
- 一致性由 §10.1 的测试保证：测试从 `utils` 读值，断言 Bible 文本里出现该值
- 改规格的流程固定为：**改 `utils.py` → 改 Bible → 跑测试**

比生成区块差的地方要认：表格里的**格式**不会被自动纠正，只有**数值**会被抓到。

### 9.2 统一返回约定

```python
# 成功
{"ok": True, ..., "warnings": [...]}
# 失败
{"ok": False, "error": "…", "hint": "…"}
```

现状违规：`asset.py` 与 `cache.py` 返回 `{"asset": …, "status": …}`，**连 `ok` 键都没有**。
两者本段不做（§4.3），但它们的返回值不得被当作成功判据。

其余约束不变：所有函数接受 `project_root`；只读函数绝不写盘；写盘函数有 `--dry-run`
（`shot.py` 与 `review.py` 已有）。

### 9.3 模块层不得执行 CLI

**这是本段的新前置条件，v1 不知道它的存在。**

`shot.py:334` 是裸的 `main()`，`review.py:367-386` 是模块层的 `argparse` 构造与解析。
后果（已实测）：

```
$ python3 -c "import shot"
--engine {EEVEE,CYCLES}      ← argparse 的 help 被打印到 stdout
IMPORT_OK
```

`import shot` / `import review` 都会执行 CLI。任何测试、任何 `from shot import setup_render`
都会先打印 help；`--project-root` 之类的参数还可能被误解析。

必须改成：

```python
if __name__ == "__main__":
    sys.exit(main())
```

`asset.py` / `cache.py` 已经是对的，照它们的样子改。
**这一条不修，§10 的测试一行都建不起来**，所以它是 Task 0。

### 9.4 命名：对象名 vs 资产 ID

v1 要求新增 `utils.make_object_name(prefix, name)` 保留大写前缀（`GEO_` / `CAM_` / `LGT_`），
因为 `normalize_name` 会转小写（`utils.py:62`），用它处理对象名会得到 `geo_grayball`，
违反 `dls.md` 的前缀规范。

现状：`make_object_name` **仍未实现**；`utils.py` 里只有 `normalize_name`。
新增该函数，同时在 `project_bible.md` 命名规范表写明适用边界：
**资产 ID 用 `normalize_name`，对象名用 `make_object_name`。**

### 9.5 `dls.md` 是目录结构的权威

只对 `chr/hero` 建 `wip/publish`（§6 的现状已符合）。`env` / `prp` / `veh` / `lib` / `fx` 平铺。
`dls.md` §3.1 只对 `chr/hero` 画了 `{wip, publish}`，**不擅自推广**——那属于对权威规范的扩展，
应在 `dls.md` 里显式决定。

---

## 10. 验证

### 10.1 两套运行环境

| 模块 | 依赖 bpy | 跑在哪 |
|---|---|---|
| `utils.py` | 否 | 系统 `python3` |
| `shot.py` / `review.py` | 部分（纯函数不需要，`*_preset` 需要） | 两者皆可，按函数区分 |
| 模板生成 | 是 | `blender -b` |

不 import bpy 的硬约束继续换来"多数代码无需开 Blender 即可测试"。

### 10.2 `.blend` 往返测试（核心）

只测"脚本没抛异常"是空的。已实测证明存在静默失效：色彩管理的 `view_transform` 是动态 RNA
enum，headless 下 `enum_items` 只返回 `['NONE']`（已记入 `project_bible.md` 的 API 约束表），
用枚举校验会让**任何**检查假通过。验收必须是往返：

```text
生成 6 个 .blend
      ↓
blender -b 重新打开每个
      ↓
逐项断言：分辨率 / fps / 单位 METRIC / shutter == 0.5 /
        engine=BLENDER_EEVEE / view_transform=AgX / look=None / display=sRGB /
        帧范围 / EXR 格式与位深 / collection 齐全
      ↓
全对 → 退出 0；任一项不符 → 打印实际值并退出 1
```

**只验证"设置落进了文件"，不验证"渲染出来对"。** `use_pass_z is True` 能断言，
Depth pass 内数据是否正确只有真渲一帧才知道；本机无 GPU，那次渲染不构成可信证据。

Blender 侧测试必须用 `TextTestRunner` + `loadTestsFromModule` 再
`sys.exit(0 if result.wasSuccessful() else 1)`，**不能用 `unittest.main()`**——
后者解析 `sys.argv`，而 Blender 传进来的是它自己的参数，失败用例不会让命令失败。

### 10.3 元测试：证明校验器不是摆设

`test_utils.py` 必须包含"改坏一个值 → 测试变红 → 改回来 → 变绿"。
若改坏了仍然全绿，说明断言是装饰品，后续所有"已校验"声明都不成立。

### 10.4 错误处理

| 情况 | 行为 |
|---|---|
| Blender 版本号前两段 ≠ `5.2` | 退出码非 0，打印实际版本（§5.1） |
| build hash 与记录不符 | **警告**，实际 hash 写入报告，继续（§5.1） |
| 目标 `.blend` 已存在 | **跳过并报 `skipped`**，不覆盖；覆盖需显式 `--overwrite` |
| HDRI 缺失（LookDev） | 警告，**不伪造**纯色环境 |
| `--project-root` 下无 `00_project/` | 退出码非 0 + 提示，**不建任何东西** |
| `--dry-run` | 以 mtime 验证不写盘，不信返回值 |

### 10.5 验收清单

- [ ] `utils.py` 是规格值唯一来源；§2.4 的 grep 只命中 `utils.py`
- [ ] `shot.py` / `review.py` 的 CLI 已收进 `if __name__ == "__main__"`（§9.3）
- [ ] `import shot` / `import review` 静默无输出
- [ ] `motion_blur_shutter == 0.5` 在每个模板中成立
- [ ] `check_blender_version` 两级：版本号前两段不符则失败，hash 不符只警告
- [ ] 6 个 `.blend` 生成，**重新打开后**规格逐项断言通过
- [ ] `make_object_name` 存在，保留大写前缀
- [ ] 元测试：改坏 `utils.py` 一个值后测试变红（§10.3）
- [ ] Bible 数值与 `utils.py` 一致（由测试断言）
- [ ] §8 的 16 项文档改动全部落地，`CR-001` 写入 `scope_lock.md` 并标注**待签署**
- [ ] `.gitignore` 含 `*.blend`；`git check-ignore 00_project/templates/tpl_light_v001.blend` 命中
- [ ] `--out/` 已删除，`g0_probe_t1.py` 改用 argparse
- [ ] 所有生成器 `--dry-run` 不写盘（以 mtime 验证）

---

## 11. 明确不在本段验证

| 项 | 原因 |
|---|---|
| EEVEE 渲染画质与单帧耗时 | 无 GPU，本机不是渲染机 |
| `volumetric_samples` / `taa_render_samples` 取值 | 无 GPU 时定的采样数无意义 → 不填，交给渲染机 |
| T3 10k 实例 GN 散布 | 需 GPU |
| T5 色彩全链路（含 Resolve） | 本机无 DaVinci Resolve |
| Pass 内容正确性 | 需真渲一帧；本段只验证设置落地 |
| 磁盘缺口（§2.2） | 121 GB vs plan 内部矛盾的 300/600 GB，需另行决策（D12） |
| HDRI 成片效果 | HDRI 文件本身属 §22.4 / §16 授权登记 |

---

## 12. 风险

| # | 风险 | 应对 |
|---|---|---|
| **R1** | **`motion_blur_shutter` 全仓库从未被写入**。`shot.py:226` 的 `setup_camera()` 只在返回值里报告 `shutter_angle`，从不落到场景上。锁定的 180° 快门目前**没有任何代码在执行** | 走 `utils.shutter_frames()` 写入；往返测试断言 `== 0.5`（§7.5） |
| **R2** | **`BLENDER_BUILD_HASH` 从未被比较**。`check_blender_version` 读出 `bh`、解码、放进返回值，然后就没了；`BLENDER_BUILD_HASH` 唯一使用处是 `metadata_template`。同时 `ver != BLENDER_VERSION` 是三段全等，官方 5.2.0 发行版（本机是 dev build）会被误杀 | 实现 v1 §5.2 的两级规则：版本号比前两段，hash 只警告（§5.1） |
| **R3** | `color_depth` 冲突：`shot.py:145` 设单值 `"32"`，但 plan §7.3 与 `project_bible.md` 都要求「颜色 16-bit Half；数据 Pass 32-bit」。multilayer EXR 的位深是文件级属性，**可能无法同时满足** | 本段记录为待决策，不擅自改。渲染机上实测后定（§11） |
| **R4** | 动态 RNA enum 陷阱已扩散：`view_transform` 与 `engine` 一样，headless 下 `enum_items` 只返回 `['NONE']` | 所有 enum 一律"赋值 + 读回验证"，禁用 `enum_items` 做前置校验（已记入 `project_bible.md`） |
| **R5** | 规格值漂移：`utils.py` 名义唯一但 `shot.py` 从不 import 它（§5.1） | Task 0 归并；验收清单用 grep 卡住 |
| **R6** | 磁盘 121 GB vs plan 要求的 300/600 GB（且 plan 自相矛盾） | 不在本段解决；渲染产物落盘前重新检查（D12） |
| **R7** | 本机 ffmpeg 无 `drawtext`、合成器 headless 崩溃——渲染机环境可能不同，VSE 路线的行为需在渲染机复核 | 记录在 `g0_feasibility_report.md` §9.3；渲染机复核前不宣称跨机可用 |
| **R8** | `scope_lock.md` 始终未签署，却已是事实上的范围基准 | 本段在文件中显式声明"签署前不构成生效基准"，并追认 CR-001 |
| **R9** | 本文档的事实快照会过期（仓库正在被并行会话改动） | §2.4 复核命令；**先跑命令再引用本文档** |

---

## 13. 术语与引用

| 缩写 | 含义 |
|---|---|
| D1–D12 | §3 的决策（D4 已推翻，D6 已改案，D9–D11 为 G0 期间新增） |
| CR | `scope_lock.md` 的变更记录（Change Request） |
| G0 | plan §5.0 技术可行性门禁 |
| VL | View Layer |
| T1–T6 | G0 的六项测试，结论见 `g0_feasibility_report.md` |
| 往返测试 | 生成 → 重新打开 → 读回断言（§10.2） |
| 追认 | 变更已实际发生，补记录以对齐文档，而非申请许可（§8.1） |
