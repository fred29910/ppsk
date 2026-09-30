# MyMovie

基于 Blender 5.2 LTS 的大型 3D 动画项目模板，目录结构与命名规范遵循 `docs/dls.md`。

当前实例化项目为**仙侠 Demo**（30 秒 / 5 镜 / 1 场景 / 1 角色），完整开发计划见 [`docs/plan.md`](docs/plan.md)。

## 快速开始

> **模板需先生成。** `.blend` 已进 `.gitignore`（plan §15），所以干净 clone 里
> `00_project/templates/` 下**一个模板都没有**，直接「打开模板」会打开空目录。
>
> ```bash
> blender -b --factory-startup --python 00_project/pipeline/build_templates.py -- \
>     --project-root . --apply
> ```
>
> 已存在的 `.blend` 默认跳过（保护 GUI 里的手工修改），确实要重建才加 `--overwrite`。
> 先 dry-run 看计划：去掉 `--apply`。

1. 生成并用 Blender **5.2.0 LTS** 打开 `00_project/templates/` 下的 6 个模板
   （Layout / Anim / CFX / FX / Light / LookDev）。
2. 核对 `00_project/bible/project_bible.md`（已按 `docs/plan.md` §7.1/§7.2 定稿反向更新）。
3. G0 技术可行性验证**已完成**，报告在 `00_project/bible/g0_feasibility_report.md`（plan §5.0）。
   开工前仍需补的是**色彩全链路验证**（plan §9.1）——「不通过不要进入资产制作」这条仍然有效。
4. 用管线脚本创建第一个镜头（见 `00_project/pipeline/`）。⚠️ `--setup_render`
   **必须**带 `--frame-range`（取自 `00_project/pipeline/shotlist.csv`），
   缺了会直接失败而不是落回模板占位范围。
5. 提交渲染前检查贴图路径、帧范围、输出路径（`docs/plan.md` §11 性能预算 / §7.4 EEVEE 约束）。
6. 规格以 `00_project/pipeline/utils.py` 为唯一机器可读来源。改规格的顺序是：
   先改 `utils.py` → 再改 `00_project/bible/project_bible.md`（测试断言的是它，不是本文件）→
   跑 `cd 00_project/pipeline && python3 -m unittest discover -s tests -t .`。
   收紧验收（必须零命中）：

   ```bash
   grep -rn '1920\|1080\|"24"\|1001\|1136' 00_project/pipeline/*.py | grep -v '^00_project/pipeline/utils.py'
   ```

## 目录说明

| 目录 | 用途 |
|---|---|
| `00_project/` | Project Bible、OCIO、管线脚本、模板 |
| `01_story/` | 剧本、色彩脚本 |
| `02_storyboard/` | 分镜 |
| `03_editorial/` | 剪辑工程、Animatic、EDL / OTIO |
| `04_audio/` | 对白、音效、音乐、混音工程 |
| `05_assets/` | 资产（wip / publish / lib） |
| `06_shots/` | 镜头（layout / anim / cfx / fx / light / comp / cache / render） |
| `07_review/` | 审阅片 |
| `08_delivery/` | 交付物 |
| `09_archive/` | 归档 |

## 落地清单

权威版本见 `docs/plan.md` §22，此处只做索引。

**已有**

- [x] 目录结构
- [x] Project Bible 定稿（分辨率 / 帧率 / 色彩管理四元组 / 快门 / 性能预算，见 plan §7、§11）
- [ ] 管线 API 骨架（`asset` / `shot` / `cache` / `review` / `utils`）— ⚠️ `asset.py` 与 `cache.py` 至今全是 `# TODO` 空壳，仅 `utils.py` / `shot.py` / `review.py` 有实际实现
- [x] 模板文档（layout / render / rig_base / lookdev_scene）

**W0 必做**

- [x] G0 技术可行性验证（plan §5.0）
- [x] 锁定 Blender **5.2.0 LTS** + build hash `fbe6228777e7`
- [ ] 色彩全链路验证（plan §9.1）

**待办**

- [x] 模板 .blend（6 个：Layout / Anim / CFX / FX / Light / LookDev）— ⚠️ `.blend` 在 `.gitignore` 里，需按「快速开始」用 `build_templates.py --apply` 生成，干净 clone 里默认没有
- [x] LookDev 场景 — 灰球 / 色卡 / 转台相机已就位；**HDRI 未安装**（`05_assets/lib/hdri/` 不存在），模板只留 World 槽位不伪造纯色环境。HDRI 属 plan §22.4 / §16 授权登记，待补
- [ ] 角色绑定基础（表情 shape keys，无口型集）
- [ ] 仙侠 FX 资产库（P0 三种）
- [ ] 灯光模板（`Cloud_Day` / `Night_Moon` / `Hall_Mystic`）
- [ ] 竹林 GN 生成器
- [ ] 资产库配置 + 发布脚本
- [ ] 镜头表 / 资产表 + Schema（plan §13）
- [ ] 管线 API 补齐（`audit_shot` / `upgrade_asset` / `get_dependencies` / `collect_render`）
- [ ] 缓存失效矩阵与 seed 固定（plan §10.4）
- [x] 渲染设置预设（EEVEE View Layer / Pass / EXR）
- [ ] 授权登记表 `licensing.csv`（plan §16）
- [ ] 渲染农场（Flamenco 4 节点）
- [ ] 版本控制与备份（3-2-1）
- [ ] 渲染预算表（plan §14）
- [ ] MCP 工具封装

## 规范

- 镜头编号：`seq<三位>_sh<三位>`，如 `seq010_sh010`
- 资产编号：`<类型>_<名称>_<变体>`，如 `chr_hero_default`
- 文件命名：`<镜头或资产>_<环节>_v<三位>.blend`
- 渲染帧：`<镜头>_<环节>_v<三位>.<四位帧号>.exr`
- 版本号只增不减，禁止 `final`、`final2`、`new`。
