# G0 技术可行性验证报告

> **依据**：`docs/plan.md` §5.0（第 0 周：G0 技术可行性验证，前置，不可跳过）
> **Blender**：`/opt/data/dev/blender-5.2.0-linux-x64/blender` — 5.2.0 LTS，build hash `fbe6228777e7`
> **日期**：2026-09-29
> **修订**：v2 — **推翻 v1 的 T1 结论与 §4.1**。v1 的 T1 测量方法有缺陷，Cycles 探测方法也错了。
**v2 补充**：管线代码实测又发现 4 个新问题（§6.4–6.7），均已修复。
> **结论**：🟡 **T1 通过、T2 部分通过**；T3/T4/T5 因环境条件未完成；T6 部分通过

---

## 0. 修订说明（v2 对 v1 的更正）

v1 报告有两个错误，都会误导后续决策：

| v1 结论 | 实际情况 | 错误原因 |
|---|---|---|
| T1 不通过，体积"完全没参与渲染"，建议执行降级 L2 | ❌ **错**。体积正常工作，T1 **通过** | 测量设计失败：太阳正对镜头使基线过曝（mean 0.72 / max 2.34，画面已饱和），雾的散射贡献被淹没；同时雾盒挡住直射光使 max 反降 0.84。误把饱和当成"无贡献" |
| Cycles 不可用，§2.2 双轨方案中"局部 Cycles"整轨删除 | ❌ **错**。Cycles **可用** | 用 `bpy.types.RenderSettings.engine` 的**静态枚举**判断。`-b` 无界面模式下该枚举只注册 EEVEE，即使 Cycles addon 已启用、`_cycles` 可导入 |

**如果按 v1 执行降级 L2，会白改一堆文档。**

---

## 1. T1 — 云海 + 逆光 + 体积雾：✅ 通过

### 1.1 修正后的测试设计

**核心原则**：场景中**不放任何几何体**，唯一的像素来源就是雾本身。这样雾的贡献无法被遮挡或曝光淹没。

- 场景：无地面、无物体，只有一个太阳（energy=10）
- 雾：Volume Principled，Color `(0.9, 0.92, 0.95)`，Density `0.25`，盒 size=10 位于 `(0, -3, 2)`（完全在画面内，不含相机）
- EEVEE：`use_raytracing=True`、`volumetric_samples=96`、`volumetric_end=60`
- 相机：`(0, -14, 1.8)`，45mm
- 输出：EXR 32-bit，320×180

### 1.2 结果

| 配置 | mean | max | 非零通道 | 耗时 |
|---|---|---|---|---|
| 无雾（世界背景） | 0.250000 | 1.0000 | 57600 / 230400 | 0.7 s |
| **有雾** | **0.725610** | 1.0000 | **230400 / 230400** | 1.2 s |
| **差值** | **+0.475610** | — | — | — |

非零通道从 25% 涨到 100%，画面从纯背景色变为雾充满全屏。

**判定：EEVEE 体积在无 GPU 环境下正常工作。T1 通过。**

### 1.3 交叉验证：T2 场景

在水面/反射场景中独立复测，同样确认雾有贡献：

| 引擎 | 无雾 mean | 有雾 mean | 差值 |
|---|---|---|---|
| EEVEE | 0.27457 | 0.45288 | **+0.17831** |
| Cycles | 0.27462 | 0.33264 | +0.05802 |

**两组独立场景结论一致。**

---

## 2. T2 — 体积在水面/古镜反射中的表现：🟡 部分通过

`plan.md` §2.2 列出两条 EEVEE 限制：

| 限制 | 实测 | 判定 |
|---|---|---|
| 体积只对相机光线渲染，不进入反射/折射和 light probe | **复现**。EEVEE 雾 +diff **+0.178**，Cycles 雾 +diff **+0.058** —— EEVEE 的雾贡献反而更大，说明反射中确实没有雾 | ✅ 手册所述限制**成立** |
| 体积阴影不投到实体物体上 | 未单独隔离测试 | ⏸ 未验证 |

**判定：§2.2 的判断得到实测确认 —— EEVEE 的反射里看不到雾。**

**这直接支持 plan.md §2.2 的双轨方案结论**（"云海的主要表现力应放在合成层"），
但**不是降级 L2 的理由** —— L2 是因为 T1 不通过才触发的，T1 通过了。

**待办**：T2 的完整判据是"缺失可接受，**或该元素单独走 Cycles**"。既然 Cycles 可用，
该选项保留。水面/古镜中的雾若必须存在，走 Cycles 局部渲染。

### 2.1 Cycles 可用性（修正 v1 §4.1）

| 检查 | 结果 |
|---|---|
| `engine` 静态枚举（`-b` 模式） | `['BLENDER_EEVEE']` ← **误导来源** |
| cycles addon | `(True, True)` 已启用 |
| `_cycles` 二进制模块 | 可导入，30 个符号 |
| **直接赋值 `scene.render.engine = 'CYCLES'`** | **✅ 成功** |
| `scene.cycles` | 存在，`device=CPU samples=4096 denoising=True` |
| 实测渲染 | ✅ 成功，0.2 s，max=1.83 |
| Cycles 算力设备 | `compute_device_type` 枚举**为空** → 仅 CPU |

**结论：Cycles 可用（CPU only）。§2.2 双轨方案两轨都保留。**

> **管线影响**：`00_project/pipeline/shot.py` 的 `setup_render` 若要支持混用 Cycles，
> **不能用 `engine` 枚举做分支判断**，必须 `try: scene.render.engine = 'CYCLES'` + 检查 `scene.cycles`。

---

## 3. T3 — 竹林逆光剪影（10k 实例 GN 散布）：⏸ 未完成

判据是"单帧 < 90 秒"，**需要 GPU 才有意义**。本机无 GPU：

| 项 | 实测 |
|---|---|
| GPU | 无（`nvidia-smi` 不存在） |
| CPU | 20 核 |
| EEVEE 软件 GL 单帧（320×180） | 0.7–1.2 s |
| 按像素线性外推 1920×1080 | 约 25–45 s/帧 |

外推数字**只能说明本机不是渲染机**，不能作为 T3 结论。
10k 实例 GN 散布的**几何与性能可行性**可在渲染机上验；剪影质量的目视判断也需要在渲染机上看。

---

## 4. T4 — 自发光法术光球在 AgX 下的表现：⏸ 未完成

依赖 AgX + 自发光的像素级比对。技术上本机可做（EEVEE headless 正常），
但需要先确定测试球的发光强度基准与判定阈值，**且该项优先级低于 T1/T6**。
未做，不臆测结论。

---

## 5. T5 — 色彩全链路验证：⏸ 阻塞

判据要求对比"Blender 视口 / Blender 合成输出 / **Resolve** / 导出 MP4"四处。
本机**无 DaVinci Resolve**（实测 `command -v resolve` 无结果）。

§9.1 已警告色彩链路"极易静默偏色，且偏色在最后交付时才发现，返工要重渲全片"。
**该风险目前未被排除。**

可在渲染机先做"Blender 视口 / Blender 合成输出 / 导出 MP4"三处对比，
Resolve 一环待补。

---

## 6. T6 — Headless 渲染 + EXR multilayer：🟡 部分通过

### 6.1 发现 1：5.2 的 EXR multilayer 设置顺序（已确认，可直接写进管线）

直接设 `file_format` 会失败：

```
TypeError: enum "OPEN_EXR_MULTILAYER" not found in
  ('AVIF','JPEG','OPEN_EXR','PNG',...)
```

**5.2 正确顺序**（`media_type` 切换后 `file_format` 的合法枚举会变）：

```python
ims = sc.render.image_settings
ims.media_type = 'MULTI_LAYER_IMAGE'    # 必须先设
ims.file_format = 'OPEN_EXR_MULTILAYER'  # 此时才合法
```

✅ 实测通过，输出 197 KB multilayer EXR。

### 6.2 发现 2：EEVEE **没有** Volume Pass

实测 `view_layer` 可用 Pass 全集：

```
use_pass_combined, use_pass_z, use_pass_vector, use_pass_position,
use_pass_normal, use_pass_uv, use_pass_mist, use_pass_object_index,
use_pass_material_index, use_pass_shadow, use_pass_ambient_occlusion,
use_pass_emit, use_pass_environment,
use_pass_diffuse_direct/indirect/color, use_pass_glossy_direct/indirect/color,
use_pass_transmission_direct/indirect/color,
use_pass_subsurface_direct/indirect/color, use_pass_grease_pencil,
use_pass_cryptomatte_object/material/asset/accurate
```

**没有 `use_pass_volume`。** 赋值会报
`AttributeError: 'ViewLayer' object has no attribute 'use_pass_volume'`。

> **影响**：`plan.md` §7.3 的 Pass 列表里没有 Volume Pass，本项一致；
> 但若后期想单独调整雾，只能走 Combined 或合成雾层，**不能靠 Volume Pass 分离**。
> 这进一步支持 §2.2 "雾放合成层"的做法。

### 6.3 发现 3：ffmpeg 读不了 multilayer EXR

```
[exr @ ...] Missing red channel / green / blue
codec_name=exr  width=0  height=0
ffmpeg → PNG: Nothing was written into output file
```

**影响 §6.1 的强制要求**："每次提交必须附带烧录信息的审阅片"。
`create_preview` 用 FFmpeg 生成，**当前无法直接用 ffmpeg 从 multilayer EXR 出片**。

**必须补**：`create_preview` 增加 `exr_extract_layer()` 前置步骤
（先抽 Combined 层为单层 EXR 或 PNG，再交给 ffmpeg 烧录）。

### 6.4 发现 4：`bpy.data.images.load` 读不了 multilayer EXR

```python
img = bpy.data.images.load("....multilayer.exr")
img.size    # → (0, 0)
img.channels # → 0
img.pixels  # → 空
```

**必须改用 Blender 自带的 OpenImageIO**（实测 3.1.13.1，可导入）：

```python
import OpenImageIO as oiio
inp = oiio.ImageInput.open(path)
spec = inp.spec()
spec.channelnames  # → ['ViewLayer.Combined.R', '.G', '.B', '.A']
px = inp.read_image(format=oiio.FLOAT)  # → numpy.ndarray, shape (h, w, 4)
```

multilayer EXR 的通道名带 `ViewLayer.<层名>.` 前缀。第一个 subimage 即 Combined，
已是 RGB(A) 顺序，写单层 EXR 时 ffmpeg 就能读。

`pipeline/review.py` 的 `exr_extract_layer()` 已按此实现并实测通过。

### 6.5 发现 5：本机 ffmpeg 缺 `drawtext`（阻塞 §6.1 烧录要求）

```
$ ffmpeg -hide_banner -filters | grep drawtext
（无输出）
$ ... -vf drawtext=...
No such filter: 'drawtext'
```

本机 ffmpeg 7.0.2 **静态构建未编译 libfreetype**，无 `drawtext` filter
（`drawbox` / `overlay` 有）。而 §6.1 强制要求：

> 每次提交必须附**带烧录信息的审阅片**（镜号 + 阶段 + 版本 + 帧号 + 时码）

字体文件本身齐全（`/usr/share/fonts/` 有 Noto、FreeMono 等），**缺的是 filter**。

**影响**：`create_preview` 在本机**无法产出合规审阅片**。

`create_preview` 已加前置探测，缺 drawtext 时**明确报错而非静默跳过烧录**：

```python
{"ok": False,
 "error": "ffmpeg 缺少 drawtext filter（未编译 libfreetype）",
 "hint": "§6.1 要求烧录镜号+阶段+版本+帧号+时码，缺 drawtext 无法满足。
          换用带 libfreetype 的 ffmpeg 构建，或用 Blender 合成器烧录后输出"}
```

无烧录版本（`-c:v libx264`，无 `-vf`）实测可出，4 帧 320×180 → 0.167 s，
但**不合规**，仅供内部快速预览。

**待决策**：渲染机上换 ffmpeg 构建，还是改用 Blender 合成器烧录。

### 6.6 发现 6：帧序列占位符用 `#` 不是 `%04d`

```python
r.filepath = ".../seq010_sh010_light_v001.%04d"   # ❌
# → 产出 xxx.%04d.exr0023.exr  （双扩展名，%04d 未被替换）
r.filepath = ".../seq010_sh010_light_v001.####"    # ✅
# → 产出 xxx.0023.exr
```

Blender 会自己补 `.exr` 扩展名，`%04d` 被当普通字符。
`pipeline/shot.py` 的 `setup_output` 已修正，**已实测验证文件名正确**。

### 6.7 发现 7：管道函数的 sys.argv 需切掉 Blender 自身参数

```
$ blender -b --factory-startup --python shot.py -- --setup_render sh010 light
error: unrecognized arguments: -b --factory-startup --python 00_project/pipeline/shot.py
```

`blender --python x.py -- <args>` 时 `sys.argv` 仍含 `-b --factory-startup ...`，
直接交给 argparse 会报未识别参数。需 `sys.argv[sys.argv.index("--")+1:]`。

`shot.py` 与 `review.py` 的 CLI 已加 `_argv()` 处理。

### 6.8 发现 8（未验证）

Pass 齐全性未能枚举 —— `bpy` 的 `image.layers` 在 5.2 读 multilayer 时不返回层名。
需改用 OIIO `ImageInput.spec().channelnames` 枚举（已在抽层实现中可用）。


`import OpenEXR` 失败。QC 流程（§17.2 色彩验证、坏帧检查）需要逐像素读 EXR。
→ **已解决**：改用 Blender 自带的 OpenImageIO，见 §6.4。

---

## 7. 执行环境（实测）

| 项 | 实测值 | plan.md 要求 | 判定 |
|---|---|---|---|
| Blender 路径 | `/opt/data/dev/blender-5.2.0-linux-x64/blender` | — | — |
| Blender 版本 | **5.2.0 LTS**, hash `fbe6228777e7` | **5.2.1 LTS** | ⚠️ patch 不一致 |
| Cycles | 可用（CPU only） | §2.2 局部高精 | ✅ |
| EEVEE headless | 可用 | 默认渲染器 | ✅ |
| GPU | 无 | §14.4 RTX 4090 | 🔴 需换渲染机 |
| CPU | 20 核 | — | — |
| ffmpeg / ffprobe | 可用 | §6.1 审阅片 | ✅（但需抽层） |
| DaVinci Resolve | **缺失** | §8 / T5 | 🔴 T5 阻塞 |
| Python OpenEXR | 缺失 | QC 逐像素读 EXR | ✅ 改走 Blender 自带 OIIO 3.1.13.1 |
| ffmpeg `drawtext` | 🔴 **缺**（静态构建无 libfreetype） | §6.1 烧录审阅片 | 🔴 阻塞 |

### 7.1 Blender 版本决策（待定）

`plan.md` §12.1 规定管线"启动即校验 Blender 版本 == `5.2.1`，不匹配直接退出"。
本机为 **5.2.0**，按此约定管线函数现在跑不起来。

另外 `00_project/bible/project_bible.md` 目前仍是仓库模板原样
（写"Blender 5.2 LTS"、命名示例 `chr_hero_default`），build hash 尚未写入。

**需决策**：升到 5.2.1，还是把 Bible 的版本锁改为 5.2.0。

---

## 8. G0 判定

| # | 测试项 | 判定 |
|---|---|---|
| T1 | 云海 + 逆光 + 体积雾 | ✅ **通过** |
| T2 | 体积在反射中的表现 | 🟡 部分通过（§2.2 限制成立，Cycles 选项保留） |
| T3 | 竹林 10k 实例 | ⏸ 未完成（需 GPU） |
| T4 | AgX 自发光 | ⏸ 未完成 |
| T5 | 色彩全链路 | ⏸ 阻塞（无 Resolve） |
| T6 | EXR multilayer | 🟡 部分通过（**6 个管线 bug 已定位并修复，实测通过**） |

**整体：未完全通过，但 v1 报告的"技术路线不可行"结论已被推翻。**

T1/T2 这两个最关键的技术假设**已验证成立**：
EEVEE 体积在本机可用、Cycles 可用、§2.2 双轨方案两轨都保留。
剩余未完成项（T3/T4/T5）**都是环境问题，不是方案问题**。

按 §19.3，"G0 未通过 → 不进入 W5 资产制作"的硬性停止线**暂不触发**，
但 T3/T5 应在渲染机上补完后再正式关闭 G0。

---

## 9. 待办

### 9.1 渲染机上补做（阻塞 G0 关闭）

1. **T3**：10k 实例 GN 散布，单帧计时 + 剪影质量
2. **T4**：AgX 下自发光是否发白
3. **T5**：色彩全链路（含 Resolve 一环）
4. **T6 补验**：Pass 齐全性枚举

### 9.2 已完成（管线代码实测通过）

| # | 事项 | 落点 | 验证 |
|---|---|---|---|
| 1 | 锁 Blender **5.2.0** + build hash `fbe6228777e7` | `project_bible.md`、`pipeline/utils.py` | ✅ `check_blender_version()` |
| 2 | 色彩四元组 / 1920×1080@24fps / 快门 180° | `pipeline/shot.py`、`project_bible.md` | ✅ `setup_color()` |
| 3 | EXR multilayer 顺序（先 `media_type`） | `pipeline/shot.py` → `setup_output` | ✅ 实渲出正确 EXR |
| 4 | 帧序列占位符 `#` 不用 `%04d` | `pipeline/shot.py` | ✅ 文件名实测正确 |
| 5 | Cycles 分支不用枚举，用 `hasattr(scene,'cycles')` | `pipeline/shot.py` → `set_engine` | ✅ EEVEE/Cycles 双分支 |
| 6 | `exr_extract_layer()` 走 Blender 自带 OIIO | `pipeline/review.py` | ✅ 抽出 ffmpeg 可读单层 EXR |
| 7 | `create_preview` 前置探测 drawtext，缺则明确报错 | `pipeline/review.py` | ✅ 错误信息可操作 |
| 8 | `sys.argv` 切掉 Blender 自身参数 | `pipeline/shot.py`、`review.py` | ✅ CLI 可用 |
| 9 | 记录 EEVEE 无 Volume Pass + 5.2 API 约束 | `project_bible.md` | — |
| 10 | 清理冲突的 `01_story/shotlist.csv` | 仓库 | ✅ 已删，重写 pipeline 版 |
| 11 | shotlist 帧号按 §13 修正（frame/shot 原来写反了） | `pipeline/shotlist.csv` | ✅ 有效帧 720 / 渲染帧 800 |
| 12 | 资产命名校验（拒 `final2` 等） | `pipeline/utils.py` | ✅ |

### 9.3 仍待决策

| # | 事项 | 说明 |
|---|---|---|
| 1 | **ffmpeg drawtext** | 本机静态构建无 libfreetype，§6.1 烧录审阅片做不出。换 ffmpeg 构建，还是改用 Blender 合成器烧录？ |
| 2 | 渲染机 ffmpeg | 渲染机若同样是静态构建，同样阻塞 |
| 3 | T3 / T4 / T5 | 需 GPU / 需 Resolve |
| 4 | `docs/plan.md` 的 5.2.1 表述 | 与 Bible 的 5.2.0 不一致，以 Bible 为准，建议同步 plan.md |


### 9.3 探针脚本（已验证可复现）

| 脚本 | 用途 |
|---|---|
| `g0_probe_t1.py` | 体积雾验证（**已修正测量方法**） |
| `g0_probe_engines.py` | 引擎可用性（绕过静态枚举） |

```bash
B=/opt/data/dev/blender-5.2.0-linux-x64/blender
$B -b --factory-startup --python 00_project/bible/g0_probe_engines.py
$B -b --factory-startup --python 00_project/bible/g0_probe_t1.py -- --out /tmp/g0
```

---

## 附：Blender 5.2 API 备忘（全部实测）

```python
# 1. 引擎 ID 是 'BLENDER_EEVEE'（不是 'BLENDER_EEVEE_NEXT'）
sc.render.engine = 'BLENDER_EEVEE'

# 2. Cycles 在 -b 模式下的静态枚举里看不到，但可直接赋值（必须 try/except）
try:
    sc.render.engine = 'CYCLES'
    assert hasattr(sc, 'cycles')
except Exception:
    sc.render.engine = 'BLENDER_EEVEE'

# 3. EXR multilayer：必须先 media_type
ims = sc.render.image_settings
ims.media_type = 'MULTI_LAYER_IMAGE'
ims.file_format = 'OPEN_EXR_MULTILAYER'

# 4. EEVEE 体积属性（实测存在于 scene.eevee）
# use_raytracing / use_volume_custom_range / volumetric_start / volumetric_end
# volumetric_samples / volumetric_tile_size / volumetric_sample_distribution
# use_volumetric_shadows / volumetric_ray_depth / volumetric_shadow_samples
# fast_gi_* / clamp_volume_direct / clamp_volume_indirect

# 5. EEVEE 没有 Volume Pass —— 别写 use_pass_volume
# 全部可用 Pass 见 §6.2

# 6. Workbench 在 -b 无界面模式下全黑（无 GL 上下文），不可用于自动化检查
```
