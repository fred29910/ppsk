可以。**如果你的目标不是“做一个 Blender 小动画”，而是做一部几十分钟甚至电影级的大型 3D 动画**，那么思路应该从“建模 → 动画 → 渲染”升级成一套完整的 **3D Animation Production Pipeline**。

下面我按接近动画电影/游戏 CG 项目的方式，从 **创意 → 剧本 → 分镜 → 资产 → 场景 → 角色 → 动画 → 特效 → 灯光 → 渲染 → 合成 → 音频 → 最终交付** 全流程讲。

---

# 一、先建立完整的生产管线

大型 Blender 项目大致是：

```text
                    ┌──────────────┐
                    │   创意 / IP   │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │    剧本       │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │ Storyboard   │
                    │   分镜        │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │   Animatic   │
                    │ 动态分镜      │
                    └──────┬───────┘
                           ↓
          ┌────────────────┼────────────────┐
          ↓                ↓                ↓
      角色资产           场景资产          道具资产
          ↓                ↓                ↓
      建模/雕刻         建模/程序化         建模
          ↓                ↓                ↓
      Retopo             UV               UV
          ↓                ↓                ↓
      Texture          Texture          Texture
          ↓                ↓                ↓
          └────────────────┼────────────────┘
                           ↓
                    ┌──────────────┐
                    │ Layout       │
                    │ 镜头布局      │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │   Rigging    │
                    │   绑定        │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │   Animation  │
                    │   动画        │
                    └──────┬───────┘
                           ↓
              ┌────────────┼────────────┐
              ↓            ↓            ↓
            FX           Hair          Cloth
            特效          毛发           布料
              └────────────┼────────────┘
                           ↓
                    ┌──────────────┐
                    │ Lighting     │
                    │   灯光        │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │   Rendering  │
                    │   渲染        │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │ Compositing  │
                    │   合成        │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │   Editing    │
                    │   剪辑        │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │ Sound / Music│
                    │   音频        │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │ Final Master │
                    └──────────────┘
```

**Blender 可以覆盖其中绝大多数环节，但大型项目通常不会只依赖 Blender。**

---

# 二、第一阶段：项目规划

大型项目最容易犯的错误是：

> 打开 Blender → 建一个角色 → 开始做动画。

这是非常容易失控的。

应该首先建立：

```text
Project
├── Story
├── Characters
├── Environments
├── Props
├── Shots
├── Animation
├── FX
├── Lighting
├── Rendering
├── Compositing
├── Audio
└── Delivery
```

例如：

```text
MyMovie/
├── 00_project/
├── 01_story/
├── 02_storyboard/
├── 03_assets/
│   ├── characters/
│   ├── environments/
│   ├── props/
│   ├── vehicles/
│   └── creatures/
├── 04_shots/
│   ├── seq010/
│   │   ├── sh010/
│   │   ├── sh020/
│   │   └── sh030/
│   ├── seq020/
│   └── seq030/
├── 05_animation/
├── 06_fx/
├── 07_lighting/
├── 08_render/
├── 09_comp/
├── 10_edit/
├── 11_audio/
└── 12_delivery/
```

---

# 三、第二阶段：剧本

先确定：

```text
故事
 ↓
人物
 ↓
冲突
 ↓
场景
 ↓
镜头
 ↓
时间线
```

例如一个 10 分钟动画：

```text
SEQ010
城市

SEQ020
主角家

SEQ030
街道

SEQ040
追逐

SEQ050
战斗

SEQ060
结尾
```

每个 Sequence 再拆成 Shot：

```text
SEQ040
├── SH010
├── SH020
├── SH030
├── SH040
├── SH050
└── SH060
```

真正生产时，**Shot 才是最重要的管理单位**。

例如：

```text
SH040

Frame:
1001 - 1120

Characters:
Hero
Enemy

Environment:
City_Street_A

Props:
Car_01
StreetLamp
TrashCan

FX:
Smoke
Dust

Camera:
CAM_SH040

Lighting:
Night_Rain
```

---

# 四、第三阶段：Storyboard

Storyboard 不需要一开始就精细。

甚至可以使用：

* 手绘
* Krita
* Photoshop
* Blender Grease Pencil
* AI 草图
* 简单 3D 方块

核心是确定：

```text
镜头角度
镜头运动
人物位置
人物动作
剪辑节奏
```

例如：

```text
SH010

┌─────────────────────────────┐
│                             │
│        城市远景              │
│                             │
│              ●              │
│             主角             │
│                             │
└─────────────────────────────┘

Camera:
Wide Shot

Duration:
4 sec
```

---

# 五、第四阶段：Animatic

这是大型动画非常关键的一步。

不要直接做最终动画。

而是先：

```text
Storyboard
     ↓
Animatic
```

Animatic 可以非常粗糙：

```text
Cube = 人
Cube = 房子
Plane = 地面
Camera = 摄像机
```

但是已经包含：

```text
镜头
+
动作
+
剪辑
+
时间
+
声音
```

例如：

```text
SH010  0:00 - 0:04
SH020  0:04 - 0:07
SH030  0:07 - 0:12
SH040  0:12 - 0:16
```

这时候就可以发现：

> “这个场景其实很无聊。”

而不用花 3 天建模之后才发现。

---

# 六、第五阶段：Asset Production

接下来才开始大量制作资产。

大型项目通常建立 Asset Library：

```text
Assets
│
├── Characters
│   ├── Hero
│   ├── Heroine
│   ├── Enemy
│   └── NPC
│
├── Environment
│   ├── City
│   ├── Forest
│   ├── House
│   └── Laboratory
│
├── Props
│   ├── Weapon
│   ├── Vehicle
│   ├── Furniture
│   └── Electronics
│
└── FX
    ├── Fire
    ├── Smoke
    ├── Explosion
    └── Magic
```

---

# 七、角色制作完整流程

一个电影级角色一般是：

```text
Concept
 ↓
Sculpt
 ↓
Retopology
 ↓
UV
 ↓
Texture
 ↓
Shader
 ↓
Rig
 ↓
Weight
 ↓
Facial Rig
 ↓
Animation
```

---

## 1. Concept

确定：

```text
正面
侧面
背面
表情
服装
颜色
比例
```

---

## 2. Sculpt

Blender Sculpt Mode：

```text
Base Mesh
 ↓
Sculpt
 ↓
High Poly
```

制作：

* 肌肉
* 脸
* 手
* 衣服
* 皱褶
* 细节

---

# 八、Retopology

雕刻模型通常不能直接用于动画。

需要：

```text
High Poly
     ↓
Retopology
     ↓
Animation Mesh
```

例如：

```text
Sculpt Mesh

10,000,000 polygons

↓

Animation Mesh

50,000 polygons
```

这里要特别关注：

### 面部

```text
眼睛
鼻子
嘴
脸颊
眉毛
```

### 肩膀

```text
Shoulder
     ↓
Arm
```

### 肘

```text
Upper Arm
    \
     O
    /
Forearm
```

### 膝盖

```text
Thigh
  |
  O
  |
Shin
```

这些地方决定后面动画变形质量。

---

# 九、UV

角色通常需要：

```text
Body
Face
Clothes
Shoes
Accessories
```

UV：

```text
3D Model
    ↓
UV Unwrap
    ↓
Texture Space
```

大型项目建议：

```text
UDIM

1001
1002
1003
1004
...
```

而不是把整个角色压缩到一张 2K Texture。

---

# 十、材质

Blender 使用：

**Shader Editor + Principled BSDF**

典型角色：

```text
Base Color
Roughness
Metallic
Normal
Displacement
Subsurface
Emission
```

例如皮肤：

```text
Base Color
      ↓
Subsurface
      ↓
Roughness
      ↓
Normal
```

---

# 十一、Rigging

这是动画生产的核心。

角色：

```text
Mesh
 +
Armature
 +
Controls
```

形成：

```text
Character Rig
```

例如：

```text
Root
 └── Pelvis
      ├── Spine
      │    ├── Chest
      │    │    ├── Neck
      │    │    │    └── Head
      │    │    ├── Arm.L
      │    │    └── Arm.R
      │    └── ...
      │
      ├── Leg.L
      └── Leg.R
```

然后建立：

```text
IK
FK
Pole
Constraints
Drivers
Custom Properties
```

---

# 十二、Face Rig

电影级动画不能只做身体。

需要：

```text
Face
├── Eyes
├── Eyebrows
├── Mouth
├── Jaw
├── Tongue
└── Facial Muscles
```

常见方式：

### Shape Keys

```text
Smile
Frown
Blink
OpenMouth
Angry
Sad
Surprised
```

进一步可以建立：

```text
Facial Controller
        ↓
Shape Keys
```

最终动画师控制：

```text
眉毛
眼睛
嘴
脸颊
下巴
```

---

# 十三、Environment 环境制作

大型场景千万不要：

> 一个 Blender 文件把整座城市全部建完。

应该采用：

```text
City
│
├── Block A
├── Block B
├── Block C
├── Street A
├── Street B
└── Building Library
```

然后使用：

* Collection
* Asset Browser
* Linked Data
* Geometry Nodes
* Procedural Generation
* Library Overrides

组合。

---

# 十四、程序化建模

大型项目非常适合 Geometry Nodes。

例如城市：

```text
Road Generator
       ↓
Building Generator
       ↓
Window Generator
       ↓
Street Light Generator
       ↓
Tree Generator
       ↓
Traffic Generator
```

最终：

```text
City Generator
```

可以通过几个参数生成整个区域。

---

# 十五、植被

森林千万不要手工复制：

```text
Tree × 10000
```

而应该：

```text
Tree Collection
       ↓
Geometry Nodes
       ↓
Scatter
       ↓
Density
       ↓
Random Scale
       ↓
Random Rotation
```

最终生成：

```text
10,000 trees
```

但是实际上可能只有：

```text
20~50 个原始资产
```

---

# 十六、Layout

资产完成以后进入：

**Layout**

也就是：

```text
人物
+
场景
+
摄像机
+
道具
```

全部放到镜头里。

例如：

```text
SH010.blend

Camera
Hero
Enemy
Street
Car
Lamp
```

重点不是精细，而是：

```text
构图
镜头
位置
比例
Blocking
```

---

# 十七、Animation

动画建议分层。

### Blocking

```text
Pose A
   ↓
Pose B
   ↓
Pose C
```

先确定关键姿势。

---

### Spline

再调整：

```text
Timing
Spacing
Arcs
Overlap
Follow Through
```

---

### Polish

最后：

```text
手指
眼睛
呼吸
衣服
头发
微表情
```

大型动画通常不是：

```text
一次性做完
```

而是：

```text
Blocking
 ↓
Spline
 ↓
Polish
 ↓
Final
```

---

# 十八、Camera

电影感很大程度来自摄影机。

需要控制：

```text
Focal Length
Sensor
Depth of Field
Focus
Camera Movement
Motion Blur
```

常见：

```text
24mm
35mm
50mm
85mm
135mm
```

例如：

```text
24mm
↓
环境感强

85mm
↓
人物肖像感
```

---

# 十九、动画缓存

大型项目不能让所有东西实时计算。

例如：

```text
Character Animation
       ↓
Cache

Cloth
       ↓
Cache

Hair
       ↓
Cache

Simulation
       ↓
Cache
```

这样最终镜头不会因为每次打开 Blender 都重新计算全部模拟。

---

# 二十、布料

Cloth Simulation：

```text
Character
    ↓
Cloth
    ↓
Collision
    ↓
Simulation
    ↓
Cache
```

例如：

```text
裙子
衣服
披风
床单
旗帜
```

---

# 二十一、头发

大型项目需要区分：

```text
Hero Hair
Background Hair
```

近景：

```text
真实 Hair Curves
```

远景：

```text
Cards
Curves
Simplified Hair
```

否则几百个角色一起出现时会非常重。

---

# 二十二、粒子与特效

Blender 可以处理：

```text
Smoke
Fire
Explosion
Dust
Rain
Snow
Debris
Magic
Water
```

尤其是：

**Mantaflow**

可以制作：

```text
Fire
Smoke
Liquid
```

大型项目通常也会把 FX 单独管理：

```text
FX/
├── Smoke
├── Fire
├── Explosion
├── Rain
└── Destruction
```

---

# 二十三、灯光

灯光阶段：

```text
Environment
      ↓
Key Light
      ↓
Fill Light
      ↓
Rim Light
      ↓
Practical Light
      ↓
Atmosphere
```

例如夜晚城市：

```text
Moon
+
Street Lights
+
Window Lights
+
Car Lights
+
Volumetric Fog
```

---

# 二十四、Rendering

Blender 主要使用：

### Cycles

适合：

```text
电影级
真实感
复杂光照
```

### Eevee

适合：

```text
实时预览
快速动画
风格化
实时项目
```

大型项目通常不会：

> 直接输出最终 MP4。

而是：

```text
Blender
 ↓
Render
 ↓
EXR
 ↓
Compositing
 ↓
Editing
 ↓
Movie
```

---

# 二十五、Render Pass

大型项目一定要考虑 Pass。

例如：

```text
Beauty
Diffuse
Specular
Emission
Volume
Shadow
Depth
Normal
Cryptomatte
Motion Vector
```

这样后期可以单独调整：

```text
角色
背景
灯光
反射
阴影
雾
```

不用重新渲染整个镜头。

---

# 二十六、EXR

电影级工作流建议：

```text
OpenEXR
32-bit
Linear
```

而不是：

```text
直接 PNG
```

例如：

```text
SH010/
├── 1001.exr
├── 1002.exr
├── 1003.exr
└── ...
```

---

# 二十七、Compositing

进入 Blender Compositor 或专业合成软件。

典型：

```text
Render
 ↓
Color Correction
 ↓
Depth
 ↓
Fog
 ↓
Bloom
 ↓
Glare
 ↓
Lens
 ↓
Color Grade
 ↓
Final
```

还可以使用：

* Nuke
* Fusion
* DaVinci Resolve

进行更专业的合成。

---

# 二十八、Editing

所有 Shot 最终进入：

```text
Timeline
```

例如：

```text
SEQ010

SH010 ───────┐
             │
SH020 ───────┤
             │
SH030 ───────┤
             │
SH040 ───────┘
```

然后调整：

```text
Cut
Timing
Transition
Pacing
```

---

# 二十九、声音

声音实际上非常重要：

```text
Dialogue
SFX
Foley
Ambience
Music
```

最终：

```text
Video
+
Audio
 ↓
Master
```

---

# 三十、大型项目最关键的 Shot Pipeline

真正进入生产以后，一个镜头应该类似：

```text
                    SH010
                      │
        ┌─────────────┼─────────────┐
        ↓             ↓             ↓
     Layout         Assets        Camera
        │             │             │
        └─────────────┼─────────────┘
                      ↓
                   Animation
                      ↓
             ┌────────┼────────┐
             ↓        ↓        ↓
           Cloth     Hair      FX
             └────────┼────────┘
                      ↓
                   Lighting
                      ↓
                    Render
                      ↓
                  Compositing
                      ↓
                    Review
                      ↓
                   Revision
                      ↓
                    Final
```

这才是大型动画真正的核心循环。

---

# 三十一、Review / Revision

专业项目不会：

```text
做完 → 完成
```

而是：

```text
Artist
 ↓
Render
 ↓
Review
 ↓
Notes
 ↓
Revision
 ↓
Render
 ↓
Review
```

例如：

```text
V001
V002
V003
V004
FINAL
```

---

# 三十二、版本控制

大型 Blender 项目强烈建议：

```text
Git
+
Git LFS
```

或者使用：

* Perforce
* Plastic SCM
* SVN

但是注意：

**Git 不适合直接管理海量 `.blend` 二进制文件。**

可以考虑：

```text
Git
 ↓
Scripts
Config
Metadata
Pipeline
```

大型资产则：

```text
Asset Storage
```

单独管理。

---

# 三十三、Blender 文件结构

非常重要。

不要：

```text
movie.blend
```

全部塞进去。

应该：

```text
assets/
    characters/
        hero/
            hero_model.blend
            hero_rig.blend
            hero_material.blend

    environments/
        city/
            city_master.blend

shots/
    seq010/
        sh010/
            sh010_layout.blend
            sh010_anim.blend
            sh010_fx.blend
            sh010_light.blend
```

---

# 三十四、Linked Asset

例如 Hero：

```text
hero_rig.blend
```

Shot：

```text
SH010
SH020
SH030
SH040
```

全部 Link：

```text
             Hero Asset
                 │
       ┌─────────┼─────────┐
       ↓         ↓         ↓
     SH010     SH020     SH030
```

修改 Hero：

```text
hero_rig.blend
```

所有 Shot 都可以同步。

这对于大型项目非常重要。

---

# 三十五、Library Override

但是 Shot 又需要修改角色：

```text
Hero
 ↓
Library Override
 ↓
Shot-specific animation
```

这样：

```text
Asset
│
├── Model
├── Rig
└── Material

Shot
│
└── Animation Override
```

资产和镜头解耦。

---

# 三十六、Asset Browser

建议建立自己的 Asset Browser：

```text
Characters
Environment
Props
Vehicles
FX
Materials
HDRI
Sounds
```

以后制作新镜头：

```text
打开 Asset Browser
       ↓
拖入 Hero
       ↓
拖入 City
       ↓
拖入 Car
       ↓
拖入 Lamp
```

就可以快速搭建镜头。

---

# 三十七、大型项目必须解决的性能问题

例如：

```text
100 个角色
+
1000 个建筑
+
10000 棵树
+
大量 FX
```

直接全部加载：

```text
RAM 爆炸
Viewport 爆炸
Render 爆炸
```

所以需要：

### LOD

```text
Hero

LOD0
LOD1
LOD2
LOD3
```

---

### Visibility

远处：

```text
Hide
```

---

### Proxy

Viewport：

```text
Low Poly Proxy
```

Render：

```text
High Quality Asset
```

---

### Instancing

例如：

```text
Tree × 10000
```

实际上：

```text
Tree Asset × Instance
```

---

# 三十八、大型场景推荐架构

可以采用：

```text
                    PROJECT
                       │
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
      ASSETS         SEQUENCES       LIBRARY
        │              │
        │              ├── SEQ010
        │              │     ├── SH010
        │              │     ├── SH020
        │              │     └── SH030
        │              │
        │              └── SEQ020
        │
        ├── Characters
        ├── Environment
        ├── Props
        ├── Vehicles
        └── FX
```

---

# 三十九、推荐的 Blender 技术栈

如果你准备真正做大型项目，我建议把 Blender 当作核心 DCC：

| 工作             | 工具                           |
| -------------- | ---------------------------- |
| 建模             | Blender                      |
| Sculpt         | Blender                      |
| UV             | Blender                      |
| Texture        | Blender / Substance 3D       |
| Rig            | Blender                      |
| Animation      | Blender                      |
| FX             | Blender                      |
| Hair           | Blender                      |
| Environment    | Blender                      |
| Geometry Nodes | Blender                      |
| Lighting       | Blender                      |
| Rendering      | Cycles                       |
| Compositing    | Blender / Nuke / Fusion      |
| Editing        | DaVinci Resolve              |
| Audio          | DaVinci Resolve / 专业 DAW     |
| Asset 管理       | Blender Asset Browser + 项目管理 |
| 自动化            | Python                       |
| 版本控制           | Git / Perforce               |
| Render Farm    | Flamenco / Deadline 等        |

---

# 四十、如果你想“纯 Blender”

如果你希望：

> **尽量全部使用 Blender，不依赖 Maya、Houdini、Substance、Nuke。**

也是可以的。

可以形成：

```text
                 Blender
                    │
       ┌────────────┼────────────┐
       ↓            ↓            ↓
     Modeling     Sculpt       UV
       ↓            ↓            ↓
    Texture       Material      Rig
       └────────────┼────────────┘
                    ↓
                 Layout
                    ↓
                Animation
                    ↓
          ┌─────────┼─────────┐
          ↓         ↓         ↓
        Cloth      Hair       FX
          └─────────┼─────────┘
                    ↓
                 Lighting
                    ↓
                  Cycles
                    ↓
               Compositor
                    ↓
               Video Editing
                    ↓
                 Audio
                    ↓
                 Final
```

**Blender 本身已经足够完成一整部 3D 动画。**

真正限制大型项目的往往不是“Blender 缺少某个功能”，而是：

> **资产管理、文件组织、版本控制、缓存、渲染调度和团队协作。**

---

# 四十一、如果是你一个人制作

如果你准备做 **Solo 3D Animation Studio**，我建议不要按照传统电影公司的方式把所有环节完全人工化。

应该建立：

```text
                 Blender
                    │
                    ↓
              Python Pipeline
                    │
        ┌───────────┼───────────┐
        ↓           ↓           ↓
      Assets       Shots       Render
        │           │           │
        ↓           ↓           ↓
    Asset DB     Shot DB     Render Farm
        │           │           │
        └───────────┼───────────┘
                    ↓
                 Review
                    ↓
                  Final
```

尤其可以大量使用 Python：

```python
create_asset()
publish_asset()
load_asset()
create_shot()
setup_camera()
setup_render()
submit_render()
collect_render()
create_preview()
```

甚至可以做到：

```text
创建 Shot
   ↓
自动创建 Blender 文件
   ↓
自动加载角色
   ↓
自动加载环境
   ↓
自动设置 Camera
   ↓
自动设置 Render
   ↓
自动输出 EXR
```

---

# 四十二、你之前提到的 Blender MCP，在这里就非常有价值

如果把你前面研究的 **Blender MCP + DeepSeek Harness / Codex / OpenCode** 接进来，可以进一步变成：

```text
                 AI Agent
                    │
             DeepSeek Harness
                    │
             Coding Agent
                    │
              Blender MCP
                    │
                 Blender
                    │
        ┌───────────┼───────────┐
        ↓           ↓           ↓
     Modeling    Animation      FX
        ↓           ↓           ↓
        └───────────┼───────────┘
                    ↓
                 Render
```

例如你可以让 Agent 执行：

```text
“创建一个 1920×1080 的镜头。”

“创建一条 500 米城市街道。”

“放置 20 栋建筑。”

“生成夜晚灯光。”

“创建雨水效果。”

“把角色 Hero 放在街道中央。”

“创建摄像机运动。”

“设置 24fps。”

“渲染 1001-1120。”

“检查渲染结果。”
```

而 Blender Python 负责真正执行。

---

# 四十三、我建议你最终建立这样的架构

如果你的目标是**大型 3D 动画 + AI 自动化**，我会建议最终架构：

```text
                         ┌───────────────┐
                         │   Story/LLM   │
                         └───────┬───────┘
                                 ↓
                         ┌───────────────┐
                         │ Project DB    │
                         └───────┬───────┘
                                 ↓
                ┌────────────────┴────────────────┐
                ↓                                 ↓
        ┌───────────────┐                 ┌───────────────┐
        │ Asset Pipeline│                 │ Shot Pipeline │
        └───────┬───────┘                 └───────┬───────┘
                ↓                                 ↓
        ┌───────────────┐                 ┌───────────────┐
        │ Blender Python│                 │ Blender Python│
        └───────┬───────┘                 └───────┬───────┘
                └────────────────┬────────────────┘
                                 ↓
                         ┌───────────────┐
                         │ Blender MCP   │
                         └───────┬───────┘
                                 ↓
                         ┌───────────────┐
                         │    Blender    │
                         └───────┬───────┘
                                 ↓
                         ┌───────────────┐
                         │ Render System │
                         └───────┬───────┘
                                 ↓
                         ┌───────────────┐
                         │ EXR / Review  │
                         └───────┬───────┘
                                 ↓
                         ┌───────────────┐
                         │   Compositing │
                         └───────┬───────┘
                                 ↓
                         ┌───────────────┐
                         │ Editing/Audio │
                         └───────┬───────┘
                                 ↓
                            FINAL MOVIE
```

**这套思路非常适合你现在正在研究的 Blender MCP + DeepSeek Harness + Coding Agent。**

如果你是准备真正做一个**大型 3D 动画项目**，下一步最值得做的不是马上学某个建模工具，而是先建立一个 **“Blender 大型动画项目模板”**：包括 `Project/Sequence/Shot/Asset` 四级目录、Blender 文件拆分、Asset Browser、Linked Asset、Library Override、Python Pipeline、Geometry Nodes、角色 Rig、渲染配置和 Flamenco Render Farm。这样以后你做任何动画，都可以直接从模板开始。
