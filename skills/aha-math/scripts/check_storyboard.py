#!/usr/bin/env python3
"""Storyboard pedagogy checker —— 教学分镜检查（强类型 JSON + 兼容旧 markdown）。

两种输入：

  1) storyboard.json —— 强类型分镜（推荐）。按 templates/storyboard.schema.json 校验结构，
     再用 abstractionLevel 等结构字段【确定性地】判定『循序渐进、不跳步骤』：
       - math 镜头不能出现在任何 concrete 镜头之前
       - 不能从 concrete 直接跳到 math（中间缺 child-language / spoken-rule）
       - 相邻镜头讲同一 relation → 提示合并
       - 低龄题旁白过长 / 缺关键镜头 / 全片不回到数学语言 → 提示
  2) storyboard.md —— 旧版散文分镜，仍做启发式检查（存在性 + 抽象先于具体 + 跳步措辞）。

退出码：0 通过；1 有错误需修复；2 用法/文件错误。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# ---------- 输出 ----------


def fail(msg: str) -> None:
    print(f"[FAIL] {msg}")


def warn(msg: str) -> None:
    print(f"[WARN] {msg}")


def ok(msg: str) -> None:
    print(f"[ ok ] {msg}")


# ---------- 抽象层级（低→高）----------

ABSTRACTION_ORDER = {"concrete": 0, "child-language": 1, "spoken-rule": 2, "math": 3}
VISUAL_MODELS = {"bar-part-whole", "bar-comparison", "area", "number-line", "coordinate",
                 "balance", "venn", "dissection", "dynamic-point", "counting", "other"}
LOW_AGE = {"小学低年级", "小学高年级"}
STRICT_FAIL_AGE = {"小学低年级", "小学高年级"}
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "templates" / "storyboard.schema.json"


# ========== 强类型 JSON 校验 ==========


def _structural_errors(data: dict) -> list[str]:
    """不依赖第三方库的结构校验；若装了 jsonschema 则改用 schema 文件，覆盖更全。"""
    try:
        import jsonschema  # type: ignore

        if SCHEMA_PATH.exists():
            schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
            v = jsonschema.Draft7Validator(schema)
            return [
                f"结构错误 @ {'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}"
                for e in sorted(v.iter_errors(data), key=lambda e: list(e.path))
            ]
    except ImportError:
        pass

    # —— 内置最小结构校验（无 jsonschema 时）——
    errs: list[str] = []

    def need(obj, keys, where):
        if not isinstance(obj, dict):
            errs.append(f"{where} 应为对象")
            return False
        for k in keys:
            if k not in obj or obj[k] in (None, "", []):
                errs.append(f"{where} 缺少必填字段: {k}")
        return True

    need(data, ["meta", "diagnosis", "scenes", "passCriteria"], "<root>")
    meta = data.get("meta", {})
    if need(meta, ["topic", "form", "audience", "learningGoal", "coreSentence"], "meta"):
        if meta.get("form") not in {"video", "web", "both", "storyboard-only"}:
            errs.append(f"meta.form 非法: {meta.get('form')}")
        if meta.get("audience") not in {"小学低年级", "小学高年级", "初中", "高中", "大学", "科普"}:
            errs.append(f"meta.audience 非法: {meta.get('audience')}")
    need(
        data.get("diagnosis", {}),
        ["problemStep", "misconception", "concreteAction", "childLanguage", "spokenRule", "mathTranslation"],
        "diagnosis",
    )
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        errs.append("scenes 应为非空数组")
        scenes = []
    vm = data.get("visualModel")
    if vm is not None and vm not in VISUAL_MODELS:
        errs.append(f"visualModel 非法: {vm}（见 references/visual-models.md / schema 枚举）")
    for i, sc in enumerate(scenes):
        where = f"scenes[{i}]"
        if not need(sc, ["id", "goal", "abstractionLevel", "necessity", "frame", "narration", "animation", "mustAvoid"], where):
            continue
        if sc.get("abstractionLevel") not in ABSTRACTION_ORDER:
            errs.append(f"{where}.abstractionLevel 非法: {sc.get('abstractionLevel')}")
        if sc.get("necessity") not in {"key", "support", "mergeable"}:
            errs.append(f"{where}.necessity 非法: {sc.get('necessity')}")
        if not re.match(r"^scene_[0-9]+$", str(sc.get("id", ""))):
            errs.append(f"{where}.id 应形如 scene_0: {sc.get('id')}")
    return errs


def check_json(data: dict) -> int:
    errors: list[str] = []
    warnings: list[str] = []

    # 1) 结构
    structural = _structural_errors(data)
    if structural:
        for e in structural:
            fail(e)
        print(f"[STOP] 结构校验未通过（{len(structural)} 处），修复后再跑教学检查")
        return 1

    meta = data["meta"]
    audience = meta["audience"]
    is_low_age = audience in LOW_AGE
    strict = audience in STRICT_FAIL_AGE
    scenes = data["scenes"]
    levels = [ABSTRACTION_ORDER[s["abstractionLevel"]] for s in scenes]

    def add(severity_strict: bool, msg: str) -> None:
        (errors if severity_strict else warnings).append(msg)

    # 2) 具体先于抽象：math 不能出现在任何 concrete 之前
    first_concrete = next((i for i, lv in enumerate(levels) if lv == 0), None)
    first_math = next((i for i, lv in enumerate(levels) if lv == 3), None)
    if first_math is not None and (first_concrete is None or first_math < first_concrete):
        add(strict, f"抽象先于具体：{scenes[first_math]['id']}(math) 出现在任何 concrete 镜头之前，"
                    f"低龄题必须先给看得见的动作")

    # 3) 不跳步骤：不能从 concrete 直接跳到 math（中间缺 child-language/spoken-rule）
    for i in range(1, len(levels)):
        if levels[i - 1] == 0 and levels[i] == 3:
            add(strict, f"跳步骤：{scenes[i-1]['id']}(concrete) 直接到 {scenes[i]['id']}(math)，"
                        f"中间缺 child-language / spoken-rule 过渡")

    # 4) 相邻镜头同一 relation → 提示合并
    for i in range(1, len(scenes)):
        r1, r2 = scenes[i - 1].get("relation"), scenes[i].get("relation")
        if r1 and r2 and r1 == r2 and not scenes[i].get("mergeableWith"):
            warnings.append(f"{scenes[i-1]['id']} 与 {scenes[i]['id']} 讲同一关系『{r1}』，考虑合并")

    # 5) 至少一个关键镜头
    if not any(s["necessity"] == "key" for s in scenes):
        warnings.append("没有任何 necessity=key 的关键镜头，分镜可能全是铺垫")

    # 6) 旁白长度（低龄题宜短）
    limit = 42 if is_low_age else 60
    for s in scenes:
        n = len(s["narration"])
        if n > limit:
            warnings.append(f"{s['id']} 旁白偏长（{n} 字 > {limit}），低龄/讲解节奏建议拆短：{s['narration'][:18]}…")

    # 7) 视频最终应回到数学语言
    if meta["form"] in {"video", "both"} and first_math is None:
        warnings.append("全片没有 math 镜头，结尾可能停在口语，未回到数学表达")

    # 8) mustAvoid 至少要有实质内容（结构已保证非空，这里查是否被敷衍成占位）
    for s in scenes:
        if s["mustAvoid"].strip() in {"无", "略", "-", "—"}:
            warnings.append(f"{s['id']}.mustAvoid 像占位符，请写清不能跳过什么")

    for item in errors:
        fail(item)
    for item in warnings:
        warn(item)

    if errors:
        print(f"[STOP] 共 {len(errors)} 个错误，请修复后再渲染")
        return 1
    ok(f"强类型分镜检查通过：{len(scenes)} 镜，抽象层级 {[s['abstractionLevel'] for s in scenes]}")
    return 0


# ========== 旧版 markdown 启发式校验 ==========

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
    "糖", "积木", "桌上", "拿走", "留下", "篮子", "数轴", "天平",
    "距离", "线段", "小数字", "小数", "代入", "卡片", "走", "退",
]
ABSTRACT_MARKERS = ["数学翻译", "公式", "符号", "=", "差增加", "差减少", "代数"]
# 泛化的『一处变化直接推另一处变化』跳步措辞（不再写死减法那一句）
JUMP_PATTERN = re.compile(
    r"(被?减数|加数|因数|被乘数|乘数|除数|被除数)\s*(增加|减少|变大|变小)\s*\d+"
    r".{0,16}?"
    r"(差|和|积|商|结果)\s*(增加|减少|变大|变小)\s*\d+"
)
CONCRETE_EXPLAIN = re.compile(r"(少|多)(拿|减|走|退|加).{0,12}(多|留|剩|远|近|大|小)|留在桌上|没有被拿走")


def check_markdown(text: str) -> int:
    errors: list[str] = []
    warnings: list[str] = []

    for section in REQUIRED_SECTIONS:
        if section not in text:
            errors.append(f"缺少必要项: {section}")

    is_low_age = any(m in text for m in LOW_AGE_MARKERS)
    has_concrete = any(m in text for m in CONCRETE_MARKERS)
    if is_low_age and not has_concrete:
        errors.append("低龄受众 storyboard 缺少具体实物/动作模型")

    # 泛化的跳步检测：出现『X 增减 → Y 增减』但附近没有具体动作解释
    if JUMP_PATTERN.search(text) and not CONCRETE_EXPLAIN.search(text):
        errors.append("存在抽象跳步：一处量变化直接推另一处量变化，缺少『少拿/多剩/前进后退』等具体动作解释")

    # 抽象先于具体（启发式）：在『镜头清单/推导主线』区域里，抽象标记首次出现早于具体标记
    region = text
    m = re.search(r"(镜头清单|推导主线)", text)
    if m:
        region = text[m.start():]
    first_concrete = min(
        [region.find(x) for x in CONCRETE_MARKERS if region.find(x) >= 0] or [10**9]
    )
    first_abstract = min(
        [region.find(x) for x in ABSTRACT_MARKERS if region.find(x) >= 0] or [10**9]
    )
    if first_abstract < first_concrete and first_abstract < 10**9:
        warnings.append("疑似抽象先于具体：公式/数学翻译在具体动作之前出现，低龄题应先做动作再上符号")

    # 旁白长度（低龄题）
    if is_low_age:
        for line in re.findall(r"旁白[:：]\s*(.+)", text):
            s = line.strip()
            if len(s) > 42:
                warnings.append(f"旁白偏长（{len(s)} 字），低龄题建议拆短：{s[:18]}…")

    for key, msg in [
        ("必须避免", "镜头未写『必须避免』，容易重新引入逻辑跳跃"),
        ("镜头必要性", "缺少『镜头必要性』，容易把中间过程拆成多余镜头"),
        ("是否可合并", "缺少『是否可合并』，无法检查连续镜头是否重复"),
        ("动画", "缺少动画动作描述，可能变成静态讲稿"),
        ("旁白", "缺少旁白，视频讲解节奏可能不清晰"),
    ]:
        if key not in text:
            warnings.append(msg)

    for item in errors:
        fail(item)
    for item in warnings:
        warn(item)

    if errors:
        print(f"[STOP] 共 {len(errors)} 个错误，请修复后再渲染")
        return 1
    ok("storyboard 教学结构检查通过（markdown 启发式；建议改用强类型 storyboard.json）")
    return 0


# ========== 入口 ==========


def main() -> int:
    if len(sys.argv) != 2:
        print("用法: check_storyboard.py <storyboard.json | storyboard.md>")
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        fail(f"文件不存在: {path}")
        return 2

    text = path.read_text(encoding="utf-8")

    is_json = path.suffix.lower() == ".json"
    if not is_json and text.lstrip().startswith("{"):
        is_json = True  # 容错：扩展名不是 .json 但内容是 JSON

    if is_json:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            fail(f"JSON 解析失败: {e}")
            return 1
        return check_json(data)

    return check_markdown(text)


if __name__ == "__main__":
    raise SystemExit(main())
