---
name: aha-math
description: >-
  Create math explanation videos, Manim animations, and optional interactive
  demos from a user's math/physics concept or word problem. Use when the user
  asks for a math video, animated explanation, storyboard, visual teaching
  script, Manim scene, or interactive math demo. Optimized for teaching clarity:
  diagnose the audience and misconception first, draft a storyboard with concrete
  visual actions, get approval when requested, then render.
metadata:
  category: education
  tags: [math, education, video, manim, storyboard, teaching, animation]
---

# Aha Math

把数学题或概念做成“看得懂为什么”的讲解产物。核心不是炫动画，而是让观众顺着画面自己明白——看到那个 “aha” 的瞬间。

> **路径约定：** 本文中所有 `scripts/`、`templates/`、`references/` 均指本 skill 目录下的对应子目录。
> 作为 Claude Code plugin 安装后即 `${CLAUDE_PLUGIN_ROOT}/skills/aha-math/...`；若以源码软链使用，则相对 skill 根目录。
> 命令请在能解析到该目录的位置运行，或自行替换为 skill 的实际安装路径。

## 硬规则

1. **尊重用户指定形式。** 用户说“视频”就只做视频；说“网页”就只做网页；没指定才默认视频 + 网页。
2. **先确认讲解方案，再渲染（强制）。** 第一步永远先把“打算怎么讲”交给用户确认：**默认给『讲解步骤』人话视图**——先点明**知识点 / 关键词 / 切入点**，再一步步讲，最后口诀+答案；不出现镜头/画面/动画/抽象层级等术语，面向普通家长。强类型分镜（storyboard）作为**内部产物**生成并校验，用户要看才展开。未确认前禁止渲染；仅当用户明确说“跳过确认/直接做”才例外。
3. **先教学诊断，后写代码。** 任何小学题、应用题、概念题都必须先找出“最容易误解的一步”。
4. **低龄受众禁止直接上抽象规则。** 顺序必须是：具体动作 → 儿童语言 → 口头规则 → 数学语言。
5. **每个关键镜头必须回答“凭什么”。** 不能从“减数减少 15”直接跳到“差 +15”。
6. **不要过度拆镜。** 连续两个镜头如果都在讲同一个关系，只保留一个“动作镜头”；例如“减法是一整条”和“两段拼回整条”应合并为“减数 + 差拼回被减数”。
7. **渲染前必须有已确认的 storyboard。** 任何视频/网页都必须基于用户确认过的 storyboard；未经确认不得渲染。
8. **不用 LaTeX 时禁用 `MathTex/Tex`。** 用 `Text(..., font="PingFang SC")` 和 Unicode。
9. **交付前必须验证。** 字形检查、静帧/布局检查、MP4 存在且大小大于 0。

## 工作流

### A. 判定形式和受众

从用户语义中直接判定，不要反复追问：

- 形式：`video` / `web` / `both` / `storyboard-only`
- 受众：小学低年级 / 小学高年级 / 初中 / 高中 / 大学 / 科普
- 目标：解题、概念解释、证明、可视化、交互探索
- 关键误解点：观众最可能在哪一步卡住

如果用户给出年级，比如“二年级小朋友”，必须降到实物动作与儿童话术。

### B0. 教学降维与误解点拆解

写分镜前先做这一层，尤其是应用题：

```text
原题关键步骤：
观众可能误解：
具体动作解释：
儿童语言：
口头规则：
数学翻译：
```

例：减数减少 15

```text
观众可能误解：以为“减少 15”会让答案少 15。
具体动作解释：老师原来拿走 75 颗糖，现在少拿 15 颗，只拿走 60 颗。
儿童语言：这 15 颗没有被拿走，还留在桌上。
口头规则：少减多少，就多剩多少。
数学翻译：减数减少 15，差增加 15。
```

### B. 写 storyboard

**优先写强类型 `storyboard.json`**（按 `templates/storyboard.schema.json`），它能被校验器确定性地拦住"抽象先于具体""跳步骤""相邻镜头重复"。范例见 `templates/storyboard.example.json`。需要给人快速看时，也可用散文版 `templates/storyboard.md`。两种都必须包含：

- 学习目标
- 受众与语言难度
- 核心误解点
- 具体动作解释
- 儿童语言/口头规则/数学语言三层翻译
- 每镜头：目标、画面、旁白、动画、必须避免的跳跃
- 每镜头抽象层级 `abstractionLevel`：concrete → child-language → spoken-rule → math（JSON 版必填，用于顺序校验）
- 镜头必要性：这一镜头是否引入了新信息；能否和前后镜头合并
- 通过标准

**所有 storyboard（json 或 md）渲染前必须运行：**

```bash
python3 scripts/check_storyboard.py <主题>/storyboard.json
```

校验器会强制：math 镜头不得早于任何 concrete 镜头、不得从 concrete 直接跳到 math、相邻镜头不得讲同一 relation、低龄旁白不过长。低龄题尤其不能跳过这一步。

写完 storyboard 后读 `references/video-orchestration.md` 的“镜头必要性检查”和“终态布局先行”，尤其是用户指出“复杂了”“多余了”“跳步骤了”之后。

#### 确认门（强制，不可跳过）

校验通过后，**把“打算怎么讲”交给用户确认，并停在这里等待**。默认面向普通家长，用『讲解步骤』人话视图，**先讲清是什么、再一步步教**；不要展示镜头/画面/动画/抽象层级等术语，也不要只丢一个 JSON 路径：

- **知识点**：这道题考的是什么——一句话说清孩子要掌握的那条关系/规律。
- **关键词**：题目里的核心词（如 被减数、减数、差、和），帮家长对上号。
- **切入点**：破题的钥匙——从哪个发现、哪句话入手（就是最容易误解、一旦想通就全通的那一步）。
- **一步步讲**：3–5 条编号步骤，纯口语、具体动作先行（对应分镜推导主线，但不出现术语）。
- **口诀 + 答案**：一句可被孩子复述的口头规则，再给最终答案。
- 结尾一句：“确认后我就做成视频/网页；想看详细分镜也可以说。”

只有用户主动说“看分镜”时，才展开完整分镜（镜头清单 + 画面/旁白/动作/abstractionLevel）。

规则：

- 明确请用户**确认或提出修改**；用户改了就回到 B 重写并重新校验，再次请确认。
- **在用户明确确认前，禁止进入 C/D、禁止安装环境、禁止渲染任何视频或网页。**
- 唯一例外：用户明确说“跳过确认/直接做”。
- 表单为 `storyboard-only` 时，交付即结束（按用户需要给步骤或分镜）。

讲解步骤视图模板：

```text
这道题打算这么讲（<受众>）

知识点：<这道题考的是什么，一句话>
关键词：<被减数 / 减数 / 差 / 和 …>
切入点：<破题的钥匙，一句话——最易误解、想通就全通的那一步>

怎么一步步讲：
1. <人话步骤，具体动作先行>
2. ...

口诀：<一句顺口规则>
答案：<最终答案>
```

只有拿到确认后，才继续 C/D。

### C. 准备视频环境

> 进入本步前，确认分镜已通过上面的“确认门”。未确认不要装环境、不要渲染。

先检查：

```bash
python3 scripts/check_env.py
```

缺 `manim` 时运行：

```bash
bash scripts/setup_manim.sh
```

若 LaTeX 不可用，所有公式使用 `Text`，不要使用 `MathTex/Tex`。

### D1. 制作 Manim 视频

1. 创建主题目录。
2. 复制 `templates/mathviz.py` 到主题目录。
3. 按 storyboard 写 `scene.py`。
4. 每段内容先 `VGroup(...).arrange()`，再 `fit_content()`。
5. 标题用 `title_bar()`，旁白用 `caption()`，切镜头用 `clear_screen()`。
6. 关键逻辑必须由可见动作表达，不只靠旁白。
7. 先做每个镜头最清楚的终态画面，再加动画；不要从入场位置猜最终布局。
8. 时间轴和停留时间由代码/模板控制，LLM 不要随手堆镜头时长。

字体检查：

```bash
python3 scripts/check_text.py <主题>/scene.py
```

静帧/布局检查：

```bash
bash scripts/render.sh <主题>/scene.py SceneName s
```

若 `render.sh` 在本机异常，可直接使用同一 venv：

```bash
cd <主题>
source "$HOME/.cache/aha-math-venv/bin/activate"
manim -s -qm scene.py SceneName
```

完整渲染：

```bash
bash scripts/render.sh <主题>/scene.py SceneName m
```

fallback：

```bash
cd <主题>
source "$HOME/.cache/aha-math-venv/bin/activate"
manim -qm scene.py SceneName
cp "$(find media/videos -type f -name 'SceneName.mp4' -print0 | xargs -0 ls -t | head -n1)" SceneName.mp4
```

### D2. 制作交互网页

只有用户要求网页或未指定形式时才做。复制 `templates/interactive_template.html` 到 `<主题>/index.html`，并运行：

```bash
python3 scripts/check_web.py <主题>/index.html
```

### E. 交付

交付要简洁说明：

- 视频路径或网页路径
- storyboard 路径
- 使用的默认值：受众、形式、是否无 LaTeX
- 验证结果：布局、字形、MP4 参数

## 低龄数学题讲解模板

低龄题优先选下面的视觉模型：

- 加减法：糖果、积木、贴纸、桌上物品
- 差：剩下多少、距离、两排长度；二年级优先“剩下多少”
- 少减/多减：拿走的篮子、回到桌上的物品
- 倍数：一组一组摆
- 分数：饼、纸条、量杯
- 方程：天平

低龄旁白句式：

```text
先别急着记名字。
你就想：桌上有……
拿走一些，还剩……
这几个没有被拿走，所以还留在这里。
少减多少，就多剩多少。
现在我们把这句话翻译回数学。
```

## 质量门槛

视频必须满足：

- 关键结论不是直接出现，而是被动作推出。
- 遮住旁白，只看画面也能看出关键变化。
- 对低龄受众，先出现实物动作，再出现术语。
- 字幕/文字不出界、不重叠。
- `[layout] DONE 共发现 0 处布局问题`。
- MP4 存在、大小大于 0，并用 `ffprobe` 验证。

## 资源索引

- `references/pedagogy-and-storyboard.md`：教学分镜方法
- `references/word-problem-patterns.md`：应用题视觉模型与低龄解释模板
- `references/video-orchestration.md`：借鉴 HyperFrames 与 fogsight-v5 的视频编排、镜头必要性、布局和校验规则
- `references/manim-guide.md`：Manim API、布局、防重叠、无 LaTeX 写法
- `references/manim-cookbook.md`：可复用 Manim 片段
- `references/interactive-web-guide.md`：交互网页
- `templates/storyboard.md`：结构化分镜模板（散文版）
- `templates/storyboard.schema.json`：强类型分镜契约（JSON Schema，含 abstractionLevel 顺序约束）
- `templates/storyboard.example.json`：填好的强类型分镜正例（差变化题，具体先行）
- `templates/scene_template.py`：Manim 场景骨架
- `templates/mathviz.py`：SafeScene 与布局检查
- `scripts/check_storyboard.py`：教学分镜检查（强类型 json + 旧版 md；判定循序渐进、不跳步骤）
- `scripts/check_text.py`：字体字形检查
- `scripts/check_web.py`：网页检查
- `scripts/setup_manim.sh` / `scripts/check_env.py` / `scripts/render.sh`：环境与渲染
