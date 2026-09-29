"""把 00_project/pipeline 加入 sys.path，让各测试文件能 import 项目模块。"""
import os
import sys

PIPELINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PIPELINE_DIR not in sys.path:
    sys.path.insert(0, PIPELINE_DIR)
