> ⚠️ **本仓库已归档（read-only）。** aha-math 已迁入 monorepo **[fieai/lifekit](https://github.com/fieai/lifekit)**（`plugins/aha-math`）。
> 安装：`/plugin marketplace add fieai/lifekit` → `/plugin install aha-math@lifekit`。后续更新只在 lifekit 进行。

<div align="center">

# aha-math

**一个把数学题/概念做成“看得懂为什么”讲解视频的 skill**

[中文](#中文) · [English](#english)

</div>

---

## 中文

一个为 Claude Code、Codex 等 Agent Skill 环境设计的数学讲解 skill。给它一道应用题、一个概念或一条公式，它先做**教学诊断**，再写 **storyboard**，最后用 [Manim](https://www.manim.community/) 渲染出一段讲解视频（可选再配一个交互网页）。

它不是“把动画做得炫一点”。

它是把一整套**教学编排**写下来：先找出观众最容易误解的那一步，把抽象规则降维成具体动作，每个关键镜头都得回答“凭什么”，然后才允许写代码、才允许渲染。怎么把一个概念讲清楚，模型本身会；什么时候该停下来确认逻辑、哪一步不能跳、哪一镜是多余的——才是 skill 要替模型想清楚的部分。

### 能做什么

- **讲解视频**：从概念/应用题/证明出发，输出一段顺着画面就能看懂的 Manim 视频
- **教学诊断**：先定位“最容易误解的一步”，对低龄题做实物动作 → 儿童语言 → 口头规则 → 数学语言的四层降维
- **Storyboard 优先**：用户要求“先看逻辑/分镜再做”时，只交付 storyboard，通过后再渲染
- **交互网页**（可选）：用户要网页或未指定形式时，产出可操作的交互 demo
- **无 LaTeX 兜底**：环境没有 LaTeX 时自动改用 `Text` + Unicode，不用 `MathTex/Tex`
- **交付前验证**：字形方框检查、静帧/布局检查、MP4 存在且大小大于 0

### 三个设计判断

不是花哨功能。每一条都是为了避开一类真实的失败模式。

1. **先教学诊断，后写代码。**
   任何应用题、概念题都必须先找出“最容易误解的一步”，再决定怎么画。低龄受众禁止直接上抽象规则——顺序必须是具体动作 → 儿童语言 → 口头规则 → 数学语言。不让模型一上来就堆动画。

2. **每个关键镜头必须回答“凭什么”。**
   不能从“减数减少 15”直接跳到“差 +15”。关键结论不是直接出现，而是被可见的动作推出来——遮住旁白，只看画面也能看出关键变化。同时不过度拆镜：讲同一个关系的连续两镜要合并。

3. **用户要看逻辑就别偷偷渲染。**
   用户说“通过了再做视频”，skill 就停在 storyboard，不往下渲染。渲染前必须有 storyboard；对用户已质疑过的逻辑，必须先给 storyboard 让用户确认。

### 安装

**推荐：通过 xman marketplace 一键安装（Claude Code）**

```
/plugin marketplace add fieai/xman
/plugin install aha-math@xman
```

**或者直接软链 skill（任何 Agent Skill 宿主）**

skill 本体在 `skills/aha-math/` 子目录下。

Claude Code 用户级：

```bash
git clone https://github.com/fieai/aha-math-skill.git
ln -s "$(pwd)/aha-math-skill/skills/aha-math" ~/.claude/skills/aha-math
```

Claude Code 项目级：

```bash
ln -s /path/to/aha-math-skill/skills/aha-math /path/to/your-project/.claude/skills/aha-math
```

Codex 等其他 Agent Skill 宿主：按各自约定把 `skills/aha-math/` 软链或复制到对应的 skill 目录。

> **依赖：** 视频渲染需要 Python + Manim（可选 LaTeX）。skill 自带 `scripts/setup_manim.sh` 在 `~/.cache/aha-math-venv` 建虚拟环境；`scripts/check_env.py` 做环境探测。没有 LaTeX 也能跑，公式自动退化为 `Text`。

### 触发场景

skill metadata 里声明的触发条件：

- 用户要把某道数学/物理题或概念做成视频、动画讲解
- 用户要 storyboard / 分镜 / 可视化教学脚本
- 用户要一个 Manim 场景或交互数学 demo
- 用户说“给二年级小朋友讲讲这道题”“这个概念怎么动画演示”“先给我看下逻辑”

### 文件结构

```
aha-math-skill/
├── .claude-plugin/
│   └── plugin.json                     Claude Code plugin manifest
├── skills/
│   └── aha-math/
│       ├── SKILL.md                    主入口：硬规则 + 工作流 A→E
│       ├── references/
│       │   ├── pedagogy-and-storyboard.md  教学分镜方法
│       │   ├── visual-models.md            数形结合视觉模型库（题型→选模型→画法→可见逻辑）
│       │   ├── word-problem-patterns.md    应用题视觉模型与低龄解释模板
│       │   ├── video-orchestration.md      镜头必要性、终态布局先行、校验规则
│       │   ├── manim-guide.md              Manim API、布局、防重叠、无 LaTeX 写法
│       │   ├── manim-cookbook.md           可复用 Manim 片段
│       │   └── interactive-web-guide.md    交互网页
│       ├── templates/
│       │   ├── storyboard.md               结构化分镜模板（散文版）
│       │   ├── storyboard.schema.json      强类型分镜契约（abstractionLevel 顺序约束）
│       │   ├── storyboard.example.json      填好的强类型分镜正例（差变化题，具体先行）
│       │   ├── scene_template.py           Manim 场景骨架
│       │   ├── mathviz.py                  SafeScene 与布局检查
│       │   ├── mathshapes.py               数形结合可复用组件（线段图/天平/数轴/面积）
│       │   ├── interactive_template.html   交互网页模板
│       │   └── example_pythagoras_proof.py 勾股定理证明示例
│       └── scripts/
│           ├── setup_manim.sh / check_env.py   环境安装与探测
│           ├── render.sh                        渲染（静帧 / 草稿 / 成片）
│           ├── check_storyboard.py              分镜检查（强类型 json + md，判定不跳步骤）
│           ├── check_text.py                    字体字形检查
│           └── check_web.py                     交互网页检查
├── LICENSE                             MIT
└── README.md
```

### 一个示例

输入：

> 给二年级小朋友讲讲：减数减少 15，差会怎么变？

skill 走的流程：

1. **判定形式与受众**：从语义判定（视频 / 网页 / both / 仅 storyboard）+ 受众降到“二年级、实物动作、儿童话术”
2. **教学降维**：定位误解点（“以为减少 15 会让答案少 15”）→ 具体动作（原来拿走 75 颗糖，现在少拿 15 颗）→ 儿童语言（这 15 颗还留在桌上）→ 口头规则（少减多少就多剩多少）→ 数学翻译（减数减少 15，差增加 15）
3. **写 storyboard**：每镜头写清目标、画面、旁白、动画、必须避免的跳跃；低龄题跑 `check_storyboard.py`。用户说“通过了再做”就停在这里
4. **渲染**：复制 `mathviz.py`，按 storyboard 写 `scene.py`，先做终态布局再加动画；字形检查 → 静帧检查 → 成片
5. **交付**：视频/网页路径、storyboard 路径、用到的默认值、验证结果（布局、字形、MP4 参数）

关键结论始终被动作推出，不直接蹦出来。

### 局限

- **依赖 Manim 渲染**：视频形态需要本机能装 Python + Manim；环境探测失败会停下来说明，不硬撑。
- **无 LaTeX 时退化**：没有 LaTeX 会自动用 `Text` + Unicode，复杂公式排版会受限。
- **不替代教学设计判断**：skill 把“何时停、何时确认、哪一镜多余”写成流程，但具体题目的教学取舍仍需人确认 storyboard。
- **默认中文语境**：字体、旁白话术按中文受众组织（如 `font="PingFang SC"`），其他语言可用但非最优。

### License

[MIT](./LICENSE)

---

## English

A math-explanation skill for Agent Skill environments (Claude Code, Codex, and others). Hand it a word problem, a concept, or a formula, and it first runs a **teaching diagnosis**, then writes a **storyboard**, then renders an explainer video with [Manim](https://www.manim.community/) (optionally plus an interactive web demo).

It's not "make the animation flashier."

It's a written-down **teaching workflow**: find the single step the audience is most likely to misread, reduce abstract rules down to concrete actions, make every key shot answer "why is this true," and only *then* allow code and rendering. Models can already explain a concept. What this skill writes down is when to stop and confirm the logic, which step must not be skipped, and which shot is redundant.

### What it does

- **Explainer videos**: from a concept / word problem / proof to a Manim video you can follow purely by watching
- **Teaching diagnosis**: locate the "most-misread step" first; for young audiences, a four-layer reduction — concrete action → kid language → spoken rule → math notation
- **Storyboard first**: when the user wants to "see the logic before rendering," deliver only the storyboard and render after approval
- **Interactive web demo** (optional): when the user asks for a web page or leaves the format open
- **No-LaTeX fallback**: when LaTeX is unavailable, switch to `Text` + Unicode instead of `MathTex/Tex`
- **Pre-delivery verification**: glyph-box check, still-frame/layout check, MP4 exists and is non-empty

### Three design calls

Not features. Each exists to avoid a specific class of failure.

1. **Diagnose teaching before writing code.**
   Any word problem or concept must first surface its "most-misread step" before deciding what to draw. For young audiences, never jump straight to abstract rules — the order must be concrete action → kid language → spoken rule → math notation.

2. **Every key shot must answer "why."**
   You may not jump from "the subtrahend drops by 15" straight to "the difference goes +15." Key conclusions are *pushed out by visible actions*, not stated — cover the narration and the change should still be readable from the frames alone. And don't over-split shots: two consecutive shots about the same relationship get merged.

3. **If the user wants the logic, don't render behind their back.**
   When the user says "render only after I approve," the skill stops at the storyboard. A storyboard is required before any render; for logic the user has already questioned, a storyboard must be confirmed first.

### Install

**Recommended: install via the xman marketplace (Claude Code)**

```
/plugin marketplace add fieai/xman
/plugin install aha-math@xman
```

**Or symlink the skill directly (any Agent Skill host)**

The skill itself lives in `skills/aha-math/`.

Claude Code (user-level):

```bash
git clone https://github.com/fieai/aha-math-skill.git
ln -s "$(pwd)/aha-math-skill/skills/aha-math" ~/.claude/skills/aha-math
```

Claude Code (project-level):

```bash
ln -s /path/to/aha-math-skill/skills/aha-math /path/to/your-project/.claude/skills/aha-math
```

Codex and other Agent Skill hosts: symlink or copy `skills/aha-math/` into your host's skill directory.

> **Dependencies:** rendering needs Python + Manim (LaTeX optional). The skill ships `scripts/setup_manim.sh` to build a venv at `~/.cache/aha-math-venv`, and `scripts/check_env.py` to probe the environment. It runs without LaTeX — formulas degrade to `Text` automatically.

### When it triggers

Declared in the skill metadata:

- Turning a math/physics problem or concept into a video or animated explanation
- Requests for a storyboard / shot list / visual teaching script
- A Manim scene or an interactive math demo
- Phrases like "explain this to a 2nd grader," "how would you animate this concept," "show me the logic first"

### File layout

```
aha-math-skill/
├── .claude-plugin/
│   └── plugin.json                     Claude Code plugin manifest
├── skills/
│   └── aha-math/
│       ├── SKILL.md                    main entry: hard rules + workflow A→E
│       ├── references/
│       │   ├── pedagogy-and-storyboard.md  storyboarding methodology
│       │   ├── visual-models.md            number-shape model library (type→model→drawing→visible logic)
│       │   ├── word-problem-patterns.md    visual models + young-audience templates
│       │   ├── video-orchestration.md      shot necessity, final-layout-first, checks
│       │   ├── manim-guide.md              Manim API, layout, anti-overlap, no-LaTeX
│       │   ├── manim-cookbook.md           reusable Manim snippets
│       │   └── interactive-web-guide.md    interactive web
│       ├── templates/
│       │   ├── storyboard.md               structured storyboard template (prose)
│       │   ├── storyboard.schema.json      strongly-typed storyboard contract (abstractionLevel ordering)
│       │   ├── storyboard.example.json      filled strongly-typed exemplar (diff problem, concrete-first)
│       │   ├── scene_template.py           Manim scene skeleton
│       │   ├── mathviz.py                  SafeScene + layout checks
│       │   ├── mathshapes.py               reusable number-shape components (bar/balance/number-line/area)
│       │   ├── interactive_template.html   interactive web template
│       │   └── example_pythagoras_proof.py worked Pythagoras proof
│       └── scripts/
│           ├── setup_manim.sh / check_env.py   env install & probe
│           ├── render.sh                        render (still / draft / final)
│           ├── check_storyboard.py              storyboard check (typed json + md; enforces no step-skipping)
│           ├── check_text.py                    glyph/font check
│           └── check_web.py                     interactive web check
├── LICENSE                             MIT
└── README.md
```

### One example

Input:

> Explain to a 2nd grader: if the subtrahend drops by 15, what happens to the difference?

The skill's flow:

1. **Format & audience**: inferred from the request (video / web / both / storyboard-only) + audience pinned to "2nd grade, concrete actions, kid language"
2. **Teaching reduction**: locate the misconception ("thinks dropping by 15 makes the answer 15 less") → concrete action (used to take 75 candies, now takes 15 fewer) → kid language (those 15 stay on the table) → spoken rule (the less you subtract, the more is left) → math (subtrahend −15 ⇒ difference +15)
3. **Storyboard**: each shot spells out goal, frame, narration, animation, and the jump to avoid; young-audience problems run `check_storyboard.py`. If the user said "render only after approval," it stops here
4. **Render**: copy `mathviz.py`, write `scene.py` from the storyboard, build the final layout before adding animation; glyph check → still check → final cut
5. **Delivery**: video/web path, storyboard path, defaults used, verification results (layout, glyphs, MP4 params)

Key conclusions are always pushed out by an action, never popped onto screen.

### Limitations

- **Depends on Manim**: the video form needs Python + Manim installable locally; if the env probe fails the skill stops and explains rather than faking it.
- **Degrades without LaTeX**: no LaTeX means `Text` + Unicode, so complex formula typesetting is limited.
- **Doesn't replace teaching judgment**: the skill encodes *when to stop, when to confirm, which shot is redundant*, but per-problem pedagogical trade-offs still want a human to confirm the storyboard.
- **Chinese-context defaults**: fonts and narration phrasing are organised for a Chinese audience (e.g. `font="PingFang SC"`); other languages work but aren't optimised.

### License

[MIT](./LICENSE)
