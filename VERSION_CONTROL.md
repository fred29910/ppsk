# 版本控制与备份

## 按数据类型分开管理

| 数据 | 工具 |
|---|---|
| 管线代码、配置、元数据、Project Bible | Git |
| .blend、贴图等大型二进制文件 | SVN / Perforce / Unity Version Control；Git LFS 只适合小规模 |
| 渲染帧、缓存 | 不进版本控制，按目录版本号管理，并纳入备份 |

## 备份原则

遵循 3-2-1 备份原则：

- 3 份副本
- 2 种介质
- 1 份异地

**整个项目期间都要备份，不是等到最后才做。**

## Git 配置

- 管线代码纳入 Git
- 使用 `.gitignore` 排除缓存、渲染帧、大型二进制
- 使用 `.gitkeep` 保留空目录结构

## 二进制文件管理

- .blend 无法合并，不适合 Git LFS 作为主存储
- 大规模项目建议使用 SVN / Perforce / Unity Version Control
- 文件锁定体验比 Git LFS 更好
