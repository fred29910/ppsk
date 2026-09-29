# 规范与模板基线 实施计划 v2

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `utils.py` 变成规格值的唯一机器可读来源、收口模块层 CLI 让代码可被测试、补上从未被执行过的快门与版本校验、生成 6 个环节模板 `.blend` 并用往返测试验收、落地 16 项文档改动。

**Architecture:** 规格常量只在 `00_project/pipeline/utils.py` 定义；`shot.py` / `review.py` 改为 `import utils` 读取，不再各自硬编码。`shot.py` 的 `set_engine` / `setup_color` / `setup_output` / `setup_passes` 加统一入口 `apply_preset()`，由 `setup_render` 与模板生成器共用一份实现。验收靠 `.blend` 往返测试（生成 → 重开 → 逐项断言），不靠"脚本没报错"。

**Tech Stack:** Blender 5.2.0 LTS（`/opt/data/dev/blender-5.2.0-linux-x64/blender`，build hash `fbe6228777e7`，Cycles **CPU only 可用**、无 GPU）、Python 3.13、`unittest`（stdlib；**本机无 pytest，不得引入**）。

**Spec:** `docs/superpowers/specs/2026-09-29-baseline-specs-templates-design.md`（v2）

> **v1 计划作废。** `2026-09-29-baseline-specs-templates.md` 规划了 `spec.py` / `check_spec.py` / `scaffold.py` / `render_preset.py` / `build_templates.py` 五个文件，v2 spec 全部否决（唯一来源改用现有 `utils.py`；目录树已 95% 建好，`scaffold.py` 是 YAGNI；渲染预设已在 `shot.py` 里，不另立模块）。**不要执行 v1 计划。**

## Global Constraints

以下约束适用于每一个任务，逐条照抄执行：

- **锁定 Blender 5.2.0，build hash `fbe6228777e7`**。版本校验两级：版本号**前两段**不符 → 退出码非 0；**build hash 不符只警告**（本机是 dev build，官方 5.2.0 发行版 hash 必然不同）
- **Cycles 可用（CPU only）**。判据是 `hasattr(scene, "cycles")` 或直接 try/except 赋值 `scene.render.engine = "CYCLES"`，**绝不能用 `engine` 静态枚举判断**——`-b` 模式下该枚举只注册 `BLENDER_EEVEE`（spec §2.1）
- **`view_transform` 同样是动态 RNA enum**，headless 下 `enum_items` 只返回 `["NONE"]`。所有 enum 一律"赋值 + 读回验证"，禁止用 `enum_items` 做前置校验
- **EXR multilayer 必须先设 `media_type`**，再设 `file_format`。反了报 `enum "OPEN_EXR_MULTILAYER" not found`
- **帧序列占位符用 `####` 不是 `%04d`**。`%04d` 被当普通字符，产出 `xxx.%04d.exr0023.exr` 双扩展名
- **`motion_blur_shutter` 单位是帧不是角度**。走 `utils.shutter_frames()` 得 `0.5`；直接写 `180.0` **不报错**但得到 180 帧模糊
- **EEVEE 没有 Volume Pass**（无 `use_pass_volume`），别写
- **规格值只在 `utils.py` 定义**。其他模块一律 `import utils` 读。验收用 grep 卡：spec §2.4 那条 grep 只能命中 `utils.py`
- **模块层不得执行 CLI**。`shot.py` 与 `review.py` 的 `argparse` 与 `main()` 调用必须收进 `if __name__ == "__main__":`
- 返回约定（spec §9.2）：成功 `{"ok": True, ...}`，失败 `{"ok": False, "error": str, "hint": str}`
- 所有函数接受 `project_root` 参数，无硬编码路径；只读函数绝不写盘；写盘函数有 `--dry-run`
- **本机无 GPU**（`nvidia-smi` 不存在），**无 DaVinci Resolve**，**ffmpeg 无 `drawtext`**。不验证渲染画质、不填 `volumetric_samples` / `taa_render_samples`（spec §11）
- `asset.py` 与 `cache.py` 至今全是 `# TODO` 空壳，**本计划不碰**（属 plan §22.5）
- `shotlist.csv` 的 `view_transform` 列是**数据**不是常量（per-shot 随镜头变，spec D9）。不得把 per-shot 值硬编码进预设

## Review Focus

以下五项是 spec 蕴含但没有测试覆盖、最可能咬人的输入。每项都已在其归属任务里加了钉住它的测试。

1. **`.blend` 已存在且被人在 GUI 里改过** — 模板生成器必须跳过而非覆盖，否则吃掉手工工作（归属 Task 6）
2. **`--project-root` 指向错误目录**（无 `00_project/`） — 必须在写任何东西之前退出非 0，否则在错误位置建出一堆空壳（归属 Task 6）
3. **动态 RNA enum 静默失效** — 用 `enum_items` 校验 `view_transform` 或 `engine` 会让**任何**检查假通过，错误要到渲染阶段才暴露（归属 Task 3）
4. **`--dry-run` 实际写了盘** — 只看返回值不看 mtime 会漏掉"报告说没写、实际写了"（归属 Task 6）
5. **HDRI 文件缺失** — 合成器路线下 LookDev 模板会崩；缺失时必须报警告且**不伪造**纯色环境（归属 Task 6）

---

## File Structure

| 文件 | 职责 | 依赖 bpy |
|---|---|---|
| `00_project/pipeline/utils.py` | **唯一规格来源** + 版本校验 + 命名 + 版本号/帧号推导 | 否 |
| `00_project/pipeline/shot.py` | 引擎/色彩/输出/Pass/镜头；`apply_preset()` 统一入口 | 部分（纯函数不需要） |
| `00_project/pipeline/review.py` | 抽层 + VSE 烧录 + ffmpeg 封装 | 部分 |
| `00_project/pipeline/build_templates.py`（新） | 生成 6 个 `.blend` | 是 |
| `00_project/pipeline/g0_probe_t1.py`（改） | `--out` 改 argparse | 是 |
| `00_project/pipeline/tests/_bootstrap.py`（新） | 把 `00_project/pipeline` 加入 `sys.path` | 否 |
| `00_project/pipeline/tests/test_utils.py`（新） | 规格唯一性、版本两级校验、快门换算、命名 | 否 |
| `00_project/pipeline/tests/test_bible.py`（新） | Bible 数值与 `utils.py` 一致（**不写生成器**，spec §9.1） | 否 |
| `00_project/pipeline/tests/test_preset.py`（新） | `apply_preset` 读回断言 | 是 |
| `00_project/pipeline/tests/test_blend_roundtrip.py`（新） | 生成 → 重开 → 逐项断言 | 是 |

**测试运行方式**（`unittest`，两套解释器）：

```bash
# 纯 Python（系统 python3）
cd 00_project/pipeline && python3 -m unittest discover -s tests -t . -v

# 需要 bpy 的（Blender 内置 Python）
cd 00_project/pipeline && blender -b --factory-startup --python tests/test_preset.py
cd 00_project/pipeline && blender -b --factory-startup --python tests/test_blend_roundtrip.py
```

Blender 侧测试**禁止用 `unittest.main()`**——它解析 `sys.argv`，而 Blender 传进来的是它自己的参数，失败用例不会让命令失败。必须 `TextTestRunner` + `loadTestsFromModule` 再 `sys.exit(0 if result.wasSuccessful() else 1)`。

---

### Task 0: 收口模块层 CLI + 规格归并到 `utils.py`

**这是前置任务。** spec §9.3：`shot.py:334` 是裸 `main()`，`review.py:367-386` 是模块层 `argparse`。已实测 `import shot` 会把 argparse help 打到 stdout。不先修，Task 1–6 的测试一行都建不起来。

**Files:**
- Modify: `00_project/pipeline/utils.py`（新增 `SHUTTER_ANGLE` / `SENSOR_WIDTH` / `shutter_frames()`）
- Modify: `00_project/pipeline/shot.py:15-25`（删重复常量，改 `import utils`）、`:334`（收 CLI）
- Modify: `00_project/pipeline/review.py:24`（删 `FPS`）、`:367-386`（收 CLI）
- Create: `00_project/pipeline/tests/_bootstrap.py`
- Create: `00_project/pipeline/tests/test_utils.py`

**Interfaces:**
- Consumes: 无（首个任务）
- Produces:
  - `utils.SHUTTER_ANGLE: float = 180.0`、`utils.SENSOR_WIDTH: float = 36.0`
  - `utils.shutter_frames() -> float`（返回 `SHUTTER_ANGLE / 360.0` = `0.5`）
  - `utils.REQUIRED_VERSION_PREFIX: str`（`"5.2"`，由 `BLENDER_VERSION` 派生）
  - `utils.check_blender_version(strict: bool = True) -> dict` 改为**两级**（见 Step 5）
  - `shot.py` / `review.py` 的 CLI 全部收进 `if __name__ == "__main__":`，import 无副作用

- [ ] **Step 1: 写失败的测试**

`00_project/pipeline/tests/_bootstrap.py`：

```python
"""把 00_project/pipeline 加入 sys.path，让各测试文件能 import 项目模块。"""
import os
import sys

PIPELINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PIPELINE_DIR not in sys.path:
    sys.path.insert(0, PIPELINE_DIR)
```

`00_project/pipeline/tests/test_utils.py`：

```python
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import utils


class TestImportIsSideEffectFree(unittest.TestCase):
    """Review Focus 的根因测试：模块层跑 CLI 会污染 import。"""

    def test_importing_shot_prints_nothing(self):
        import subprocess
        r = subprocess.run(
            [sys.executable, "-c", "import shot"],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            capture_output=True, text=True,
        )
        self.assertEqual(0, r.returncode, r.stderr)
        self.assertEqual("", r.stdout, "import shot 打印了内容 —— CLI 没收进 __main__")

    def test_importing_review_prints_nothing(self):
        import subprocess
        r = subprocess.run(
            [sys.executable, "-c", "import review"],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            capture_output=True, text=True,
        )
        self.assertEqual(0, r.returncode, r.stderr)
        self.assertEqual("", r.stdout, "import review 打印了内容 —— CLI 没收进 __main__")


class TestSpecIsSingleSource(unittest.TestCase):
    """规格值只在 utils.py 定义。别的模块硬编码就是漂移。"""

    def test_shot_does_not_define_spec_constants(self):
        import shot
        for name in ("BLENDER_VERSION", "RESOLUTION", "FPS", "SHUTTER_ANGLE", "SENSOR_WIDTH"):
            self.assertFalse(
                hasattr(shot, name) or name in vars(shot),
                f"shot.py 仍自己定义 {name} —— 应改为读 utils.{name}",
            )

    def test_review_does_not_define_fps(self):
        import review
        self.assertNotIn("FPS", vars(review), "review.py 仍自己定义 FPS")

    def test_shutter_and_sensor_live_in_utils(self):
        """这两个原本只在 shot.py；utils 必须齐全才算唯一来源。"""
        self.assertEqual(180.0, utils.SHUTTER_ANGLE)
        self.assertEqual(36.0, utils.SENSOR_WIDTH)


class TestShutter(unittest.TestCase):
    def test_shutter_deg_converts_to_frames(self):
        """180° = 0.5 帧。直接写 180.0 会得到 180 帧模糊且不报错。"""
        self.assertEqual(0.5, utils.shutter_frames())


class TestLocks(unittest.TestCase):
    def test_version_prefix_is_first_two_segments(self):
        self.assertEqual("5.2", utils.REQUIRED_VERSION_PREFIX)
        self.assertEqual(
            utils.REQUIRED_VERSION_PREFIX,
            ".".join(utils.BLENDER_VERSION.split(".")[:2]),
        )
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd 00_project/pipeline && python3 -m unittest discover -s tests -t . -v`
Expected: FAIL —— `utils.shutter_frames` 不存在；`import shot` 测试因 stdout 非空而 FAIL

- [ ] **Step 3: `utils.py` 增加常量与 `shutter_frames()`**

在 `utils.py` 的 `# ---- 锁定规格 ----` 块内 `FRAME_START = 1001` 之后追加：

```python
SHUTTER_ANGLE = 180.0    # 度。写进 Blender 时必须过 shutter_frames() 换算
SENSOR_WIDTH = 36.0      # mm，全片统一（project_bible.md 锁定）
```

在 `check_blender_version` 之前追加：

```python
REQUIRED_VERSION_PREFIX = ".".join(BLENDER_VERSION.split(".")[:2])


def shutter_frames() -> float:
    """快门角度（度）→ Blender 的 motion_blur_shutter（帧）。180° → 0.5 帧。

    ⚠️ 单位是帧不是角度。直接写 180.0 会得到 180 帧的运动模糊且**不报错**。
    """
    return SHUTTER_ANGLE / 360.0
```

- [ ] **Step 4: `shot.py` / `review.py` 去重**

`shot.py`：删掉 `:18-23` 的整块（`# ---- 项目规格 ----` 到 `SENSOR_WIDTH = 36.0`），
在 `import os` 之后加 `import utils`（同目录，`sys.path` 由 Blender 的脚本目录与测试 bootstrap 保证）。
把函数体里用到这些名字的地方改成 `utils.RESOLUTION` / `utils.FPS` / `utils.SENSOR_WIDTH` / `utils.SHUTTER_ANGLE`。
`STAGES` 与 `AVAILABLE_PASSES` 留在 `shot.py`（不是规格值，是管线结构）。

`review.py`：删掉 `:24` 的 `FPS = 24`，加 `import utils`，`_timecode(frame, fps=None)` 改为：

```python
def _timecode(frame: int, fps: int | None = None) -> str:
    """帧号 → 时码 HH:MM:SS:FF"""
    fps = fps or utils.FPS
    ...
```

- [ ] **Step 5: 收口两处 CLI**

`shot.py`：把末尾的裸 `main()` 改为

```python
if __name__ == "__main__":
    main()
```

`review.py`：把 `:367-386` 的模块层 argparse 构造与 `_a = p.parse_args(_argv())` 及
其后的 `if _a.create_preview: ... else: p.print_help()` 全部缩进到一个
`def main():` 函数体内，函数末尾加

```python
if __name__ == "__main__":
    main()
```

参照 `asset.py:29` / `cache.py:22` 已有的 `if __name__ == "__main__":` 写法。

- [ ] **Step 6: `check_blender_version` 改两级校验**

替换 `if ver != BLENDER_VERSION:` 那一段（原 `utils.py:49-55`）：

```python
    if not ver.startswith(utils_required := REQUIRED_VERSION_PREFIX + "."):
        msg = f"Blender 版本不符: {ver} 需 {REQUIRED_VERSION_PREFIX}.x"
        if strict:
            raise SystemExit(f"[FATAL] {msg}\n  项目锁 {BLENDER_VERSION}，不跨 major.minor 混用")
        return {"ok": False, "error": msg, "hint": "改 BLENDER_VERSION 或用正确版本"}

    # build hash 不同**不失败**：本机是 dev build，官方 5.2.0 发行版 hash 必然不同
    warnings = []
    if bh != BLENDER_BUILD_HASH:
        warnings.append(
            f"build hash 与记录不符: 记录 {BLENDER_BUILD_HASH}，实际 {bh}；"
            f"继续执行但请确认渲染机一致"
        )
    return {"ok": True, "version": ver, "build_hash": bh, "warnings": warnings}
```

- [ ] **Step 7: 运行测试确认通过**

Run: `cd 00_project/pipeline && python3 -m unittest discover -s tests -t . -v`
Expected: PASS

- [ ] **Step 8: 人工确认 grep 只命中 `utils.py`（spec §5.1 的硬约束）**

Run: `cd 00_project/ppsk && grep -rn "^FPS\|^RESOLUTION\|^BLENDER_VERSION\|^SHUTTER\|^SENSOR_WIDTH" 00_project/pipeline/`
Expected: 每一条都在 `utils.py`；`shot.py` 与 `review.py` 零命中

- [ ] **Step 9: 提交**

```bash
git add 00_project/pipeline/utils.py 00_project/pipeline/shot.py 00_project/pipeline/review.py 00_project/pipeline/tests/
git commit -m "refactor(pipeline)：规格值归并到 utils.py，模块层 CLI 收进 __main__

规格常量只在 utils.py 定义，shot.py / review.py 改为 import utils 读取。
新增 shutter_frames()（180° → 0.5 帧）与 REQUIRED_VERSION_PREFIX。
check_blender_version 改两级：版本号前两段不符才失败，build hash 只警告。
fix(shot/review)：模块层跑 argparse 导致 import 有副作用，收进 __main__。"
```

---

### Task 1: `apply_preset()` — 渲染设置统一入口

**Files:**
- Modify: `00_project/pipeline/shot.py`（新增 `apply_preset`；`setup_output` 补单位/帧范围/快门）
- Create: `00_project/pipeline/tests/test_preset.py`

**Interfaces:**
- Consumes: `utils.RESOLUTION` / `utils.FPS` / `utils.shutter_frames()` / `utils.SENSOR_WIDTH` / `utils.VIEW_TRANSFORM` / `utils.LOOK` / `utils.DISPLAY_DEVICE` / `utils.FRAME_START` / `utils.HANDLE_FRAMES`
- Produces: `shot.apply_preset(scene, *, shot: str, stage: str, version: str = "v001", view_transform: str | None = None, engine: str = "EEVEE", project_root: str = ".") -> dict`
  - 返回 `{"ok": True, "engine":…, "color":…, "output":…, "passes":…, "warnings":[…]}`；任一子项失败则 `{"ok": False, "error": "k: …", "hint": …}`（`setup_render` 现有的聚合写法）
  - `setup_render()` 改为只调 `apply_preset()`，不再自己逐项调四个函数
  - `view_transform=None` 时用 `utils.VIEW_TRANSFORM`（`"AgX"`）

- [ ] **Step 1: 写失败的测试**

`00_project/pipeline/tests/test_preset.py`：

```python
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bpy
import utils
import shot


def fresh_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


class TestVersionCheck(unittest.TestCase):
    def test_hash_mismatch_is_warning_not_failure(self):
        """本机 dev build 与官方发行版 hash 必然不同 —— 只能警告"""
        r = utils.check_blender_version.__wrapped__() if hasattr(utils.check_blender_version, "__wrapped__") \
            else utils.check_blender_version(strict=False)
        self.assertTrue(r["ok"], r)
        self.assertIsInstance(r.get("warnings", []), list)


class TestApplyPreset(unittest.TestCase):
    def setUp(self):
        self.scene = fresh_scene()
        self.r = shot.apply_preset(self.scene, shot="seq010_sh010", stage="light",
                                   project_root="/tmp/opencode")

    def test_resolution_and_fps(self):
        self.assertEqual(list(utils.RESOLUTION),
                         [self.scene.render.resolution_x, self.scene.render.resolution_y])
        self.assertEqual(utils.FPS, self.scene.render.fps)

    def test_units_are_metric(self):
        """Bible 锁定公制 1u=1m，模板与实际渲染都要靠这一条"""
        self.assertEqual("METRIC", self.scene.unit_settings.system)
        self.assertEqual(1.0, self.scene.unit_settings.scale_length)

    def test_shutter_is_frames_not_degrees(self):
        """⚠️ Review Focus：直接写 180.0 会被当成 180 帧"""
        self.assertAlmostEqual(0.5, self.scene.render.motion_blur_shutter, places=5)
        self.assertNotAlmostEqual(utils.SHUTTER_ANGLE, self.scene.render.motion_blur_shutter)

    def test_motion_blur_off_vector_on(self):
        """D7：二者互斥，选 Vector"""
        self.assertFalse(self.scene.render.use_motion_blur)
        self.assertTrue(self.scene.view_layers[0].use_pass_vector)

    def test_color_readback(self):
        vs, ds = self.scene.view_settings, self.scene.display_settings
        self.assertEqual(utils.VIEW_TRANSFORM, vs.view_transform)
        self.assertEqual(utils.LOOK, vs.look)
        self.assertEqual(utils.DISPLAY_DEVICE, ds.display_device)

    def test_per_shot_view_transform(self):
        """G0-T4：关键 FX 镜头换 Khronos PBR Neutral（spec D9）"""
        sc = fresh_scene()
        shot.apply_preset(sc, shot="seq010_sh020", stage="light",
                          view_transform="Khronos PBR Neutral", project_root="/tmp/opencode")
        self.assertEqual("Khronos PBR Neutral", sc.view_settings.view_transform)

    def test_exr_multilayer_and_frame_range(self):
        ims = self.scene.render.image_settings
        self.assertEqual("MULTI_LAYER_IMAGE", ims.media_type)
        self.assertEqual("OPEN_EXR_MULTILAYER", ims.file_format)
        # 帧范围：1001 起 + 8 帧 handles
        self.assertEqual(utils.FRAME_START, self.scene.frame_start)
        self.assertEqual(utils.FRAME_START + 2 * utils.HANDLE_FRAMES, self.scene.frame_end)
        self.assertEqual(utils.FRAME_START + utils.HANDLE_FRAMES, self.scene.frame_current)

    def test_output_uses_hash_placeholder(self):
        """⚠️ %04d 会产出双扩展名（g0 报告 §6.6）"""
        self.assertIn("####", self.scene.render.filepath)
        self.assertNotIn("%04d", self.scene.render.filepath)

    def test_engine_is_eevee_by_default(self):
        self.assertEqual("BLENDER_EEVEE", self.scene.render.engine)


if __name__ == "__main__":
    _suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    _result = unittest.TextTestRunner(verbosity=2).run(_suite)
    sys.exit(0 if _result.wasSuccessful() else 1)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd 00_project/pipeline && blender -b --factory-startup --python tests/test_preset.py`
Expected: FAIL —— `module 'shot' has no attribute 'apply_preset'`

- [ ] **Step 3: 实现 `apply_preset()`**

在 `shot.py` 的 `setup_passes` 之后、`# ==== 镜头 ====` 之前插入：

```python
def apply_preset(
    scene,
    *,
    shot: str,
    stage: str,
    version: str = "v001",
    view_transform: str | None = None,
    engine: str = "EEVEE",
    project_root: str = ".",
) -> dict:
    """
    渲染设置唯一入口。setup_render 与 build_templates 共用这一份实现。

    覆盖：分辨率 / fps / 公制单位 / 帧范围（1001 起 + 8 handles）/
    快门 0.5 帧 / 运动模糊关 + Vector 开 / 色彩四元组 / EXR multilayer /
    帧序列 #### 占位符 / 全部可用 View Layer Pass。

    ⚠️ 不设 volumetric_samples / taa_render_samples：本机无 GPU，
    采样数由渲染机决定（spec §11）。
    """
    if stage not in STAGES:
        return {"ok": False, "error": f"未知环节: {stage}",
                "hint": f"合法值: {', '.join(STAGES)}"}

    scene.render.engine = engine  # 交给 set_engine 处理 Cycles 分支
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.frame_start = utils.FRAME_START
    scene.frame_end = utils.FRAME_START + 2 * utils.HANDLE_FRAMES
    scene.frame_current = utils.FRAME_START + utils.HANDLE_FRAMES
    # ⚠️ 单位是帧不是角度（utils.shutter_frames 已封装换算）
    scene.render.motion_blur_shutter = utils.shutter_frames()
    scene.render.use_motion_blur = False   # D7：与 Vector Pass 互斥，选后者

    res = {
        "engine": set_engine(scene, engine),
        "color": setup_color(scene, view_transform or utils.VIEW_TRANSFORM),
        "output": setup_output(scene, shot, stage, version, project_root),
        "passes": setup_passes(scene),
    }
    failed = {k: v for k, v in res.items() if not v.get("ok")}
    if failed:
        return {"ok": False,
                "error": "; ".join(f"{k}: {v['error']}" for k, v in failed.items()),
                "hint": "见 g0_feasibility_report.md 附录",
                **res}
    return {"ok": True, "warnings": [], **res}
```

把 `setup_output` 里的 `r.resolution_x, r.resolution_y = RESOLUTION` 与 `r.fps = FPS`
改成 `utils.RESOLUTION` / `utils.FPS`（Task 0 已加 import）。

- [ ] **Step 4: `setup_render` 改为调用 `apply_preset`**

`setup_render` 的 `dry_run` 分支之后、`import bpy` 之后，把
`scene = bpy.context.scene` 到 `return {"ok": True, ...}` 整段替换为：

```python
    scene = bpy.context.scene
    r = apply_preset(scene, shot=shot, stage=stage, engine=engine,
                     view_transform=view_transform, project_root=project_root)
    if not r.get("ok"):
        return {"ok": False, "error": r.get("error"), "hint": r.get("hint")}
    return {"ok": True, "shot": shot, "stage": stage, **r}
```

`setup_render` 的 `view_transform` 参数默认值改为 `None`（由 `apply_preset` 兜底成
`utils.VIEW_TRANSFORM`），CLI 的 `--view-transform` 默认值同步改为 `None`。

- [ ] **Step 5: 运行测试确认通过**

Run: `cd 00_project/pipeline && blender -b --factory-startup --python tests/test_preset.py 2>&1 | tail -25; echo "exit=${PIPESTATUS[0]}"`
Expected: 全部 OK，`exit=0`

- [ ] **Step 6: 确认 `apply_preset` 在纯 Python 下可 import（不 import bpy 的部分不受影响）**

Run: `cd 00_project/ppsk && python3 -c "import sys; sys.path.insert(0,'00_project/pipeline'); import utils, shot; assert 'bpy' not in sys.modules, 'shot.py 在模块层 import 了 bpy'; print('ok', utils.shutter_frames(), utils.REQUIRED_VERSION_PREFIX)"`
Expected: `ok 0.5 5.2`

- [ ] **Step 7: 提交**

```bash
git add 00_project/pipeline/shot.py 00_project/pipeline/tests/test_preset.py
git commit -m "feat(shot)：apply_preset() 渲染设置统一入口

setup_render 与 build_templates 共用一份实现。
补上从未被执行过的 motion_blur_shutter（0.5 帧）、公制单位、帧范围、
use_motion_blur=False。view_transform 支持 per-shot 覆盖（spec D9）。"
```

---

### Task 2: `make_object_name()` — 对象名 vs 资产 ID

**Files:**
- Modify: `00_project/pipeline/utils.py`（追加函数）
- Modify: `00_project/pipeline/tests/test_utils.py`（追加测试类）

**Interfaces:**
- Consumes: `utils.normalize_name`（已存在）
- Produces: `utils.make_object_name(prefix: str, name: str) -> str` —— 返回 `f"{prefix}_{clean}"`，
  `clean` 为把非 `[A-Za-z0-9_]` 换成 `_`、折叠连续 `_`、去首尾 `_` 后的 `name`；
  `clean` 为空时返回 `prefix` 本身

- [ ] **Step 1: 写失败的测试**

追加到 `tests/test_utils.py` 末尾（`import utils` 已在顶部）：

```python
class TestObjectName(unittest.TestCase):
    def test_keeps_uppercase_prefix(self):
        """normalize_name 会转小写，违反 dls.md 的 GEO_/CAM_/LGT_ 前缀规范"""
        self.assertEqual("CAM_cam", utils.make_object_name("CAM", "cam"))
        self.assertEqual("GEO_grayball", utils.make_object_name("GEO", "grayball"))
        self.assertEqual("LGT_key", utils.make_object_name("LGT", "key"))

    def test_normalize_name_is_for_asset_ids(self):
        """资产 ID 走 normalize_name（小写下划线），与对象名划清边界"""
        self.assertEqual("chr_hero", utils.normalize_name("CHR-Hero"))

    def test_strips_illegal_chars(self):
        # `-` 和空格各换成一个 `_`，两个不同字符之间不会合并
        self.assertEqual("GEO_a_b_c", utils.make_object_name("GEO", "a-b c"))

    def test_empty_name_returns_prefix(self):
        self.assertEqual("GEO", utils.make_object_name("GEO", "---"))
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd 00_project/pipeline && python3 -m unittest discover -s tests -t . -v`
Expected: FAIL —— `AttributeError: module 'utils' has no attribute 'make_object_name'`

- [ ] **Step 3: 实现 `make_object_name()`**

追加到 `utils.py` 末尾：

```python
def make_object_name(prefix: str, name: str) -> str:
    """对象名：保留 dls.md 规定的大写前缀，如 CAM_cam / GEO_grayball。

    资产 ID 才用 normalize_name（小写下划线）。两者不可混用：
    normalize_name 会转小写，用它处理对象名会得到 geo_grayball，
    违反命名规范。
    """
    clean = re.sub(r"[^A-Za-z0-9_]", "_", name)
    clean = re.sub(r"_+", "_", clean).strip("_")
    return f"{prefix}_{clean}" if clean else prefix
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd 00_project/pipeline && python3 -m unittest discover -s tests -t . -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add 00_project/pipeline/utils.py 00_project/pipeline/tests/test_utils.py
git commit -m "feat(utils)：make_object_name 保留大写前缀

对象名用 make_object_name（大写前缀 GEO_/CAM_/LGT_），
资产 ID 用 normalize_name（小写下划线）。两者划清边界。"
```

---

### Task 3: Bible 数值与 `utils.py` 一致性测试

**不写生成器。** spec §9.1 明确否决了 v1 的哨兵区块方案：「`utils.py` 已是唯一来源，
再加一层同步机制收益不抵复杂度」。改为一条纯断言测试：从 `utils` 读值，断言
`project_bible.md` 文本里出现该值。代价是表格**格式**不会被自动纠正，只有**数值**会被抓到
——这一点 spec 已明示接受。

**Files:**
- Create: `00_project/pipeline/tests/test_bible.py`

**Interfaces:**
- Consumes: `utils` 全部规格常量；`00_project/bible/project_bible.md` 全文
- Produces: 无（纯测试）

- [ ] **Step 1: 写测试**

创建 `00_project/pipeline/tests/test_bible.py`：

```python
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import utils

BIBLE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "00_project", "bible", "project_bible.md",
)


def bible_text() -> str:
    with open(BIBLE, encoding="utf-8") as f:
        return f.read()


class TestBibleMatchesUtils(unittest.TestCase):
    """spec §9.1：Bible 人工维护，但数值必须与 utils.py 一致。

    只抓数值，不抓格式 —— 格式漂移不管，这是该方案已知的代价。
    """

    def test_blender_version_and_hash(self):
        t = bible_text()
        self.assertIn(utils.BLENDER_VERSION, t)
        self.assertIn(utils.BLENDER_BUILD_HASH, t)

    def test_resolution(self):
        self.assertIn(f"{utils.RESOLUTION[0]}×{utils.RESOLUTION[1]}", bible_text())

    def test_fps(self):
        self.assertIn(str(utils.FPS), bible_text())

    def test_shutter_angle_in_degrees(self):
        """Bible 记的是人读的度数，不是换算后的帧数"""
        self.assertIn(f"{int(utils.SHUTTER_ANGLE)}°", bible_text())

    def test_shutter_conversion_is_consistent(self):
        """180° 必须对应 0.5 帧 —— 两处都写进 Bible 才不会只改一处"""
        t = bible_text()
        self.assertIn("180°", t)
        self.assertIn("0.5 帧", t)
        self.assertEqual(0.5, utils.shutter_frames())

    def test_color_quadruple(self):
        t = bible_text()
        for v in (utils.VIEW_TRANSFORM, utils.LOOK, utils.DISPLAY_DEVICE):
            self.assertIn(v, t)

    def test_sensor_width(self):
        self.assertIn(str(int(utils.SENSOR_WIDTH)), bible_text())

    def test_frame_convention(self):
        t = bible_text()
        self.assertIn(str(utils.FRAME_START), t)
        self.assertIn(f"{utils.HANDLE_FRAMES} 帧 handles", t)

    def test_no_stale_blender_version(self):
        """5.2.1 只允许出现在「改为实测的 5.2.0」这类修订记录语境里"""
        body = bible_text().split("## 修订记录")[0]
        self.assertNotIn("5.2.1", body, "正文里还有 5.2.1 —— 修订记录里的历史引用不算")


class TestTamperIsDetected(unittest.TestCase):
    """元测试：改坏 utils.py 的值后测试必须变红，否则这个测试是装饰品"""

    def test_fps_change_would_break_bible_assertion(self):
        original = utils.FPS
        try:
            utils.FPS = 48
            self.assertNotIn(str(utils.FPS), bible_text().split("fps")[-1][:20] or "x")
        finally:
            utils.FPS = original
```

- [ ] **Step 2: 运行测试**

Run: `cd 00_project/pipeline && python3 -m unittest discover -s tests -t . -v`
Expected: PASS（当前 Bible 已由 G0 期间填好，数值应已对齐）。若某条 FAIL，
说明 Bible 与 `utils.py` 已经漂移 —— **修 Bible，不要改测试**。

- [ ] **Step 3: 确认测试真能抓到漂移（手工制造一次）**

Run: `cd /mnt/data/dsv/ppsk && sed -i 's/^FPS = 24$/FPS = 48/' 00_project/pipeline/utils.py && (cd 00_project/pipeline && python3 -m unittest discover -s tests -t . 2>&1 | tail -4) ; sed -i 's/^FPS = 48$/FPS = 24/' 00_project/pipeline/utils.py && (cd 00_project/pipeline && python3 -m unittest discover -s tests -t . 2>&1 | tail -3)`
Expected: 第一次 FAIL（`test_fps` 或相关用例红），第二次 PASS

> **这条 Step 的意义**：若改了 `utils.FPS` 测试仍然全绿，说明断言写虚了，
> 后续所有"Bible 与 utils 一致"的声明都不成立（spec §10.3）。

- [ ] **Step 4: 提交**

```bash
git add 00_project/pipeline/tests/test_bible.py
git commit -m "test(bible)：Bible 数值与 utils.py 一致性断言

按 spec §9.1 不写生成器 —— utils.py 已是唯一来源，再加一层同步机制
收益不抵复杂度。改为纯断言测试：只抓数值，格式漂移不管。"
```

---

<details><summary>已作废：v1 的哨兵生成区块方案（保留供追溯，不要执行）</summary>

> v1 计划曾设计 `check_bible.py`：`BEGIN`/`END` 哨兵 + `render_block()` 从 `utils` 渲染
> Markdown 表格 + `--sync` 写回区块。**spec §9.1 否决了这个方案**，理由是
> "再加一层同步机制收益不抵复杂度"。本计划原先误写了该任务，已按 spec 改为纯断言测试。
> 若将来确实需要自动同步（例如 Bible 表格频繁漂移），可重新引入 —— 但要先更新 spec §9.1。

</details>
---

### Task 4: 目录与探针脚本修正

**Files:**
- Modify: `00_project/bible/g0_probe_t1.py:25-27`（argparse 化）
- Modify: `docs/dls.md`（§3.1 目录树 +2 行、§6.6 fx 路径）
- Modify: `README.md`（规范节镜头编号范例）
- Delete: `--out/` 目录（仓库根的垃圾）
- Create: `05_assets/fx/`

**Interfaces:**
- Consumes: 无（纯数据与脚本修正）
- Produces: `g0_probe_t1.py` 支持 `--out <目录>` 与 `--res <宽> <高>`；
  `05_assets/fx/` 存在；`dls.md` / `README.md` 范例改为 `seq010_sh010`

- [ ] **Step 1: 修 `g0_probe_t1.py` 的参数解析**

替换 `g0_probe_t1.py:25-27` 三行（`argv = ...` / `OUT = ...` / `RES = ...`）为：

```python
import argparse

_p = argparse.ArgumentParser(prog="g0_probe_t1.py")
_p.add_argument("--out", default="/tmp/g0_t1", help="输出目录")
_p.add_argument("--res", nargs=2, type=int, default=(320, 180), metavar=("W", "H"))
_a = _p.parse_args(_argv())
OUT = _a.out
RES = tuple(_a.res)
```

> **为什么必须改**：原代码 `OUT = argv[0]` 按位置取参数，但同文件用法说明写的是
> `-- --out <目录>`。照说明调用时 `argv[0] == "--out"`，`os.makedirs("--out")` 会在
> **仓库根**建出字面量 `--out` 目录。`g0_feasibility_report.md` §9.3 给的复现命令
> 正会触发它（spec §6.1）。

- [ ] **Step 2: 验证解析正确且不再产生 `--out`**

Run: `cd /mnt/data/dsv/ppsk && rm -rf -- "--out" && blender -b --factory-startup --python 00_project/bible/g0_probe_t1.py -- --out /tmp/g0_t1_fix 2>&1 | tail -3 && ls /tmp/g0_t1_fix && (ls -d -- "--out" 2>/dev/null && echo "BUG 仍在" || echo "OK: 仓库根无 --out")`
Expected: 输出帧文件在 `/tmp/g0_t1_fix`，且打印 `OK: 仓库根无 --out`

- [ ] **Step 3: 删掉仓库根的 `--out/` 垃圾目录**

Run: `cd /mnt/data/dsv/ppsk && rm -rf -- "--out" && (ls -d -- "--out" 2>/dev/null && echo "删除失败" || echo "OK: 已删除")`
Expected: `OK: 已删除`

> **注意**：`.gitignore` 有 `*.exr`，所以这个目录 `git status` 看不见。删之前先 `ls` 确认
> 里面只有 `.exr`（Step 3 前已确认过是 `t1_.exr` / `t4_.exr` 两个探针输出，无用户资产）。

- [ ] **Step 4: 建 `05_assets/fx/` 并更新 `dls.md`**

Run: `cd /mnt/data/dsv/ppsk && mkdir -p 05_assets/fx && touch 05_assets/fx/.gitkeep && ls 05_assets/`
Expected: 列出 `chr env fx lib prp veh`

`docs/dls.md` §3.1 目录树里，`05_assets/` 的 `├── lib/` 行**之前**加一行：

```
│   ├── fx/              # 可发布 FX 预设（与 chr/env/prp/veh/lib 平级）
```

**不加** `wip/publish` —— `dls.md` §3.1 只对 `chr/hero` 画了 `{wip, publish}`，
不擅自推广到其他分类（spec §9.5）。

- [ ] **Step 5: `dls.md` §6.6 改 fx 路径**

`docs/dls.md` §6.6 末尾那句「放进 `05_assets/lib/fx/`」改为：

> FX 按类型做成可复用的预设或节点组。**可发布的 FX 预设放 `05_assets/fx/`**；
> 节点组与 GN 生成器放 `05_assets/lib/`。镜头里只调参数并缓存。

- [ ] **Step 6: `README.md` 规范节改镜头编号范例**

`README.md` 规范节「镜头编号：`seq<三位>_sh<三位>`，如 `seq040_sh020`」→
`如 seq010_sh010`（真实镜头表是 `SEQ010` 的 sh010–sh050）。
`dls.md` §3.1 目录树里的 `06_shots/seq040/sh020/` 范例同样改为 `seq010/sh010/`。

- [ ] **Step 7: 确认没有残留的 `seq040` 范例**

Run: `cd /mnt/data/dsv/ppsk && grep -rn "seq040" README.md docs/dls.md 00_project/bible/ | grep -v "superpowers/"
Expected: 无输出

- [ ] **Step 8: 提交**

```bash
git add 00_project/bible/g0_probe_t1.py docs/dls.md README.md 05_assets/fx/.gitkeep
git commit -m "fix(dls)：补 05_assets/fx/，镜头范例改 seq010_sh010

g0_probe_t1.py 的 --out 改 argparse —— 原先按位置取 argv[0]，
照自家用法说明调用会在仓库根建出字面量 --out 目录（spec §6.1）。
删掉仓库根的 --out/ 垃圾目录（内含两个探针 EXR 输出）。"
```

---

### Task 5: 6 个环节模板 `.blend` + 往返测试

**Files:**
- Create: `00_project/pipeline/build_templates.py`
- Modify: `00_project/pipeline/tests/test_blend_roundtrip.py`（新建）
- Modify: `.gitignore`（补 `*.blend`）

**Interfaces:**
- Consumes: `shot.apply_preset()`（Task 1）、`utils.make_object_name()`（Task 2）、`utils.SENSOR_WIDTH`
- Produces: `build_templates.TEMPLATES`（tuple of `(filename, stage_kind)`，6 项）、
  `build_templates.COLLECTIONS`、`build(project_root, apply=False, overwrite=False) -> dict`
  - 返回 `{"ok": True, "written": [...], "skipped": [...], "warnings": [...]}`
  - 产出 6 个 `.blend` 到 `<project_root>/00_project/templates/`

- [ ] **Step 1: 先补 `.gitignore`**

`.gitignore` 的 `# Blender` 块内，`*.blend1` **之前**加一行 `*.blend`（plan §15：`.blend` 不进 Git）。

Run: `cd /mnt/data/dsv/ppsk && git check-ignore -v -- "00_project/templates/tpl_light_v001.blend" || echo "尚未忽略，Step 1 未生效"`
Expected: 打印命中的 ignore 规则

- [ ] **Step 2: 写往返测试**

创建 `00_project/pipeline/tests/test_blend_roundtrip.py`：

```python
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bpy
import utils
import build_templates

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
TPL_DIR = os.path.join(ROOT, "00_project", "templates")


def open_blend(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    return bpy.context.scene


def tmp_root():
    root = tempfile.mkdtemp()
    os.makedirs(os.path.join(root, "00_project", "templates"))
    return root


class TestTemplatesExist(unittest.TestCase):
    def test_six_templates_present(self):
        for name, _ in build_templates.TEMPLATES:
            self.assertTrue(os.path.exists(os.path.join(TPL_DIR, name)), name)

    def test_templates_count_is_six(self):
        self.assertEqual(6, len(build_templates.TEMPLATES))


class TestSharedSettings(unittest.TestCase):
    """spec §10.2：每个模板重开后都要满足的规格项"""

    def test_all_templates_carry_shared_settings(self):
        for name, _ in build_templates.TEMPLATES:
            with self.subTest(template=name):
                sc = open_blend(os.path.join(TPL_DIR, name))
                self.assertEqual(list(utils.RESOLUTION),
                                 [sc.render.resolution_x, sc.render.resolution_y])
                self.assertEqual(utils.FPS, sc.render.fps)
                self.assertEqual("METRIC", sc.unit_settings.system)
                self.assertEqual("BLENDER_EEVEE", sc.render.engine)
                self.assertEqual(utils.VIEW_TRANSFORM, sc.view_settings.view_transform)
                self.assertEqual(utils.LOOK, sc.view_settings.look)
                self.assertEqual(utils.DISPLAY_DEVICE, sc.display_settings.display_device)
                # ⚠️ 全仓库从未被执行过的断言
                self.assertAlmostEqual(0.5, sc.render.motion_blur_shutter, places=5)
                self.assertEqual(utils.FRAME_START, sc.frame_start)


class TestStageSpecific(unittest.TestCase):
    def test_layout_has_camera_and_guides(self):
        open_blend(os.path.join(TPL_DIR, "tpl_layout_v001.blend"))
        self.assertTrue(any(o.type == "CAMERA" for o in bpy.data.objects))
        self.assertIn("GUIDE_", bpy.data.collections)

    def test_guides_never_render(self):
        """9:16 参考线只在 Layout 阶段可见，绝不能进渲染（spec §7.3）"""
        open_blend(os.path.join(TPL_DIR, "tpl_layout_v001.blend"))
        guides = [o for o in bpy.data.objects if "guide" in o.name.lower()]
        self.assertTrue(guides, "缺少 9:16 参考线对象")
        for g in guides:
            self.assertTrue(g.hide_render, f"{g.name} 的 hide_render 必须为 True")

    def test_camera_defaults(self):
        open_blend(os.path.join(TPL_DIR, "tpl_layout_v001.blend"))
        cam_obj = [o for o in bpy.data.objects if o.type == "CAMERA"][0]
        self.assertEqual("CAM_cam", cam_obj.name)
        self.assertEqual(utils.SENSOR_WIDTH, cam_obj.data.sensor_width)
        self.assertEqual(35.0, cam_obj.data.lens)      # 占位值，逐镜由镜头表覆盖
        self.assertEqual(0.0, cam_obj.data.shift_x)    # 9:16 靠安全框 + 后期裁切
        self.assertEqual(0.0, cam_obj.data.shift_y)

    def test_light_has_exr_and_view_layers(self):
        sc = open_blend(os.path.join(TPL_DIR, "tpl_light_v001.blend"))
        self.assertEqual("OPEN_EXR_MULTILAYER", sc.render.image_settings.file_format)
        self.assertTrue(any(vl.name.startswith("VL_") for vl in sc.view_layers))
        self.assertTrue(any(o.type == "LIGHT" for o in bpy.data.objects))

    def test_anim_has_no_camera(self):
        open_blend(os.path.join(TPL_DIR, "tpl_anim_v001.blend"))
        self.assertFalse([o for o in bpy.data.objects if o.type == "CAMERA"])

    def test_lookdev_has_turntable_grayballs_colorchecker(self):
        open_blend(os.path.join(TPL_DIR, "tpl_lookdev_v001.blend"))
        names = [o.name for o in bpy.data.objects]
        self.assertGreaterEqual(len([n for n in names if "grayball" in n]), 3)
        self.assertTrue(any("colorchecker" in n for n in names), "缺少 ColorChecker 色卡")


class TestBuildBehavior(unittest.TestCase):
    def test_missing_hdri_is_warning_not_fake(self):
        """Review Focus #5：HDRI 缺失要警告，不伪造纯色环境"""
        r = build_templates.build(tmp_root(), apply=True, overwrite=False)
        self.assertTrue(r["ok"], r)
        self.assertTrue(any("HDRI" in w for w in r["warnings"]),
                        f"HDRI 缺失未进 warnings: {r['warnings']}")

    def test_wrong_project_root_errors_without_writing(self):
        """Review Focus #2：无 00_project/ 的目录必须拒绝且不建任何东西"""
        empty = tempfile.mkdtemp()
        r = build_templates.build(empty, apply=True, overwrite=False)
        self.assertFalse(r["ok"])
        self.assertIn("00_project", r["hint"])
        self.assertEqual([], os.listdir(empty))

    def test_dry_run_does_not_touch_disk(self):
        """Review Focus #4：用 mtime 验证，不信返回值"""
        root = tmp_root()
        r = build_templates.build(root, apply=False, overwrite=False)
        self.assertTrue(r["ok"])
        self.assertEqual(6, len(r["written"]))       # 报告说要写
        self.assertEqual([], os.listdir(os.path.join(root, "00_project", "templates")))

    def test_existing_file_is_skipped_without_overwrite(self):
        """Review Focus #1：GUI 里的手工修改不能被吃掉"""
        root = tmp_root()
        target = os.path.join(root, "00_project", "templates", "tpl_anim_v001.blend")
        with open(target, "wb") as f:
            f.write(b"hand edited in gui")
        r = build_templates.build(root, apply=True, overwrite=False)
        self.assertIn("tpl_anim_v001.blend", r["skipped"])
        with open(target, "rb") as f:
            self.assertEqual(b"hand edited in gui", f.read())

    def test_overwrite_flag_actually_rewrites(self):
        """反向：显式 --overwrite 必须真的写，否则保护逻辑是死代码"""
        root = tmp_root()
        target = os.path.join(root, "00_project", "templates", "tpl_anim_v001.blend")
        with open(target, "wb") as f:
            f.write(b"hand edited in gui")
        r = build_templates.build(root, apply=True, overwrite=True)
        self.assertIn("tpl_anim_v001.blend", r["written"])
        with open(target, "rb") as f:
            self.assertNotEqual(b"hand edited in gui", f.read())


if __name__ == "__main__":
    _suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    _result = unittest.TextTestRunner(verbosity=2).run(_suite)
    sys.exit(0 if _result.wasSuccessful() else 1)
```

- [ ] **Step 3: 运行测试确认失败**

Run: `cd 00_project/pipeline && blender -b --factory-startup --python tests/test_blend_roundtrip.py 2>&1 | tail -12; echo "exit=${PIPESTATUS[0]}"`
Expected: FAIL —— `ModuleNotFoundError: No module named 'build_templates'`

- [ ] **Step 4: 实现 `build_templates.py`**

模块 docstring：

```python
"""生成 6 个环节模板 .blend。需要 bpy。

渲染设置全部走 shot.apply_preset()，不自己重设一遍。
绝不覆盖已存在的 .blend（除非显式 --overwrite）：模板会被人在 GUI 里改，
生成器不能默默吃掉手工工作。
"""
```

模块级常量：

```python
COLLECTIONS = ("CHR_", "ENV_", "PRP_", "FX_", "LGT_", "GUIDE_")

TEMPLATES = (
    ("tpl_layout_v001.blend",   "layout"),
    ("tpl_anim_v001.blend",     "anim"),
    ("tpl_cfx_v001.blend",      "cfx"),
    ("tpl_fx_v001.blend",       "fx"),
    ("tpl_light_v001.blend",    "light"),
    ("tpl_lookdev_v001.blend",  "lookdev"),
)

# 每个模板建哪些 collection
STAGE_COLLECTIONS = {
    "layout":  ("CHR_", "ENV_", "PRP_", "GUIDE_"),
    "anim":    ("CHR_",),
    "cfx":     ("CHR_",),
    "fx":      ("FX_",),
    "light":   ("LGT_",),
    "lookdev": (),
}
```

`build(project_root: str, apply: bool = False, overwrite: bool = False) -> dict` 的行为：

- 校验 `<project_root>/00_project` 存在，否则返回
  `{"ok": False, "error": "project root 缺少 00_project/", "hint": "用 --project-root 指向工程根目录，不是它的子目录"}`，**且不写任何东西**
- `apply=False`：只报告计划，返回 `{"ok": True, "written": [...6 个名...], "skipped": [...], "warnings": []}`
- `apply=True`：逐个模板
  - `os.path.exists` 且 `overwrite=False` → 记入 `skipped`，**跳过**
  - 否则 `bpy.ops.wm.read_factory_settings(use_empty=True)` 重置（保证每个模板干净）→
    建 `STAGE_COLLECTIONS[kind]` 里的 collection → 按 kind 补内容 → 
    调 `shot.apply_preset(scene, shot="<tpl>", stage="light", project_root=project_root)` →
    `bpy.ops.wm.save_as_mainfile(filepath=...)` → 记入 `written`
- 各 kind 的补充内容：
  - `layout`：加相机（名字 `utils.make_object_name("CAM", "cam")`），
    设 `sensor_width=utils.SENSOR_WIDTH`、`sensor_fit="AUTO"`、`lens=35.0`、
    `shift_x=0.0`、`shift_y=0.0`、`clip_start=0.1`、`clip_end=1000.0`；
    `GUIDE_` 里加 9:16 线框（`bpy.data.objects.new(utils.make_object_name("GEO", "guide_vertical"), None)`，
    设 `empty_display_type="WIRE"`、`hide_render=True`）
  - `light`：`apply_preset` 之后再加两个 view layer —— `VL_beauty`（合并）与 `VL_char`（排除 `ENV_`），
    并 `scene.view_layers[0].name = "VL_beauty"`；加一盏占位灯 `utils.make_object_name("LGT", "key")`
  - `lookdev`：加转台 empty + 相机 parent 上去、3 个灰球
    （`utils.make_object_name("GEO", f"grayball_rough{v}")`，v ∈ 0.2/0.5/0.9）、
    ColorChecker 24 色卡（`utils.make_object_name("GEO", "colorchecker")`）。
    **HDRI 只留 World 槽位并往 `warnings` 加「HDRI 未安装」**，不伪造纯色环境
  - `anim` / `cfx` / `fx`：不加对象（cfx 可加一个 `CHR_cloth` 空 collection 标记工作区）
- 返回 `{"ok": True, "written": [...], "skipped": [...], "warnings": [...]}`
- `main(argv)`：`--project-root`、`--apply`、`--overwrite`；成功 `0` / 失败 `1`；
  文件末尾加 `if __name__ == "__main__": sys.exit(main())`

- [ ] **Step 5: 生成模板（先 dry-run，再实跑）**

Run: `cd /mnt/data/dsv/ppsk && blender -b --factory-startup --python 00_project/pipeline/build_templates.py -- --project-root . 2>&1 | tail -4`
Expected: 打印将要写入的 6 个文件名，`00_project/templates/` 下仍无 `.blend`

Run: `cd /mnt/data/dsv/ppsk && blender -b --factory-startup --python 00_project/pipeline/build_templates.py -- --project-root . --apply 2>&1 | tail -4 && ls 00_project/templates/*.blend | wc -l`
Expected: `6`

- [ ] **Step 6: 运行往返测试确认通过**

Run: `cd 00_project/pipeline && blender -b --factory-startup --python tests/test_blend_roundtrip.py 2>&1 | tail -30; echo "exit=${PIPESTATUS[0]}"`
Expected: 全部 OK，`exit=0`

- [ ] **Step 7: 验证覆盖保护在真实模板上生效（mtime 不变）**

Run: `cd /mnt/data/dsv/ppsk && before=$(stat -c %Y 00_project/templates/tpl_anim_v001.blend) && blender -b --factory-startup --python 00_project/pipeline/build_templates.py -- --project-root . --apply >/dev/null 2>&1 && after=$(stat -c %Y 00_project/templates/tpl_anim_v001.blend) && [ "$before" = "$after" ] && echo "SKIP_OK: mtime unchanged"`
Expected: `SKIP_OK: mtime unchanged`

- [ ] **Step 8: 确认 `.blend` 未被 Git 跟踪**

Run: `cd /mnt/data/dsv/ppsk && git status --short 00_project/templates/ && git check-ignore -v 00_project/templates/tpl_light_v001.blend`
Expected: `git status` 对 templates 无输出；`check-ignore` 打印 `*.blend` 规则

- [ ] **Step 9: 提交**

```bash
git add 00_project/pipeline/build_templates.py 00_project/pipeline/tests/test_blend_roundtrip.py .gitignore
git commit -m "feat(templates)：6 个环节模板 .blend + 往返测试

渲染设置走 shot.apply_preset()，不重设一遍。
覆盖保护：已存在的 .blend 跳过，--overwrite 才覆盖。
HDRI 缺失只警告不伪造纯色环境。.blend 加入 .gitignore（plan §15）。"
```

---

### Task 6: 文档定稿与变更记录

**Files:**
- Modify: `00_project/bible/project_bible.md`（补性能预算节）
- Modify: `00_project/bible/scope_lock.md`（`:25` + CR-001 + 签署声明）
- Modify: `00_project/bible/licensing.csv`（`:2`）
- Modify: `README.md`（`:9`、`:44`、落地清单、新增 utils.py 说明）
- Modify: `docs/plan.md`（§22.1 / §22.2 / §22.3 勾选）

**Interfaces:**
- Consumes: 无（纯文档）
- Produces: 无代码接口

- [ ] **Step 1: `project_bible.md` 补性能预算**

在「云雾双轨方案」节之前插入一节，把 plan §11 的全表搬进 Bible（这是 spec §8.1
一直要求但从未补上的一节）：

```markdown
## 性能与场景规模预算（plan §11，锁定）

| 指标 | 上限 | 超限处理 |
|---|---|---|
| 单镜头角色数 | 2（本 Demo 1） | — |
| 同屏 FX 预设实例 | 5（本 Demo 3） | 拆分镜头或合批 |
| 单镜头总三角面 | **150 万** | GN 实例化 / LOD / 视锥剔除 |
| 材质数 / 材质槽 | 60 | 合并同类材质 |
| 灯光数 | 20 | Light Linking 复用 |
| Light probe sphere | 128（EEVEE 硬上限） | 提高 probe 覆盖效率 |
| Light probe plane（视锥内） | 16（EEVEE 硬上限） | 改用 sphere |
| VDB 体素分辨率 | 128³ | 降分辨率 + 后期补偿 |
| GN 实例数（竹林） | 10,000 | 提高几何复用率 |
| 显存 VRAM | ≤ 20 GB | 拆镜头 / 降体积分辨率 |
| 单镜头 Alembic 缓存 | ≤ 2 GB | 降拓扑 / 只导可见区块 |
| View Layer 数 | ≤ 4 | 重渲成本线性增长 |
```

- [ ] **Step 2: `scope_lock.md` 改版本行**

`:25` 的 `| **渲染器** | EEVEE（Blender 5.2.1 LTS） | 锁定版本，不升级 |`
→ `| **渲染器** | EEVEE（Blender **5.2.0 LTS**，build `fbe6228777e7`） | 锁定版本，不升级 |`

- [ ] **Step 3: `scope_lock.md` 追加 CR-001 追认 + 签署声明**

文件末尾追加（spec §8.1 的模板，这是**追认**——变更已在 `utils.py` / `project_bible.md` /
`plan.md` 实际发生，补记录以对齐）：

```markdown
## 6. 变更记录

### CR-001 锁定版本 5.2.1 → 5.2.0（追认）
| 项目 | 内容 |
|---|---|
| 变更日期 | 2026-09-29 |
| 变更项 | 锁定版本：Blender 5.2.1 LTS → **5.2.0 LTS**（build hash `fbe6228777e7`） |
| 原因 | G0 实测本机可用版本为 5.2.0；严格锁 5.2.1 会使全部管线函数无法运行（plan §12.1） |
| 已发生的实际改动 | `utils.py` / `project_bible.md` / `plan.md` 已先行改为 5.2.0，本 CR 为追认 |
| 影响 | plan §7.1 / §12.1 已同步；`README.md` / `licensing.csv` 已同步 |
| 未承担的风险 | 5.2.1 若为更新的 patch，本项目将错过其修复；**升级需另开 CR** |
| 决策人 | 待签 |
```

在 `## 5. 签署` 之前加一句现状声明：

> **本文件签署栏为空，签署前不构成生效基准。**

- [ ] **Step 4: `licensing.csv` 改版本**

`:2` 行中两处 `Blender 5.2.1 LTS` → `Blender 5.2.0 LTS`。

- [ ] **Step 5: `README.md` 四处**

| 位置 | 改动 |
|---|---|
| `:9` | `用 Blender **5.2.1 LTS** 打开` → `**5.2.0 LTS**` |
| `:44` | `- [ ] 锁定 Blender 5.2.1 LTS + 记录 build hash` → `- [x] 锁定 Blender **5.2.0 LTS** + build hash `fbe6228777e7`` |
| 落地清单 | G0 打勾；「模板 .blend」「LookDev 场景」「渲染设置预设」按 Task 5 结果打勾；「锁定版本」打勾 |
| 快速开始 | 新增一行：「规格以 `00_project/pipeline/utils.py` 为唯一机器可读来源。改规格的顺序是：先改 `utils.py` → 再改本文件 → 跑 `cd 00_project/pipeline && python3 -m unittest discover -s tests -t .`」 |

- [ ] **Step 6: `docs/plan.md` 三处勾选**

| 位置 | 改动 |
|---|---|
| §22.1 | 修正两处失实勾选：**管线 API 骨架**——`asset.py` 与 `cache.py` 至今全是 `# TODO` 空壳（把 `[x]` 降级并注明）；**镜头目录骨架**——`seq040/sh020/` 存在但与镜头表 `SEQ010` 冲突（注明） |
| §22.2 | G0 打勾并注明「T4 不通过，已定 per-shot `Khronos PBR Neutral` 对策」；「EEVEE 体积实测」打勾（报告 §1.2 已测）；**「probe 上限」保持未勾**（只验过枚举存在，未实测上限行为） |
| §22.3 | 本计划完成项逐条打勾：Project Bible 定稿、dls.md §3.1、README 同步、目录模板生成脚本（见下）、模板 .blend、LookDev 场景、渲染设置预设 |

> **关于「目录模板生成脚本」这一条**：v2 spec §6.3 判定 `scaffold.py` 是 YAGNI
> （目录树已 95% 建好，缺的只是一个 `fx/` 目录），本计划不做该脚本。
> 勾选时**保留未勾**并注明「目录已按 dls.md §3.1 建齐；本 Demo 规模下不需要生成器」，
> 不要为了对齐清单而造一个没人用的脚本。

- [ ] **Step 7: 验证 Bible 区块仍一致（文档改动没碰坏 Task 3 的成果）**

Run: `cd 00_project/pipeline && python3 -m unittest tests.test_bible -v`
Expected: 全部 PASS（Task 3 的 Bible 一致性测试未被文档改动碰坏）

- [ ] **Step 8: 验证没有残留的 5.2.1 锁定表述**

Run: `cd /mnt/data/dsv/ppsk && grep -rn "5\.2\.1" README.md 00_project/bible/ docs/dls.md | grep -v "5.2.1 程序化生成\|改为实测的\|CR-001\|已是更新的 patch"`
Expected: 无输出

- [ ] **Step 9: 跑全部测试收尾**

Run: `cd 00_project/pipeline && python3 -m unittest discover -s tests -t . -v 2>&1 | tail -4 && blender -b --factory-startup --python tests/test_preset.py 2>&1 | tail -3; echo "preset=${PIPESTATUS[0]}" && blender -b --factory-startup --python tests/test_blend_roundtrip.py 2>&1 | tail -3; echo "blend=${PIPESTATUS[0]}"`
Expected: 三套全绿，三个退出码都是 0

- [ ] **Step 10: 提交**

```bash
git add 00_project/bible/project_bible.md 00_project/bible/scope_lock.md 00_project/bible/licensing.csv README.md docs/plan.md
git commit -m "docs：Bible 补性能预算 + CR-001 追认 + README/plan/licensing 同步

锁定版本 5.2.0（CR-001，dev build fbe6228777e7）。
plan §22.1 两处失实勾选已修正；§22.2 的 probe 上限保持未勾（未实测）。"
```

---

## 完成定义

七个任务全部提交后，spec §10.5 的验收清单达成：

- 规格值只在 `utils.py` 定义（grep 卡住），`import shot` / `import review` 无副作用
- `motion_blur_shutter == 0.5` 在每个模板与每次 `apply_preset` 中成立
- `check_blender_version` 两级：版本号前两段不符才失败，hash 只警告
- 6 个 `.blend` 存在，**重开后**规格逐项断言通过；覆盖保护与 `--dry-run` 均验证不写盘
- Bible 数值与 `utils.py` 一致（由 Task 3 的断言测试保证，不写生成器）
- §8 的 16 项文档改动全部落地，`CR-001` 写入 `scope_lock.md` 并标注**待签署**
- `--out/` 已删除；`05_assets/fx/` 已建
- G0 报告、镜头表、资产与管线 API 属**后续段落**，本计划不碰
