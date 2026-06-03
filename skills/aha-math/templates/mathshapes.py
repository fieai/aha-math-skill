"""mathshapes.py —— 数形结合可复用组件（把视觉模型的画法规则固化进代码）。

配合 mathviz 用：scene 同目录放本文件 + mathviz.py，然后
    from mathshapes import proportional_bars, comparison_diff, part_whole, \
        number_line, mark_point, balance_scale, area_partition

设计目标：把 references/visual-models.md 里的硬规则做成「构造即合规」——
  - 线段图：左端对齐 + 长度严格成比例（调用者无法画错）
  - 分段：用分隔线/相邻色块，不留空隙
  - 未知量：用 ? + 花括号
所有函数返回 manim Mobject（VGroup），可直接 self.play(...)。
"""
from manim import *
from mathviz import C_MAIN, C_WARM, C_OK, C_ACCENT, C_SUB, C_PURP, C_GREY, ZH

_PAL = [C_MAIN, C_WARM, C_OK, C_SUB, C_PURP, C_ACCENT]


def unit_scale(values, max_width=9.0):
    """由一组数值算出「每单位对应多少 manim 宽度」，使最大值占 max_width。"""
    m = max((abs(float(v)) for v in values), default=1.0) or 1.0
    return max_width / m


# ---------- 线段图：比较模型（两条独立、左对齐、成比例）----------

def proportional_bars(values, labels=None, colors=None, left_x=-5.0,
                      top_y=1.3, gap=0.95, height=0.55, u=None):
    """左端对齐 + 长度成比例的一组横条（comparison 模型）。
    返回 VGroup；附带属性 .bars(各条 rect)、.u、.left_x，供 comparison_diff 用。"""
    if u is None:
        u = unit_scale(values)
    pal = colors or _PAL
    bars, items = [], []
    for i, v in enumerate(values):
        w = max(0.02, abs(float(v)) * u)
        y = top_y - i * gap
        bar = RoundedRectangle(width=w, height=height, corner_radius=0.08, stroke_width=0)
        bar.set_fill(pal[i % len(pal)], 1.0).move_to([left_x + w / 2, y, 0])
        grp = VGroup(bar)
        if labels and i < len(labels) and labels[i] is not None:
            lab = Text(str(labels[i]), font=ZH).scale(0.4).set_color(BLACK)
            lab.move_to(bar.get_left()).shift(RIGHT * 0.45)
            grp.add(lab)
        bars.append(bar)
        items.append(grp)
    g = VGroup(*items)
    g.bars, g.u, g.left_x, g.height = bars, u, left_x, height
    return g


def comparison_diff(bars_group, i=0, j=1, color=C_ACCENT, label="差"):
    """标出第 i、j 条右端的长度差：双箭头 + 文字（comparison 模型的「差」）。"""
    bi, bj = bars_group.bars[i], bars_group.bars[j]
    xi, xj = bi.get_right()[0], bj.get_right()[0]
    lo, hi = sorted([xi, xj])
    if hi - lo < 0.06:                      # 两条等长，无差可标
        return VGroup()
    y = min(bi.get_bottom()[1], bj.get_bottom()[1]) - 0.3
    arrow = DoubleArrow([lo, y, 0], [hi, y, 0], buff=0, color=color,
                        stroke_width=4, tip_length=0.18)
    lab = Text(label, font=ZH).scale(0.5).set_color(color).next_to(arrow, DOWN, buff=0.12)
    return VGroup(arrow, lab)


# ---------- 线段图：整体部分模型 ----------

def part_whole(whole, parts, part_labels=None, whole_label=None, unknown_whole=False,
               left_x=-5.0, top_y=1.0, gap=0.95, height=0.55, u=None):
    """上「整体」条 + 下等长、分段（相邻色块，不留空隙）的「部分」条。
    unknown_whole=True 时整体条用 花括号 + ? 表示。"""
    if u is None:
        u = unit_scale([whole])
    W = float(whole) * u
    y_top, y_bot = top_y, top_y - gap
    g = VGroup()

    # 整体条
    if unknown_whole:
        brace = Brace(Line([left_x, y_top, 0], [left_x + W, y_top, 0]), UP, buff=0.08)
        q = Text("?", font=ZH).scale(0.55).set_color(C_ACCENT).next_to(brace, UP, buff=0.05)
        g.add(brace, q)
    else:
        top = RoundedRectangle(width=W, height=height, corner_radius=0.08, stroke_width=0)
        top.set_fill(C_ACCENT, 1.0).move_to([left_x + W / 2, y_top, 0])
        g.add(top)
        if whole_label is not None:
            g.add(Text(str(whole_label), font=ZH).scale(0.4).set_color(BLACK).move_to(top))

    # 部分条：相邻色块拼成一条（无空隙），等长于整体
    x = left_x
    for k, p in enumerate(parts):
        w = float(p) * u
        seg = Rectangle(width=w, height=height, stroke_width=1.5).set_stroke(WHITE, 1.5)
        seg.set_fill(_PAL[k % len(_PAL)], 1.0).move_to([x + w / 2, y_bot, 0])
        g.add(seg)
        if part_labels and k < len(part_labels) and part_labels[k] is not None:
            g.add(Text(str(part_labels[k]), font=ZH).scale(0.36).set_color(BLACK)
                  .move_to([x + w / 2, y_bot, 0]))
        x += w
    return g


# ---------- 数轴 ----------

def number_line(x_min=-5, x_max=5, y=0.0, length=10.0, step=1, numbers=True):
    # label_constructor=Text 避免 LaTeX（本 skill 默认无 LaTeX 环境）
    nl = NumberLine(x_range=[x_min, x_max, step], length=length,
                    include_numbers=numbers, label_constructor=Text, font_size=22)
    nl.move_to([0, y, 0])
    return nl


def mark_point(nl, value, color=C_ACCENT, label=None, show_distance=False):
    """在数轴上标一个点；show_distance=True 时画出到原点的距离（绝对值）。"""
    p = nl.number_to_point(value)
    dot = Dot(p, color=color, radius=0.09)
    g = VGroup(dot)
    if label is not None:
        g.add(Text(str(label), font=ZH).scale(0.4).set_color(color).next_to(dot, UP, buff=0.12))
    if show_distance:
        o = nl.number_to_point(0)
        seg = Line(o, p).set_stroke(color, 5)
        g.add(seg)
    return g


# ---------- 天平 ----------

def balance_scale(left_label="", right_label="", tilt=0.0, span=5.0):
    """示意天平：横梁 + 两托盘 + 支点三角。tilt 为横梁倾角(弧度)，演示失衡/平衡。"""
    beam = Line(LEFT * span / 2, RIGHT * span / 2).set_stroke(C_GREY, 7)
    pivot = Triangle().scale(0.45).set_fill(C_GREY, 1).set_stroke(width=0)
    pivot.next_to(beam, DOWN, buff=0).shift(UP * 0.05)
    lpan = Line(LEFT * 0.7, RIGHT * 0.7).set_stroke(C_MAIN, 6).move_to(beam.get_left())
    rpan = Line(LEFT * 0.7, RIGHT * 0.7).set_stroke(C_WARM, 6).move_to(beam.get_right())
    g = VGroup(beam, lpan, rpan)
    if left_label:
        g.add(Text(str(left_label), font=ZH).scale(0.5).set_color(C_MAIN).next_to(lpan, UP, buff=0.15))
    if right_label:
        g.add(Text(str(right_label), font=ZH).scale(0.5).set_color(C_WARM).next_to(rpan, UP, buff=0.15))
    if tilt:
        g.rotate(tilt, about_point=beam.get_center())
    return VGroup(pivot, g)


# ---------- 面积模型 ----------

def area_partition(heights, widths, h_labels=None, w_labels=None,
                   origin=None, scale=0.6, fill_opacity=0.55):
    """把 (Σheights) × (Σwidths) 的大长方形切成网格小块（分配律/完全平方/平方差）。
    每块用不同色，边长可标注。返回 VGroup。"""
    if origin is None:
        origin = LEFT * 2.5 + DOWN * 1.5
    cells = VGroup()
    y = 0.0
    for r, h in enumerate(heights):
        x = 0.0
        for c, w in enumerate(widths):
            cw, ch = float(w) * scale, float(h) * scale
            rect = Rectangle(width=cw, height=ch, stroke_width=1.5).set_stroke(WHITE, 1.5)
            rect.set_fill(_PAL[(r + c) % len(_PAL)], fill_opacity)
            rect.move_to(origin + RIGHT * (x + cw / 2) + UP * (y + ch / 2))
            cells.add(rect)
            x += cw
        y += h * scale
    # 边长标注
    if w_labels:
        x = 0.0
        for c, w in enumerate(widths):
            cw = float(w) * scale
            if c < len(w_labels) and w_labels[c] is not None:
                cells.add(Text(str(w_labels[c]), font=ZH).scale(0.4).set_color(C_GREY)
                          .move_to(origin + RIGHT * (x + cw / 2) + DOWN * 0.3))
            x += cw
    if h_labels:
        y = 0.0
        for r, h in enumerate(heights):
            ch = float(h) * scale
            if r < len(h_labels) and h_labels[r] is not None:
                cells.add(Text(str(h_labels[r]), font=ZH).scale(0.4).set_color(C_GREY)
                          .move_to(origin + LEFT * 0.3 + UP * (y + ch / 2)))
            y += h * scale
    return cells
