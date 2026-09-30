# MyMovie

基于 Blender 5.2 LTS 的大型 3D 动画项目模板，目录结构与命名规范遵循 `docs/dls.md`。

当前实例化项目为**仙侠 Demo**（30 秒 / 5 镜 / 1 场景 / 1 角色），完整开发计划见 [`docs/plan.md`](docs/plan.md)。

## 快速开始

1. 用 Blender **5.2.1 LTS** 打开 `00_project/templates/` 下的模板文件。
2. 核对 `00_project/bible/project_bible.md`（首次开工前必须按 `docs/plan.md` §7 反向更新）。
3. **先跑 G0 技术可行性验证**（`docs/plan.md` §5.0），不通过不要进入资产制作。
4. 用管线脚本创建第一个镜头（见 `00_project/pipeline/`）。
5. 提交渲染前检查贴图路径、帧范围、输出路径（`docs/plan.md` §11 性能预算 / §7.4 EEVEE 约束）。

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
- [x] Project Bible 初稿（待按 plan §7 更新）
- [x] 管线 API 骨架（`asset` / `shot` / `cache` / `review` / `utils`）
- [x] 模板文档（layout / render / rig_base / lookdev_scene）

**W0 必做**

- [ ] G0 技术可行性验证（plan §5.0）
- [ ] 锁定 Blender 5.2.1 LTS + 记录 build hash
- [ ] 色彩全链路验证（plan §9.1）

**待办**

- [ ] 模板 .blend
- [ ] LookDev 场景
- [ ] 角色绑定基础（表情 shape keys，无口型集）
- [ ] 仙侠 FX 资产库（P0 三种）
- [ ] 灯光模板（`Cloud_Day` / `Night_Moon` / `Hall_Mystic`）
- [ ] 竹林 GN 生成器
- [ ] 资产库配置 + 发布脚本
- [ ] 镜头表 / 资产表 + Schema（plan §13）
- [ ] 管线 API 补齐（`audit_shot` / `upgrade_asset` / `get_dependencies` / `collect_render`）
- [ ] 缓存失效矩阵与 seed 固定（plan §10.4）
- [ ] 渲染设置预设（EEVEE View Layer / Pass / EXR）
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
