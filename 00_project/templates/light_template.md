# 灯光模板说明

## 灯光层次

按层叠加（不是串联）：

1. 环境光：HDRI / 天空
2. 主光（Key）
3. 辅光（Fill）
4. 轮廓光（Rim）
5. 场景光源（Practical）
6. 大气：雾 / 体积

## 灯光模板

同一场戏的所有镜头共享一套灯光，只做局部微调：

- Night_Rain
- Day_Sunny
- Indoor_Office

## 使用方式

1. Link 灯光模板
2. 按镜头微调补光
3. 使用 Light Linking 给角色单独补光

## 检查清单

- [ ] 色彩脚本已对照
- [ ] 灯光模板已加载
- [ ] Light Linking 已设置
- [ ] 渲染设置已预置
