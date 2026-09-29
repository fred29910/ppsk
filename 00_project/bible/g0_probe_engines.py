"""
G0 引擎探针：确认 Blender 5.2 无界面模式下的渲染引擎可用性

关键发现（2026-09-29）：
  `bpy.types.RenderSettings.engine` 的**静态枚举在 -b 无界面模式下只有
  ['BLENDER_EEVEE']**，即使 Cycles addon 已启用、_cycles 模块可导入。
  用枚举判断"有没有 Cycles"会得到错误结论。

  正确做法：直接赋值 `scene.render.engine = 'CYCLES'`，并检查
  `scene.cycles` 是否出现。

用法：
    blender -b --factory-startup --python g0_probe_engines.py
"""

import bpy

argv = bpy.app.driver_namespace.get("g0argv", [])


def main():
    bh = bpy.app.build_hash
    bh = bh.decode() if isinstance(bh, bytes) else bh
    print(f"Blender: {bpy.app.version_string}  hash={bh}")

    # 1. 静态枚举（会误导人）
    enum = [i.identifier for i in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    print(f"[1] engine 静态枚举 = {enum}")
    print(f"    ⚠️ 此处看不到 CYCLES，但不代表不可用")

    # 2. Cycles addon 状态
    try:
        import addon_utils

        for m in addon_utils.modules():
            if m.__name__ == "cycles":
                print(f"[2] cycles addon: {addon_utils.check('cycles')}")
    except Exception as e:
        print(f"[2] addon 查询失败: {e}")

    # 3. _cycles 二进制模块
    try:
        import _cycles

        print(f"[3] _cycles 可导入，符号数 = {len([s for s in dir(_cycles) if not s.startswith('__')])}")
    except Exception as e:
        print(f"[3] _cycles 导入失败: {e}")

    # 4. 决定性检查：直接赋值
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    try:
        sc.render.engine = "CYCLES"
        ok = sc.render.engine == "CYCLES"
        print(f"[4] 直接赋值 'CYCLES' → {sc.render.engine}  {'✓ 可用' if ok else '✗'}")
        if hasattr(sc, "cycles"):
            c = sc.cycles
            print(f"    sc.cycles 存在: device={c.device} samples={c.samples} denoising={c.use_denoising}")
    except Exception as e:
        print(f"[4] 赋值失败: {type(e).__name__}: {e}")

    # 5. 算力设备
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        types = [i.identifier for i in prefs.bl_rna.properties["compute_device_type"].enum_items]
        print(f"[5] Cycles compute_device_type 可选 = {types or '（空 → 无可用设备）'}")
        print(f"    devices = {[(d.name, d.type) for d in prefs.devices] or '（空）'}")
    except Exception as e:
        print(f"[5] 设备查询失败: {e}")

    # 6. 结论
    cyc_ok = hasattr(bpy.data.scenes[0], "cycles")
    print()
    print(f"结论: Cycles {'可用' if cyc_ok else '不可用'}（判据是 scene.cycles，不是 engine 枚举）")
    print("提示: 资产/灯光文件若要混用 Cycles，不要用枚举做分支判断。")


main()
