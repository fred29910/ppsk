# 规范与模板基线 实施计划

> # ⛔ 本计划已作废，请勿执行
>
> **继任计划：[`2026-09-29-baseline-specs-templates-v2.md`](2026-09-29-baseline-specs-templates-v2.md)**
>
> 本计划基于 spec v1，而 spec v2（commit `fbdbf27`）**推翻了本计划要建的大半文件**：
>
> | 本计划要建 | v2 的处置 |
> |---|---|
> | `spec.py` 单一规格来源 | **不建**。唯一来源改用已存在的 `utils.py` |
> | `check_spec.py` | **不建**。改名 `check_bible.py`，数据源从 `spec.py` 换成 `utils.py` |
> | `scaffold.py` 目录生成器 | **不建**。目录树已 95% 建好，YAGNI（spec §6.3） |
> | `render_preset.py` | **不建**。渲染预设已在 `shot.py` 里，改为抽 `apply_preset()` 共用（spec §5.2） |
> | `build_templates.py` | 仍要建，但依赖改指向 `shot.apply_preset()` 而非 `render_preset.apply()` |
>
> 此外本计划基于一条**已被实测推翻的测量**：「本机无 Cycles / 无 Workbench」。
> 实测 `scene.render.engine = "CYCLES"` 赋值成功、`hasattr(scene, "cycles")` 为真、
> `device = "CPU"` —— **Cycles 可用（CPU only）**。`-b` 模式下 `engine` 静态枚举
> 只注册 `BLENDER_EEVEE`，不能据此判断引擎是否存在（spec §2.1）。
>
> **下方内容仅作历史记录保留。**

---

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立 `spec.py` 单一规格来源、`scaffold.py` 目录生成器、两个 `.blend` 模板生成器，并落地 5 份文档的定稿与变更记录。

**Architecture:** `spec.py`（纯数据，不 import bpy）→ `check_spec.py` 校验 Bible 生成区块；`scaffold.py` 只增不删地建目录；`render_preset.py` 提供 `apply(scene)` 函数，被 `build_templates.py` 烘进 `tpl_light_v001.blend`，下一段的 `setup_render` 复用同一函数。验收靠 `.blend` 往返测试（生成 → 重开 → 逐项断言），不靠"脚本没报错"。

**Tech Stack:** Blender 5.2.0 LTS（`blender`，dev build hash `fbe6228777e7`，无 Cycles / Workbench，无 GPU）、Python 3.13、`unittest`（stdlib，Blender 内置 Python 亦可用；**本机无 pytest，不得引入**）。

**Spec:** `docs/superpowers/specs/2026-09-29-baseline-specs-templates-design.md`

## Global Constraints

以下约束适用于每一个任务，逐条照抄执行：

- **Blender 版本号前两段必须为 `5.2`**，不匹配时退出码非 0。**build hash 不匹配只警告**——本机是 dev build（`fbe6228777e7`），官方 5.2.0 发行版 hash 必然不同（spec §5.2）
- **锁定版本为 5.2.0，不是 plan.md 原写的 5.2.1**。改版本号须走 `scope_lock.md` 的 CR-001 流程
- **`spec.py` / `check_spec.py` / `scaffold.py` 不得 import bpy**，必须能被系统 `python3` 直接导入
- 除 `spec.py` 外，任何模块**不得硬编码** `spec.py` 中的数值
- 所有函数接受 `project_root` 参数，无硬编码路径
- 只读函数绝不写盘；写盘函数必须有 `--dry-run`
- 返回约定（spec §9.2）：成功 `{"ok": True, ...}`，失败 `{"ok": False, "error": str, "hint": str}`
- **色彩管理的 view transform 是动态 RNA enum，`enum_items` 只返回 `['NONE']`**——校验一律用"赋值 + 读回"，禁止用 `enum_items` 做前置校验（spec §2.1）
- `motion_blur_shutter` 单位是**帧**不是角度。`shutter_deg / 360.0` → `0.5`；直接写 `180.0` 不报错但得到 180 帧模糊（spec §7.6）
- 目录结构只在 `chr/hero` 下建 `wip`/`publish`；`env` / `prp` / `fx` / `veh` / `lib` 平铺（spec §6）
- 本机无 GPU、无 Cycles。**不验证渲染画质、不填 `volumetric_samples` / `taa_render_samples`**（spec §11）
- `01_story/shotlist.csv` 存在但与 plan.md §13 Schema 有 6 处冲突（帧范围两列语义颠倒、主键格式、SEQ 分组、资产引用为中文散文、版本号两位、status 取 `pending`）。**本计划不读它、不改它**，那是下一段 `create_shot` 的前置决策

## Review Focus

以下五项是 spec 蕴含但没有任何测试覆盖、最可能咬人的输入。每项都已在其归属任务的步骤中加了钉住它的测试。

1. **`.blend` 已存在且被人在 GUI 里改过** — `build_templates` 必须跳过而非覆盖，否则吃掉手工工作（归属 Task 5）
2. **`--project-root` 指向错误目录**（无 `00_project/`） — 必须在写任何东西之前退出非 0，否则在错误位置建出一堆空壳（归属 Task 2）
3. **动态 RNA enum 静默失效** — 用 `enum_items` 校验 view transform 会让**任何**检查假通过，错误要到渲染阶段才暴露（归属 Task 4）
4. **`volumetric_samples` / `taa_render_samples` 为 `None`** — 下游 `setup_render` 拿到 `None` 若静默取默认值，会锁死错误的采样数且无人察觉（归属 Task 1）
5. **`--dry-run` 实际写了盘** — 只看返回值不看 mtime 会漏掉"报告说没写、实际写了"的情况（归属 Task 2、Task 5）

---

## File Structure

| 文件 | 职责 | 依赖 bpy |
|---|---|---|
| `00_project/pipeline/spec.py` | 全部规格数值的唯一来源 + 派生函数 | 否 |
| `00_project/pipeline/check_spec.py` | 渲染/校验/写回 Bible 规格生成区块 | 否 |
| `00_project/pipeline/scaffold.py` | 声明式目录树 + 只增不删地创建 | 否 |
| `00_project/pipeline/render_preset.py` | `apply(scene)` 渲染设置 + Blender 版本校验 | **是** |
| `00_project/pipeline/build_templates.py` | 生成 6 个 `.blend` 模板 | **是** |
| `00_project/pipeline/utils.py` | 新增 `make_object_name`（**改动现有文件，其余不动**） | 否 |
| `00_project/pipeline/tests/test_spec.py` | 派生函数 + 不变量 | 否 |
| `00_project/pipeline/tests/test_check_spec.py` | 区块渲染/校验/同步/元测试 | 否 |
| `00_project/pipeline/tests/test_scaffold.py` | 幂等、不删、dry-run、错误项目根 | 否 |
| `00_project/pipeline/tests/test_render_preset.py` | 读回断言、None 处理、版本校验 | **是** |
| `00_project/pipeline/tests/test_blend_roundtrip.py` | 生成 → 重开 → 逐项断言 | **是** |
| `00_project/pipeline/tests/_bootstrap.py` | 把 `00_project/pipeline` 加入 `sys.path` | 否 |

**测试运行方式**（`unittest`，两套解释器）：

```bash
# 纯 Python（系统 python3）
cd 00_project/pipeline && python3 -m unittest discover -s tests -t . -v

# 需要 bpy 的（Blender 内置 Python）
cd 00_project/pipeline && blender -b --factory-startup --python tests/test_render_preset.py
cd 00_project/pipeline && blender -b --factory-startup --python tests/test_blend_roundtrip.py
```

Blender 侧测试必须在文件末尾 `sys.exit(0 if result.wasSuccessful() else 1)`，已实测 Blender 会把它作为真实退出码传播（失败 = 1，通过 = 0）。每个 `test_*.py` 顶部：

```python
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

---

### Task 1: `spec.py` — 规格唯一来源

**Files:**
- Create: `00_project/pipeline/spec.py`
- Test: `00_project/pipeline/tests/test_spec.py`

**Interfaces:**
- Consumes: 无（首个任务）
- Produces: 模块级常量 `BLENDER_VERSION`(str `"5.2.0"`)、`BLENDER_BUILD_HASH`(str `"fbe6228777e7"`)、`BLENDER_BUILD_FLAVOR`(str `"dev"`)、`CYCLES_AVAILABLE`(bool `False`)，字典 `SPEC` / `COLOR` / `EXR` / `EEVEE` / `BUDGET`，函数 `shutter_frames() -> float`、`render_path(stage_dir: str, shot: str, stage: str, version: str, frame: int) -> str`

- [ ] **Step 1: 写失败的测试**

`00_project/pipeline/tests/test_spec.py`：

```python
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import spec


class TestShutter(unittest.TestCase):
    def test_shutter_deg_converts_to_frames(self):
        """180° 快门 = 0.5 帧。直接写 180.0 会得到 180 帧模糊。"""
        self.assertEqual(0.5, spec.shutter_frames())


class TestRenderPath(unittest.TestCase):
    def test_frame_is_zero_padded_to_four(self):
        p = spec.render_path("render/light/v003", "seq010_sh010", "light", "v003", 1001)
        self.assertEqual("render/light/v003/seq010_sh010_light_v003.1001.exr", p)

    def test_path_uses_spec_format(self):
        """路径必须用 spec.py 的 EXR['path']，不得硬编码 .exr"""
        self.assertTrue(p_endswith_exr := spec.render_path("d", "s", "l", "v001", 1).endswith(".exr"))
        self.assertIn(".exr", spec.EXR["path"])


class TestLocks(unittest.TestCase):
    def test_version_is_520_not_521(self):
        """CR-001：锁定 5.2.0（开发机实际版本），非 plan.md 原写的 5.2.1"""
        self.assertEqual("5.2.0", spec.BLENDER_VERSION)

    def test_samples_are_none_pending_g0(self):
        """无 GPU 时采样数无意义，必须留 None 让下游显式失败，不得填默认值"""
        self.assertIsNone(spec.EEVEE["volumetric_samples"])
        self.assertIsNone(spec.EEVEE["taa_render_samples"])

    def test_probe_limits_are_eevee_hard_limits(self):
        self.assertEqual(128, spec.EEVEE["max_probe_sphere"])
        self.assertEqual(16, spec.EEVEE["max_probe_plane"])


class TestBudget(unittest.TestCase):
    def test_budget_covers_plan_section_11(self):
        for k in ("tris_per_shot", "materials", "lights", "vdb_resolution",
                  "gn_instances", "vram_gb", "view_layers"):
            self.assertIn(k, spec.BUDGET)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd 00_project/pipeline && python3 -m unittest discover -s tests -t . -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'spec'`

- [ ] **Step 3: 实现 `spec.py`**

`00_project/pipeline/spec.py` 文件头必须是这段 docstring（禁止 import bpy 的理由写在里面）：

```python
"""项目规格 —— 唯一机器可读来源。

不 import bpy：本模块必须能被系统 Python 直接导入（check_spec / scaffold 在 Blender 外跑）。
所有数值与 00_project/bible/project_bible.md 的规格生成区块保持一致，由 check_spec.py 校验。
禁止在其他模块硬编码这些值。
"""
```

然后按 spec §5.1 逐字写入常量 `BLENDER_VERSION` / `BLENDER_BUILD_HASH` / `BLENDER_BUILD_FLAVOR` / `CYCLES_AVAILABLE` 与字典 `SPEC` / `COLOR` / `EXR` / `EEVEE` / `BUDGET`，值必须与 spec §5.1 代码块完全一致——包括 `volumetric_samples: None` 与 `taa_render_samples: None` 这两个留空项。

`spec.py` 中**必须**额外提供这两个派生函数（这是 Step 1 测试所 pin 的逻辑，不得内联到字典里）：

```python
def shutter_frames() -> float:
    """快门角度（度）→ Blender 的 motion_blur_shutter（帧）。180° → 0.5 帧。"""
    return SPEC["shutter_deg"] / 360.0


def render_path(stage_dir: str, shot: str, stage: str, version: str, frame: int) -> str:
    """按 EXR['path'] 模板渲染帧文件路径。"""
    return os.path.join(stage_dir, EXR["path"].format(
        stage_dir=stage_dir, shot=shot, stage=stage, version=version, frame=frame))
```

`render_path` 需 `import os`。`EXR["path"]` 模板保留 spec 中的 `{stage_dir}` 占位（会被 `os.path.join` 覆盖一次，无副作用）。

- [ ] **Step 4: 运行测试确认通过**

Run: `cd 00_project/pipeline && python3 -m unittest discover -s tests -t . -v`
Expected: PASS，8 个测试全绿

- [ ] **Step 5: 确认 spec.py 可被系统 python 导入且未拉入 bpy**

Run: `cd 00_project/pipeline && python3 -c "import spec, sys; assert 'bpy' not in sys.modules, 'spec.py 不得 import bpy'; print('ok', spec.BLENDER_VERSION, spec.shutter_frames())"`
Expected: 输出 `ok 5.2.0 0.5`

- [ ] **Step 6: 提交**

```bash
git add 00_project/pipeline/spec.py 00_project/pipeline/tests/test_spec.py
git commit -m "feat(spec)：规格唯一来源 spec.py

锁定 Blender 5.2.0（build hash fbe6228777e7，dev build）。
volumetric_samples / taa_render_samples 留 None，待 G0 实测后填。"
```

---

### Task 2: `scaffold.py` — 目录结构生成器

**Files:**
- Create: `00_project/pipeline/scaffold.py`
- Test: `00_project/pipeline/tests/test_scaffold.py`

**Interfaces:**
- Consumes: `spec`（仅用于读取 `SPEC`，实际目录树不依赖它）
- Produces: `DIRS`(tuple of 相对路径 str)、`plan_dirs(project_root: str) -> dict`、`apply_dirs(project_root: str, apply: bool = False) -> dict`、`main(argv: list[str] | None) -> int`

- [ ] **Step 1: 写失败的测试**

`00_project/pipeline/tests/test_scaffold.py`：

```python
import os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scaffold


def make_root():
    """造一个合法的项目根：必须含 00_project/。"""
    root = tempfile.mkdtemp()
    os.makedirs(os.path.join(root, "00_project"))
    return root


class TestDirList(unittest.TestCase):
    def test_wip_publish_only_under_chr_hero(self):
        """spec §6：只有 chr/hero 有 wip/publish，env/prp/fx 不擅自推广"""
        wip = [d for d in scaffold.DIRS if d.endswith("/wip")]
        self.assertEqual(["05_assets/chr/hero/wip"], wip)

    def test_fx_is_top_level_peer(self):
        self.assertIn("05_assets/fx", scaffold.DIRS)

    def test_veh_is_retained_but_empty(self):
        self.assertIn("05_assets/veh", scaffold.DIRS)
        self.assertFalse([d for d in scaffold.DIRS if d.startswith("05_assets/veh/")])

    def test_no_shot_seq_dirs(self):
        """镜头目录依赖镜头表，属下一段 create_shot"""
        self.assertFalse([d for d in scaffold.DIRS if d.startswith("06_shots/seq")])


class TestApply(unittest.TestCase):
    def test_creates_missing_dirs(self):
        root = make_root()
        r = scaffold.apply_dirs(root, apply=True)
        self.assertTrue(r["ok"], r)
        self.assertTrue(os.path.isdir(os.path.join(root, "05_assets/fx")))
        self.assertGreater(len(r["created"]), 10)

    def test_idempotent_second_run_creates_nothing(self):
        root = make_root()
        scaffold.apply_dirs(root, apply=True)
        r2 = scaffold.apply_dirs(root, apply=True)
        self.assertEqual([], r2["created"])
        self.assertGreater(len(r2["skipped"]), 10)

    def test_never_deletes_existing_content(self):
        """Review Focus #2：目录里有用户文件必须跳过，绝不删"""
        root = make_root()
        d = os.path.join(root, "05_assets/prp")
        os.makedirs(d)
        marker = os.path.join(d, "我的设计稿.txt")
        open(marker, "w").write("keep me")
        r = scaffold.apply_dirs(root, apply=True)
        self.assertTrue(r["ok"])
        self.assertTrue(os.path.exists(marker))

    def test_dry_run_does_not_touch_disk(self):
        """Review Focus #5：用 mtime 验证，不信返回值"""
        root = make_root()
        probe = os.path.join(root, "05_assets")
        before = os.stat(root).st_mtime_ns
        r = scaffold.apply_dirs(root, apply=False)
        self.assertTrue(r["ok"])
        self.assertGreater(len(r["created"]), 10)   # 报告说要建
        self.assertFalse(os.path.exists(probe))     # 但没建
        self.assertEqual(before, os.stat(root).st_mtime_ns)

    def test_wrong_project_root_errors_without_writing(self):
        """Review Focus #2：无 00_project/ 的目录必须拒绝，且不建任何东西"""
        empty = tempfile.mkdtemp()
        r = scaffold.apply_dirs(empty, apply=True)
        self.assertFalse(r["ok"])
        self.assertIn("00_project", r["hint"])
        self.assertEqual([], os.listdir(empty))
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd 00_project/pipeline && python3 -m unittest discover -s tests -t . -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scaffold'`

- [ ] **Step 3: 实现 `scaffold.py`**

模块 docstring：

```python
"""目录结构生成器 —— 声明式、幂等、只增不删。

不 import bpy：必须能在系统 Python 下运行。
目录树对应 docs/dls.md §3.1（+ fx/ 提升，见 spec D5）。不建 seq###/sh###：
镜头目录依赖镜头表，属下一段 create_shot。
"""
```

`DIRS` 写成 tuple of 正斜杠相对路径，顺序为 `00_project` 四个子目录 → `01_story` … `04_audio` → `05_assets`（`chr/hero/wip`、`chr/hero/publish`、`env`、`prp`、`fx`、`veh`、`lib`）→ `06_shots` → `07_review` / `08_delivery` / `09_archive`。父目录不必单列——`os.makedirs` 会带上，但为了让 `DIRS` 同时可读，把父目录也列进去。

两个函数的契约：

- `plan_dirs(project_root)` **绝不写盘**（plan §12.1 只读函数不写盘）。先校验 `project_root/00_project` 存在，否则返回 `{"ok": False, "error": "project root 缺少 00_project/", "hint": "用 --project-root 指向工程根目录，不是它的子目录"}`。然后返回 `{"ok": True, "created": [...缺失项...], "skipped": [...已存在项...]}`
- `apply_dirs(project_root, apply=False)`：校验同上；`apply=False` 时只返回计划（不写盘）；`apply=True` 时 `os.makedirs(..., exist_ok=True)` 逐个创建。**代码中不得出现 `os.remove` / `os.rmdir` / `shutil.rmtree`**。返回 `{"ok": True, "created": [...], "skipped": [...], "warnings": []}`
- `main(argv)`：`argparse`，`--project-root`（默认 `"."`）与 `--apply`（store_true）。返回 `0` / `1`；失败时打印返回的 `error` + `hint`
- `if __name__ == "__main__": sys.exit(main())`

- [ ] **Step 4: 运行测试确认通过**

Run: `cd 00_project/pipeline && python3 -m unittest discover -s tests -t . -v`
Expected: PASS

- [ ] **Step 5: 在真实工程上跑 dry-run，确认零写入**

Run: `cd /mnt/data/dsv/ppsk && python3 00_project/pipeline/scaffold.py --project-root .` 
Expected: 打印将要创建的目录清单，退出码 0。再次运行并用 `git status --short` 确认工作区**没有**新增未跟踪文件（dry-run 不落盘）

- [ ] **Step 6: 提交**

```bash
git add 00_project/pipeline/scaffold.py 00_project/pipeline/tests/test_scaffold.py
git commit -m "feat(scaffold)：声明式目录生成器，幂等且只增不删"
```

---

### Task 3: `check_spec.py` + Bible 规格生成区块

**Files:**
- Create: `00_project/pipeline/check_spec.py`
- Modify: `00_project/bible/project_bible.md`（插入生成区块）
- Test: `00_project/pipeline/tests/test_check_spec.py`

**Interfaces:**
- Consumes: `spec`（全部数值来源）
- Produces: `BEGIN`(str `"<!-- BEGIN GENERATED: spec.py -->"`)、`END`(str `"<!-- END GENERATED: spec.py -->"`)、`render_block() -> str`、`extract_block(text: str) -> str | None`、`check_text(bible: str) -> dict`、`sync_text(bible: str) -> str`、`main(argv: list[str] | None) -> int`

- [ ] **Step 1: 写失败的测试**

`00_project/pipeline/tests/test_check_spec.py`：

```python
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import check_spec, spec


SEED = "前置正文\n\n" + check_spec.BEGIN + "\nSTALE\n" + check_spec.END + "\n\n后置正文\n"


class TestBlock(unittest.TestCase):
    def test_render_block_is_deterministic(self):
        self.assertEqual(check_spec.render_block(), check_spec.render_block())

    def test_render_block_contains_key_values(self):
        b = check_spec.render_block()
        self.assertIn(str(spec.SPEC["resolution"][0]), b)
        self.assertIn("AgX", b)
        self.assertIn("5.2.0", b)
        self.assertIn("0.5", b)          # 快门换算后的帧值

    def test_extract_returns_inner_text(self):
        self.assertEqual("STALE", check_spec.extract_block(SEED).strip())

    def test_extract_missing_block_is_none(self):
        self.assertIsNone(check_spec.extract_block("没有区块"))


class TestCheck(unittest.TestCase):
    def test_matching_block_passes(self):
        good = "x\n" + check_spec.BEGIN + "\n" + check_spec.render_block() + "\n" + check_spec.END + "\n"
        r = check_spec.check_text(good)
        self.assertTrue(r["ok"], r)

    def test_stale_block_fails_and_names_the_field(self):
        """元测试：校验器必须能抓到真实的差异，否则是装饰品"""
        r = check_spec.check_text(SEED)
        self.assertFalse(r["ok"])
        self.assertIn("stale", r["error"].lower())

    def test_missing_block_fails(self):
        r = check_spec.check_text("无区块")
        self.assertFalse(r["ok"])
        self.assertIn("区块", r["error"])

    def test_check_does_not_write(self):
        """只读函数绝不写盘"""
        before = check_spec.render_block()
        check_spec.check_text(SEED)
        self.assertEqual(before, check_spec.render_block())


class TestSync(unittest.TestCase):
    def test_sync_replaces_block_content(self):
        out = check_spec.sync_text(SEED)
        self.assertEqual("前置正文", out.splitlines()[0])
        self.assertIn("前置正文", out)
        self.assertIn("后置正文", out)
        self.assertNotIn("STALE", out)

    def test_sync_is_idempotent(self):
        once = check_spec.sync_text(SEED)
        twice = check_spec.sync_text(once)
        self.assertEqual(once, twice)
        self.assertTrue(check_spec.check_text(twice)["ok"])


class TestSelfTamper(unittest.TestCase):
    """Review Focus：改坏 spec.py 后校验必须报出来（端到端证伪）"""
    def test_mismatch_detected_when_spec_changes(self):
        original = spec.SPEC["fps"]
        try:
            spec.SPEC["fps"] = 30
            r = check_spec.check_text(
                check_spec.BEGIN + "\n" + check_spec.render_block() + "\n" + check_spec.END + "\n")
            self.assertFalse(r["ok"])
        finally:
            spec.SPEC["fps"] = original
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd 00_project/pipeline && python3 -m unittest discover -s tests -t . -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'check_spec'`

- [ ] **Step 3: 实现 `check_spec.py`**

模块 docstring：

```python
"""校验 00_project/bible/project_bible.md 的规格生成区块与 spec.py 一致。

不 import bpy。默认只比对不写盘；--sync 才写回。
不解析 Markdown 表格——区块本身就是 check_spec 渲染的格式。
"""
```

- `BEGIN = "<!-- BEGIN GENERATED: spec.py -->"`、`END = "<!-- END GENERATED: spec.py -->"`
- `render_block() -> str`：从 `spec` 渲染一张 Markdown 表格，列至少覆盖：Blender 版本 / build hash / 分辨率 / fps / 快门（角度与换算后的帧值两个都要出现）/ 帧范围 / 单位 / 色彩管理四元组 / EXR 格式与位深 / 运动模糊与 Vector 取值 / EEVEE probe 上限与 shadow pool / 性能预算（`spec.BUDGET` 全部键）。**不得出现字面量**——所有数字都从 `spec` 取（例如 `"{}°（{:.1f} 帧）".format(spec.SPEC["shutter_deg"], spec.shutter_frames())`）
- `extract_block(text) -> str | None`：返回 `BEGIN` 与 `END` 之间的内容；任一哨兵缺失返回 `None`
- `check_text(bible: str) -> dict`：无区块 → `{"ok": False, "error": "Bible 中找不到规格生成区块", "hint": "插入 BEGIN/END 哨兵，或跑 --sync 生成"}`；内容与 `render_block()` 不一致 → `{"ok": False, "error": "Bible 规格区块与 spec.py 不一致（区块 stale）", "hint": "跑 check_spec.py --sync 更新区块"}`；一致 → `{"ok": True}`
- `sync_text(bible: str) -> str`：区块不存在则**不猜位置**，返回原串（由调用方报告错误）；存在则整段替换为 `render_block()`，**哨兵行与区块外的所有内容逐字保留**
- `main(argv)`：`--project-root`（默认 `"."`）、`--sync`。`--sync` 需同时给 `--apply` 才写盘（与其它写盘函数一致的显式开关）；否则只打印差异并返回 `1`。成功 `0`

- [ ] **Step 4: 运行测试确认通过**

Run: `cd 00_project/pipeline && python3 -m unittest discover -s tests -t . -v`
Expected: PASS

- [ ] **Step 5: 在真实 Bible 上跑一次同步（此时 Bible 还没有区块，预期失败并给出 hint）**

Run: `cd /mnt/data/dsv/ppsk && python3 00_project/pipeline/check_spec.py --project-root . --sync --apply`
Expected: 退出码非 0，提示找不到区块。此时**在 `project_bible.md` 末尾插入空区块哨兵**：

```
<!-- BEGIN GENERATED: spec.py -->
<!-- END GENERATED: spec.py -->
```

- [ ] **Step 6: 再次同步并确认校验通过（往返幂等）**

Run: `cd /mnt/data/dsv/ppsk && python3 00_project/pipeline/check_spec.py --project-root . --sync --apply && python3 00_project/pipeline/check_spec.py --project-root .`
Expected: 第一次退出 0 并写入区块；第二次退出 0（不再报 stale）

- [ ] **Step 7: 人工确认区块里没有硬编码漂移**

Run: `cd /mnt/data/dsv/ppsk && grep -n "1920\|5.2.0\|0.5\|AgX" 00_project/bible/project_bible.md`
Expected: 每个命中都落在生成区块内，且值与 `spec.py` 一致

- [ ] **Step 8: 提交**

```bash
git add 00_project/pipeline/check_spec.py 00_project/pipeline/tests/test_check_spec.py 00_project/bible/project_bible.md
git commit -m "feat(check_spec)：Bible 规格生成区块与 spec.py 的一致性校验"
```

---

### Task 4: `render_preset.py` — 渲染设置预设

**Files:**
- Create: `00_project/pipeline/render_preset.py`
- Test: `00_project/pipeline/tests/test_render_preset.py`

**Interfaces:**
- Consumes: `spec`（全部取值来源）
- Produces: `REQUIRED_VERSION_PREFIX`(str `"5.2"`)、`check_blender_version() -> dict`、`apply(scene, project_root: str) -> dict`、`main(argv: list[str] | None) -> int`

- [ ] **Step 1: 写失败的测试**

`00_project/pipeline/tests/test_render_preset.py`：

```python
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bpy
import render_preset, spec


def fresh_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


class TestVersionCheck(unittest.TestCase):
    def test_prefix_matches_locked_version(self):
        self.assertEqual(render_preset.REQUIRED_VERSION_PREFIX, ".".join(spec.BLENDER_VERSION.split(".")[:2]))

    def test_check_passes_on_this_build(self):
        r = render_preset.check_blender_version()
        self.assertTrue(r["ok"], r)
        self.assertIn(bpy.app.version_string.split()[1][:3], r["version"])

    def test_hash_mismatch_is_warning_not_failure(self):
        """build hash 与 dev build 不同时必须继续，只警告"""
        r = render_preset.check_blender_version(expected_hash="deadbeef0000")
        self.assertTrue(r["ok"])
        self.assertTrue(r["warnings"])


class TestApply(unittest.TestCase):
    def setUp(self):
        self.scene = fresh_scene()
        self.r = render_preset.apply(self.scene, "/tmp/opencode")

    def test_resolution_and_fps(self):
        self.assertEqual(list(spec.SPEC["resolution"]),
                         [self.scene.render.resolution_x, self.scene.render.resolution_y])
        self.assertEqual(spec.SPEC["fps"], self.scene.render.fps)

    def test_shutter_is_frames_not_degrees(self):
        """Review Focus #3：直接写 180.0 会被当成 180 帧"""
        self.assertAlmostEqual(0.5, self.scene.render.motion_blur_shutter, places=5)
        self.assertNotAlmostEqual(spec.SPEC["shutter_deg"], self.scene.render.motion_blur_shutter)

    def test_color_management_readback(self):
        vs, ds = self.scene.view_settings, self.scene.display_settings
        self.assertEqual(spec.COLOR["view_transform"], vs.view_transform)
        self.assertEqual(spec.COLOR["display_device"], ds.display_device)

    def test_engine_and_units(self):
        self.assertEqual(spec.EEVEE["engine"], self.scene.render.engine)
        self.assertEqual("METRIC", self.scene.unit_settings.system)

    def test_exr_settings(self):
        im = self.scene.render.image_settings
        self.assertEqual("OPEN_EXR_MULTILAYER", im.file_format)
        self.assertEqual("16", im.color_depth)

    def test_motion_blur_off_vector_on(self):
        """D7：运动模糊与 Vector Pass 互斥，选后者"""
        self.assertFalse(self.scene.render.use_motion_blur)
        self.assertTrue(self.scene.view_layers[0].use_pass_vector)

    def test_none_samples_raise_instead_of_defaulting(self):
        """Review Focus #4：None 必须显式失败，不得静默取默认"""
        r = render_preset.apply(self.scene, "/tmp/opencode")
        self.assertFalse(r["ok"])
        self.assertIn("volumetric_samples", r["error"] + r["hint"])

    def test_apply_reports_passes_effective(self):
        vl = self.scene.view_layers[0]
        self.assertIn("passes_effective", self.r)
        self.assertIn("z", self.r["passes_effective"])
        # 读回只证明勾选状态，不证明数据正确 —— 见 spec §5.1
        self.assertTrue(vl.use_pass_z)


if __name__ == "__main__":
    # 退出码契约：Blender 把 sys.exit 的值作为真实退出码传播（失败=1，通过=0）。
    # 不用 unittest.main()：它解析 sys.argv，而 Blender 传进来的是自己的参数。
    _suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    _result = unittest.TextTestRunner(verbosity=2).run(_suite)
    sys.exit(0 if _result.wasSuccessful() else 1)
```

> **不要用 `unittest.main()`。** 它在 Blender 下解析 `sys.argv`（含 Blender 自身参数），实测失败用例返回退出码 2、通过用例返回 0——**失败不会让命令失败**。必须用 `TextTestRunner` + `loadTestsFromModule`，再 `sys.exit(0 if result.wasSuccessful() else 1)`（此模式实测：失败 = 1，通过 = 0）。

- [ ] **Step 2: 运行测试确认失败**

Run: `cd 00_project/pipeline && blender -b --factory-startup --python tests/test_render_preset.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'render_preset'`

- [ ] **Step 3: 实现 `render_preset.py`**

模块 docstring：

```python
"""渲染设置预设 —— 唯一实现，供 build_templates 与（下一段）setup_render 共用。

需要 bpy。本模块不硬编码任何数值，全部取自 spec.py。
"""
```

- `REQUIRED_VERSION_PREFIX = ".".join(spec.BLENDER_VERSION.split(".")[:2])`
- `check_blender_version(expected_hash: str | None = None) -> dict`：取 `bpy.app.version` 的前两段拼成字符串；不等于 `REQUIRED_VERSION_PREFIX` → `{"ok": False, "error": "Blender 版本不符：需 {前缀}，实际 {实际}", "hint": "见 spec §5.2 与 scope_lock.md CR-001"}`。hash 不同**不失败**，`warnings` 里带上实际 hash。成功返回 `{"ok": True, "version": ..., "hash": ..., "warnings": [...]}`
- `apply(scene, project_root: str) -> dict`：先 `check_blender_version()`，不符则**直接返回失败，不改场景任何设置**。然后设：
  - `render.resolution_x/y` ← `spec.SPEC["resolution"]`；`fps`；`fps_base` 保持 1.0
  - `render.motion_blur_shutter = spec.shutter_frames()`；`render.use_motion_blur = spec.EXR["motion_blur"]`
  - `view_settings.view_transform` / `look`、`display_settings.display_device` ← `spec.COLOR`；`sequencer_colorspace_settings.name = spec.COLOR["display_device"]`
  - `unit_settings.system` / `scale_length` ← `spec.SPEC["unit"]`
  - `render.engine = spec.EEVEE["engine"]`
  - `eevee.shadow_pool_size = spec.EEVEE["shadow_pool_size"]`（**设为 str，`bpy` 接受字符串赋值**）
  - `render.image_settings`：`file_format` / `color_depth` ← `spec.EXR`；`color_management = "FOLLOW_SCENE"`
  - `render.filepath` ← `spec.render_path(os.path.join(project_root, "06_shots", "<shot>", "render", stage, version), ...)` 的目录部分（即 `.../render/<stage>/<version>/`）
  - 逐个 `scene.view_layers[0].use_pass_<name> = True` ← `spec.EEVEE["passes_required"]` 中以 `use_pass_` 前缀存在的项
  - **全部设完后读回** `view_layers[0]` 的 `use_pass_*`，把实际为 `True` 的 pass 名（去掉前缀、小写）写进返回值的 `passes_effective`
  - **若 `spec.EEVEE["volumetric_samples"]` 或 `taa_render_samples` 为 `None`**：不猜默认值。返回 `{"ok": False, "error": "spec.EEVEE['volumetric_samples'] 为 None", "hint": "待 G0 实测后填入 spec.py，不得静默使用默认值", "passes_effective": [...], "warnings": [...]}`——**其余已设项保留并已读回**
  - 成功返回 `{"ok": True, "passes_effective": [...], "warnings": [...]}`
- `main(argv)`：`--project-root`（默认 `"."`）；`apply()` 到 `bpy.context.scene` 并 `print` 返回值；成功 `0` / 失败 `1`

- [ ] **Step 4: 运行测试确认通过**

Run: `cd 00_project/pipeline && blender -b --factory-startup --python tests/test_render_preset.py 2>&1 | tail -20`
Expected: 全部 OK，`sys.exit` 给出 0（用 `echo $?` 确认为 0）

- [ ] **Step 5: 确认 apply 不抛异常（None 采样数走返回值而非异常）**

Run: `cd 00_project/pipeline && blender -b --factory-startup --python-expr "import sys; sys.path.insert(0,'.'); import render_preset; r=render_preset.apply(__import__('bpy').context.scene,'.'); print('OK_FLAG',r['ok']); print('PASSES',r['passes_effective'][:5])" 2>&1 | grep -E "OK_FLAG|PASSES"`
Expected: `OK_FLAG False` + 一个非空 PASSES 列表（证明"失败但仍读回并报告"）

- [ ] **Step 6: 提交**

```bash
git add 00_project/pipeline/render_preset.py 00_project/pipeline/tests/test_render_preset.py
git commit -m "feat(render_preset)：EEVEE 渲染设置预设与两级版本校验

None 采样数显式失败并给 hint，不静默取默认值。"
```

---

### Task 5: `build_templates.py` + `.blend` 往返测试

**Files:**
- Create: `00_project/pipeline/build_templates.py`
- Modify: `00_project/pipeline/utils.py`（**只追加** `make_object_name`，其余一行不动）
- Test: `00_project/pipeline/tests/test_blend_roundtrip.py`

**Interfaces:**
- Consumes: `spec`、`render_preset.apply(scene, project_root)`、`utils.make_object_name(prefix, name)`
- Produces: `TEMPLATES`(tuple of (filename, stage_kind) 描述)、`COLLECTIONS`(tuple of collection 名)、`build(project_root: str, apply: bool = False, overwrite: bool = False) -> dict`、`main(argv: list[str] | None) -> int`

- [ ] **Step 1: 先加 `make_object_name` 并写它的失败测试**

在 `00_project/pipeline/utils.py` **末尾追加**（不改动文件已有内容）：

```python
def make_object_name(prefix: str, name: str) -> str:
    """对象名：保留 dls.md 规定的大写前缀，如 CAM_cam / GEO_grayball。
    资产 ID 才用 normalize_name（小写下划线）。两者不可混用。"""
    import re as _re
    clean = _re.sub(r"[^A-Za-z0-9_]", "_", name)
    clean = _re.sub(r"_+", "_", clean).strip("_")
    return f"{prefix}_{clean}" if clean else prefix
```

在 `tests/test_spec.py` 末尾追加（保持 import 段不变，加 `import utils`）：

```python
class TestObjectName(unittest.TestCase):
    def test_keeps_uppercase_prefix(self):
        """normalize_name 会转小写，违反 dls.md 的 GEO_/CAM_ 前缀规范"""
        self.assertEqual("CAM_cam", utils.make_object_name("CAM", "cam"))
        self.assertEqual("GEO_grayball", utils.make_object_name("GEO", "grayball"))

    def test_normalize_name_is_for_asset_ids(self):
        self.assertEqual("chr_hero", utils.normalize_name("CHR-Hero"))
```

Run: `cd 00_project/pipeline && python3 -m unittest discover -s tests -t . -v`
Expected: 先 FAIL（`make_object_name` 不存在），追加函数后 PASS

- [ ] **Step 2: 写往返测试**

`00_project/pipeline/tests/test_blend_roundtrip.py`。**这个测试不生成文件——生成由 Task 5 Step 5 手工/命令行完成，测试只负责重开并断言**：

```python
import os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bpy
import spec, build_templates

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
TPL_DIR = os.path.join(ROOT, "00_project", "templates")


def open_blend(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    return bpy.context.scene


class TestAllTemplatesExist(unittest.TestCase):
    def test_every_template_file_present(self):
        for name, _ in build_templates.TEMPLATES:
            self.assertTrue(os.path.exists(os.path.join(TPL_DIR, name)), name)


class TestSharedSettings(unittest.TestCase):
    """每个模板重开后都必须满足的规格项 —— spec §10.2 往返断言"""

    def _assert_common(self, sc):
        self.assertEqual(list(spec.SPEC["resolution"]),
                         [sc.render.resolution_x, sc.render.resolution_y])
        self.assertEqual(spec.SPEC["fps"], sc.render.fps)
        self.assertEqual("METRIC", sc.unit_settings.system)
        self.assertEqual(spec.EEVEE["engine"], sc.render.engine)
        self.assertEqual(spec.COLOR["view_transform"], sc.view_settings.view_transform)
        self.assertEqual(spec.COLOR["look"], sc.view_settings.look)
        self.assertEqual(spec.COLOR["display_device"], sc.display_settings.display_device)
        self.assertEqual(spec.SPEC["frame"]["first"], sc.frame_start)
        self.assertEqual(spec.SPEC["frame"]["end"], sc.frame_end)
        self.assertAlmostEqual(0.5, sc.render.motion_blur_shutter, places=5)

    def test_all_templates_carry_shared_settings(self):
        for name, _ in build_templates.TEMPLATES:
            with self.subTest(template=name):
                self._assert_common(open_blend(os.path.join(TPL_DIR, name)))


class TestStageSpecific(unittest.TestCase):
    def test_layout_has_camera_and_guides(self):
        sc = open_blend(os.path.join(TPL_DIR, "tpl_layout_v001.blend"))
        objs = bpy.data.objects
        self.assertTrue(any(o.type == "CAMERA" for o in objs))
        self.assertIn("GUIDE_", bpy.data.collections)

    def test_vertical_guides_never_render(self):
        """spec §7.4：9:16 只做 Layout 阶段参考线，绝不能进渲染"""
        open_blend(os.path.join(TPL_DIR, "tpl_layout_v001.blend"))
        guides = [o for o in bpy.data.objects if "guide" in o.name.lower()]
        self.assertTrue(guides, "缺少 9:16 参考线对象")
        for g in guides:
            self.assertTrue(g.hide_render, f"{g.name} 的 hide_render 必须为 True")

    def test_camera_defaults_follow_spec(self):
        """spec §7.5：模板只固定不随镜头变化的部分"""
        open_blend(os.path.join(TPL_DIR, "tpl_layout_v001.blend"))
        cam = [o for o in bpy.data.objects if o.type == "CAMERA"][0].data
        self.assertEqual("CAM_cam", bpy.data.objects[[o.name for o in bpy.data.objects
                         if o.type == "CAMERA"][0]].name.split(".")[0] or cam.name)
        self.assertEqual(0.0, cam.shift_x)
        self.assertEqual(0.0, cam.shift_y)
        self.assertEqual(35.0, cam.lens)          # 占位值，逐镜由 shotlist 覆盖

    def test_light_has_render_settings(self):
        sc = open_blend(os.path.join(TPL_DIR, "tpl_light_v001.blend"))
        self.assertEqual("OPEN_EXR_MULTILAYER", sc.render.image_settings.file_format)
        self.assertTrue(any(vl.name.startswith("VL_") for vl in sc.view_layers))
        self.assertTrue(any(o.type == "LIGHT" for o in bpy.data.objects))

    def test_anim_has_no_camera(self):
        bpy.ops.wm.open_mainfile(filepath=os.path.join(TPL_DIR, "tpl_anim_v001.blend"))
        self.assertFalse([o for o in bpy.data.objects if o.type == "CAMERA"])

    def test_lookdev_has_colorchecker_and_grayballs(self):
        bpy.ops.wm.open_mainfile(filepath=os.path.join(TPL_DIR, "tpl_lookdev_v001.blend"))
        self.assertGreaterEqual(len([o for o in bpy.data.objects if o.type == "MESH"]), 4)
        names = [o.name for o in bpy.data.objects]
        self.assertTrue(any("colorchecker" in n for n in names), "缺少 ColorChecker 色卡")
        self.assertGreaterEqual(len([n for n in names if "grayball" in n]), 3)

    def test_lookdev_reports_missing_hdri_instead_of_faking_it(self):
        """spec §10.4：HDRI 缺失要报警告，不伪造纯色环境。
        建到临时 root，不碰真实模板（否则会与覆盖保护测试相互干扰）。"""
        tmp = tempfile.mkdtemp()
        os.makedirs(os.path.join(tmp, "00_project", "templates"))
        r = build_templates.build(tmp, apply=True, overwrite=False)
        self.assertTrue(r["ok"], r)
        self.assertTrue(any("HDRI" in w for w in r["warnings"]),
                        f"HDRI 缺失未进入 warnings: {r['warnings']}")
        for name, _ in build_templates.TEMPLATES:
            self.assertTrue(os.path.exists(
                os.path.join(tmp, "00_project", "templates", name)), name)


class TestOverwriteProtection(unittest.TestCase):
    """Review Focus #1：已存在的 .blend 必须跳过，GUI 里的手工修改不能被吃掉"""

    def test_existing_file_is_skipped_without_overwrite(self):
        p = os.path.join(TPL_DIR, "tpl_anim_v001.blend")
        self.assertTrue(os.path.exists(p))
        r = build_templates.build(ROOT, apply=True, overwrite=False)
        self.assertTrue(r["ok"], r)
        self.assertIn("tpl_anim_v001.blend", r["skipped"])
        self.assertNotIn("tpl_anim_v001.blend", r["written"])

    def test_overwrite_flag_actually_rewrites(self):
        """反向：显式 --overwrite 必须真的写，否则保护逻辑是死代码"""
        tmp = tempfile.mkdtemp()
        os.makedirs(os.path.join(tmp, "00_project", "templates"))
        target = os.path.join(tmp, "00_project", "templates", "tpl_anim_v001.blend")
        with open(target, "wb") as f:
            f.write(b"hand edited in gui")
        r = build_templates.build(tmp, apply=True, overwrite=True)
        self.assertTrue(r["ok"], r)
        self.assertIn("tpl_anim_v001.blend", r["written"])
        with open(target, "rb") as f:
            self.assertNotEqual(b"hand edited in gui", f.read())


if __name__ == "__main__":
    # 同 Task 4：不用 unittest.main()（它会解析 sys.argv）
    _suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    _result = unittest.TextTestRunner(verbosity=2).run(_suite)
    sys.exit(0 if _result.wasSuccessful() else 1)
```

- [ ] **Step 3: 运行测试确认失败**

Run: `cd 00_project/pipeline && blender -b --factory-startup --python tests/test_blend_roundtrip.py 2>&1 | tail -15; echo "exit=$?"`
Expected: FAIL — `ModuleNotFoundError: No module named 'build_templates'`

- [ ] **Step 4: 实现 `build_templates.py`**

模块 docstring：

```python
"""生成 6 个环节模板 .blend。需要 bpy。

绝不覆盖已存在的 .blend（除非显式 --overwrite）：模板会被人在 GUI 里改，
生成器不能默默吃掉手工工作。
"""

COLLECTIONS = ("CHR_", "ENV_", "PRP_", "FX_", "LGT_", "GUIDE_")

TEMPLATES = (
    ("tpl_layout_v001.blend", "layout"),
    ("tpl_anim_v001.blend",   "anim"),
    ("tpl_cfx_v001.blend",    "cfx"),
    ("tpl_fx_v001.blend",     "fx"),
    ("tpl_light_v001.blend",  "light"),
    ("tpl_lookdev_v001.blend", "lookdev"),
)
```

`build(project_root: str, apply: bool = False, overwrite: bool = False) -> dict` 的行为：

- 校验 `<project_root>/00_project` 存在，否则失败（同 `scaffold` 的错误约定）
- `apply=False` 时只报告计划，返回 `{"ok": True, "written": [...], "skipped": [...]}`
- `apply=True`：逐个模板，`os.path.exists` 且 `overwrite=False` → 记入 `skipped`；否则
  1. `bpy.ops.wm.read_factory_settings(use_empty=True)` 重置（保证每个模板干净）
  2. 建 `COLLECTIONS` 里该 stage 需要的 collection：`layout` → `CHR_ ENV_ PRP_ GUIDE_`；`anim` → `CHR_`；`cfx` → `CHR_` + `CHR_cloth`；`fx` → `FX_`；`light` → `LGT_`；`lookdev` → 不建这些
  3. `layout`：加 `CAM_cam`（名字用 `utils.make_object_name("CAM", "cam")`），按 spec §7.5 设 `sensor_width` / `sensor_fit` / `lens` / `shift_x` / `shift_y` / `clip_start` / `clip_end`；`GUIDE_` 里加 9:16 线框（一个 empty 或 mesh，`hide_render=True`）
  4. `light`：调 `render_preset.apply(scene, project_root)`，再把返回的 `passes_effective` 记入 `warnings`（不丢弃）；加两个 `VIEW_` 层 `VL_beauty` / `VL_char`（`VL_char` 排除 `ENV_` collection）；加一个占位灯（名字 `utils.make_object_name("LGT", "key")`）
  5. `lookdev`：加转台 empty + 相机 parent 上去、3 个灰球（`GEO_grayball_rough0.2/0.5/0.9`）、ColorChecker 24 色卡（1 个 mesh，`GEO_colorchecker`）。**HDRI 只留 World 槽位并加 `warnings` 标注"HDRI 未安装"**，不伪造纯色环境
  6. `scene.frame_start/end/current` ← `spec.SPEC["frame"]` 的 `first` / `end` / `valid_start`
  7. `bpy.ops.wm.save_as_mainfile(filepath=...)` → 记入 `written`
- 返回 `{"ok": True, "written": [...], "skipped": [...], "warnings": [...]}`
- `main(argv)`：`--project-root`、`--apply`、`--overwrite`；成功 `0` / 失败 `1`

- [ ] **Step 5: 生成模板（先 dry-run，再实跑）**

Run: `cd /mnt/data/dsv/ppsk && blender -b --factory-startup --python 00_project/pipeline/build_templates.py -- --project-root .`
Expected: 打印将要写入的 6 个文件名，退出 0，`00_project/templates/` 仍为空

Run: `cd /mnt/data/dsv/ppsk && blender -b --factory-startup --python 00_project/pipeline/build_templates.py -- --project-root . --apply`
Expected: 退出 0，`00_project/templates/` 下出现 6 个 `.blend`

- [ ] **Step 6: 运行往返测试确认通过**

Run: `cd /mnt/data/dsv/ppsk/00_project/pipeline && blender -b --factory-startup --python tests/test_blend_roundtrip.py 2>&1 | tail -25; echo "exit=${PIPESTATUS[0]}"`
Expected: 全部 OK，退出 0

- [ ] **Step 7: 验证覆盖保护与 dry-run 都不写盘（Review Focus #1 #5）**

Run: `cd /mnt/data/dsv/ppsk && before=$(stat -c %Y 00_project/templates/tpl_anim_v001.blend) && blender -b --factory-startup --python 00_project/pipeline/build_templates.py -- --project-root . --apply >/dev/null 2>&1 && after=$(stat -c %Y 00_project/templates/tpl_anim_v001.blend) && [ "$before" = "$after" ] && echo "SKIP_OK: mtime unchanged"`
Expected: 输出 `SKIP_OK: mtime unchanged`

- [ ] **Step 8: 确认 .blend 未被 Git 跟踪**

Run: `cd /mnt/data/dsv/ppsk && git check-ignore -v 00_project/templates/tpl_light_v001.blend || echo "警告：.blend 未被 .gitignore 忽略，需按 plan §18 补规则"`
Expected: 打印命中的 ignore 规则；若是"警告"，把 `*.blend` 加入 `.gitignore`（plan §15：`.blend` 不进 Git）后再继续

- [ ] **Step 9: 提交**

```bash
git add 00_project/pipeline/build_templates.py 00_project/pipeline/utils.py 00_project/pipeline/tests/test_blend_roundtrip.py
git commit -m "feat(templates)：生成 6 个环节模板 .blend + 往返测试

utils.make_object_name 保留 dls.md 的大写前缀，与 normalize_name 划清边界。"
```

---

### Task 6: 文档定稿与变更记录

**Files:**
- Modify: `00_project/bible/project_bible.md`
- Modify: `00_project/bible/scope_lock.md`
- Modify: `docs/dls.md`（§3.1 目录树 line 192–199、§6.6 line 692）
- Modify: `docs/plan.md`（8 处，见 spec §8.4）
- Modify: `README.md`

**Interfaces:**
- Consumes: 无（纯文档）
- Produces: 无代码接口

- [ ] **Step 1: 定稿 `project_bible.md`**

按 spec §8.1 的六节结构重写：技术规格（**5.2.0 + build hash `fbe6228777e7` + dev build**、1920×1080、24 fps、180° 快门、公制、1001 起 + 8 帧 handles）、色彩管理四元组（Scene Linear / **AgX** / sRGB / **None** + per-shot `Khronos PBR Neutral` 例外）、EEVEE 约束（probe ≤128/≤16、shadow pool、运动模糊/Vector 互斥且选 Vector）、性能预算（plan §11 全表）、命名规范（原表 + **两处新增**：`tpl_` 前缀一行；"资产 ID 用 `normalize_name`，对象名用 `make_object_name`"一行）、**本机环境记录**（dev build、无 GPU、无 Cycles、磁盘 121 GB < 300 GB）。

Task 3 已插入的规格生成区块**保持原样不动**——它由 `check_spec.py` 管，不手改。

- [ ] **Step 2: 写 `scope_lock.md` 的 CR-001**

在 `scope_lock.md` 末尾追加 spec §8.2 的 `## 6. 变更记录` + `### CR-001`（含"未承担的风险：5.2.1 仍是最新 patch…升到 5.2.1 需另开 CR"、"决策人：待签"）。同时把「渲染器」行的 `Blender 5.2.1 LTS` 改为 `Blender 5.2.0 LTS（build fbe6228777e7，dev build）`。

在 `## 5. 签署` 之前加一句现状声明：**本文件签署栏为空，签署前不构成生效基准**。

- [ ] **Step 3: 改 `docs/dls.md` 两处**

§3.1 目录树：在 `05_assets/` 下加一行 `│   ├── fx/              # 可发布 FX 预设（与 chr/env/prp/veh/lib 平级）`，**不加** `wip/publish`。§6.6（line 692）：`05_assets/lib/fx/` → `05_assets/fx/`，并补一句划分规则「`fx/` 放可发布 FX 预设；`lib/` 放节点组与 GN 生成器」。

- [ ] **Step 4: 改 `docs/plan.md` 八处**

按 spec §8.4 表格逐条执行。特别注意：
- 附录 C line 1073 的外部事实「5.2.1 已于 2026-08-25 发布」**保留**，只把结论"→ 必须锁 patch"改为"→ 本项目锁 5.2.0，理由见 CR-001"
- §2.2 line 97 / §5.0 T2 line 197 / §7.1 line 362 / §19.1 line 856 四处 **Cycles 就地加标注**："本机引擎枚举仅 `BLENDER_EEVEE`，该降级路径未验证，需在渲染机复核"
- §22.1 修正两处失实勾选：管线 API 骨架实为全 TODO 空壳；镜头目录骨架 `seq040/sh020/` 不存在
- §22.3 把本计划完成的项目打勾

- [ ] **Step 5: 改 `README.md`**

line 3 / 9 / 44 版本号改 5.2.0；落地清单按 §22.3 更新勾选；新增一句：「规格以 `00_project/pipeline/spec.py` 为机器可读来源，改规格改它再跑 `python3 00_project/pipeline/check_spec.py --project-root . --sync --apply`」。

- [ ] **Step 6: 验证 Bible 区块仍然一致（文档改动没碰坏 Task 3 的成果）**

Run: `cd /mnt/data/dsv/ppsk && python3 00_project/pipeline/check_spec.py --project-root .`
Expected: 退出 0

- [ ] **Step 7: 验证没有残留的 5.2.1 锁定表述（CR-001 语境除外）**

Run: `cd /mnt/data/dsv/ppsk && grep -rn "5\.2\.1" README.md 00_project/bible/ docs/ | grep -v "CR-001\|5.2.1 仍是最新 patch\|5.2.1 LTS 于\|已于 2026-08-25"`
Expected: 无输出

- [ ] **Step 8: 确认 scaffold 对真实工程仍幂等（文档改动没影响目录树）**

Run: `cd /mnt/data/dsv/ppsk && python3 00_project/pipeline/scaffold.py --project-root . --apply && python3 00_project/pipeline/scaffold.py --project-root . --apply`
Expected: 第二次 `created` 为空

- [ ] **Step 9: 跑全部测试收尾**

Run: `cd 00_project/pipeline && python3 -m unittest discover -s tests -t . -v 2>&1 | tail -5 && blender -b --factory-startup --python tests/test_render_preset.py 2>&1 | tail -3 && blender -b --factory-startup --python tests/test_blend_roundtrip.py 2>&1 | tail -3`
Expected: 三套全绿

- [ ] **Step 10: 提交**

```bash
git add 00_project/bible/project_bible.md 00_project/bible/scope_lock.md docs/dls.md docs/plan.md README.md
git commit -m "docs：Bible 定稿 + CR-001 + dls/plan/README 同步

锁定版本改 5.2.0（CR-001，dev build）。Cycles 降级路径就地标注本机未验证。
plan §22.1 两处失实勾选已修正。"
```

---

## 完成定义

六个任务全部提交后，本段（plan.md §22.3）达成：

- 6 个 `.blend` 存在于 `00_project/templates/`，**重开后**规格逐项断言通过
- `scaffold.py` 幂等、只增不删、dry-run 零写入
- `check_spec.py` 能抓出真实的 spec 漂移（Task 3 的 `TestSelfTamper` 是这个能力的证明）
- `motion_blur_shutter == 0.5` 在每个模板中成立
- 5 份文档落地，`CR-001` 写入且标注待签署
- G0 报告、镜头表 Schema 冲突、资产与管线 API 属**后续段落**，本计划不碰
