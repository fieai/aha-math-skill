#!/usr/bin/env python3
"""Lightweight storyboard pedagogy checker.

It is intentionally heuristic: it catches missing teaching scaffolds before the
agent jumps into rendering.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


REQUIRED_SECTIONS = [
    "教学诊断",
    "观众可能误解",
    "具体动作解释",
    "儿童语言",
    "口头规则",
    "数学翻译",
    "通过标准",
]

LOW_AGE_MARKERS = ["二年级", "低年级", "小朋友", "孩子", "儿童"]
CONCRETE_MARKERS = [
    "糖",
    "积木",
    "桌上",
    "拿走",
    "留下",
    "篮子",
    "数轴",
    "天平",
    "距离",
    "线段",
    "小数字",
    "小数",
    "代入",
    "卡片",
]
MATH_ONLY_JUMPS = [
    "减数减少 15，所以差增加 15",
    "减数减少15，所以差增加15",
    "减数减少 15，差增加 15",
    "减数减少15，差增加15",
]


def fail(msg: str) -> None:
    print(f"[FAIL] {msg}")


def warn(msg: str) -> None:
    print(f"[WARN] {msg}")


def ok(msg: str) -> None:
    print(f"[ ok ] {msg}")


def main() -> int:
    if len(sys.argv) != 2:
        print("用法: check_storyboard.py <storyboard.md>")
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        fail(f"文件不存在: {path}")
        return 2

    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    warnings: list[str] = []

    for section in REQUIRED_SECTIONS:
        if section not in text:
            errors.append(f"缺少必要项: {section}")

    is_low_age = any(marker in text for marker in LOW_AGE_MARKERS)
    has_concrete = any(marker in text for marker in CONCRETE_MARKERS)

    if is_low_age and not has_concrete:
        errors.append("低龄受众 storyboard 缺少具体实物/动作模型")

    for jump in MATH_ONLY_JUMPS:
        if jump in text and not re.search(r"少(拿|减).{0,12}(多|留|剩)", text):
            errors.append("存在抽象跳步：减数减少直接跳到差增加，缺少少拿/多剩解释")

    if "必须避免" not in text:
        warnings.append("镜头未写“必须避免”，容易重新引入逻辑跳跃")

    if "镜头必要性" not in text:
        warnings.append("缺少“镜头必要性”，容易把中间过程拆成多余镜头")

    if "是否可合并" not in text:
        warnings.append("缺少“是否可合并”，无法检查连续镜头是否重复")

    if "动画" not in text:
        warnings.append("缺少动画动作描述，可能变成静态讲稿")

    if "旁白" not in text:
        warnings.append("缺少旁白，视频讲解节奏可能不清晰")

    for item in errors:
        fail(item)
    for item in warnings:
        warn(item)

    if errors:
        print(f"[STOP] 共 {len(errors)} 个错误，请修复后再渲染")
        return 1

    ok("storyboard 教学结构检查通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
