# MyMovie

基于 Blender 5.2 LTS 的大型 3D 动画项目模板，目录结构与命名规范遵循 `docs/dls.md`。

## 快速开始

1. 用 Blender 5.2 LTS 打开 `00_project/templates/` 下的模板文件。
2. 填写 `00_project/bible/project_bible.md`。
3. 用管线脚本创建第一个镜头（见 `00_project/pipeline/`）。
4. 提交渲染前检查贴图路径、帧范围、输出路径。

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

- [x] 目录结构
- [ ] Project Bible
- [ ] 模板 .blend
- [ ] LookDev 场景
- [ ] 角色绑定基础
- [ ] 资产库配置 + 发布脚本
- [ ] 镜头表 / 资产表
- [ ] 管线 API
- [ ] 渲染设置预设
- [ ] 渲染农场
- [ ] 版本控制与备份
- [ ] 渲染预算表
- [ ] MCP 工具封装

## 规范

- 镜头编号：`seq<三位>_sh<三位>`，如 `seq040_sh020`
- 资产编号：`<类型>_<名称>_<变体>`，如 `chr_hero_default`
- 文件命名：`<镜头或资产>_<环节>_v<三位>.blend`
- 渲染帧：`<镜头>_<环节>_v<三位>.<四位帧号>.exr`
- 版本号只增不减，禁止 `final`、`final2`、`new`。
