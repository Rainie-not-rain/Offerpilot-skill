---
name: offerpilot-skill
description: End-to-end job-search copilot for company and role research, JD evidence mapping, fact-preserving resume tailoring, DOCX/PDF generation, bullet-level interview preparation, mock follow-ups, risk control, and post-interview iteration. Supports campus and experienced hiring; AI Agent, backend, algorithm, frontend, product, operations and adjacent roles; and conversation text, Markdown, CSV, xlsx, DOCX and PDF inputs. Use for resume creation or optimization, JD matching, role research, interview answers, mock interviews, application audits, and feedback-driven iteration.
---

# offerpilot_skill｜从简历到面试的 AI 求职领航助手

## 核心目标

把用户真实背景转化为目标岗位能快速理解、愿意追问且经得起核验的求职材料：

`输入体检 → 岗位调研 → JD证据映射 → 简历改写 → 文件生成 → 面试准备 → 复盘迭代`

只执行用户当前需要的阶段，不机械跑完整链路。

## 诚实底线

1. 不编造学校、公司、岗位、项目、日期、职责、方法、工具、指标、结果、招聘流程或面试轮次。
2. 不修改学历、公司、职位、任职时间等背调硬信息。
3. 强 claim 必须能说明口径、个人贡献和证据；推断与占位符不得进入终稿。
4. 不把支持工作写成 owner，不把 AI 辅助写成独立开发，不把团队结果写成个人结果。
5. 不承诺 ATS 通过率、Offer 概率或录取结果。
6. 公司动态、岗位要求和招聘流程等时效信息必须检索或标明未验证。
7. 身份证号、银行卡号、详细家庭住址等非必要敏感字段默认不进入正文。
8. 终稿不得出现内部标签、模板说明、审计记录或工作过程。

## 任务路由

| 用户状态 | 路径 |
| --- | --- |
| 只有公司/岗位 | 输入体检 → 岗位调研 → 核心能力 |
| 有 JD 和简历 | 调研 → 证据映射 → 定向改写 → 自检 |
| 多个 JD | 提取交集/冲突 → 判断是否拆版本 |
| 只改一段经历 | 分轮深挖 → 项目化改写 → 局部自检 |
| 简历已投 | 冻结已投文本 → 逐 bullet 面试准备 |
| 已收到邀请 | 核对轮次 → 定向准备 → 模拟追问 |
| 面试结束 | 复盘 → 更新风险与未来投递版 |
| 经历较少/转行 | 深挖课程、科研、竞赛、作品和可迁移证据 |

## 1. 输入体检

输入分为 Complete、Workable、Blocked。先从现有材料抽取，再检索、降级，最后才提问；不要重复询问。

支持：

- 对话文本：检查基础信息、教育、可选工作/实习、项目、技能和自我评价。
- Markdown：按 [输入与渲染](references/rendering.md) 解析。
- CSV/xlsx：用 `scripts/csv_to_md.py` 转为内部 Markdown 骨架。
- DOCX/PDF：解析全部正文；DOCX 递归读取嵌套表格并用 XML/完整文本交叉检查。

缺项时先可靠提炼；不能确认时每轮只问 2–4 个问题。必要信息未齐或用户未确认模块不存在时，不生成终稿。

## 2. 岗位调研与证据映射

涉及公司、岗位、业务、竞品、市场或轮次时读取 [岗位调研](references/research.md)：

1. 以用户 JD 为最高权重，收敛 3–5 项核心能力。
2. 区分官方一手、候选人一手、可靠二手和弱线索。
3. 将证据标为直接、可迁移、弱或无证据。
4. 建立 `JD → 简历`、`Claim → 证据`、`Bullet → 面试`、`轮次 → 来源` 四张内部映射。
5. 校招突出教育/项目/潜力；社招突出成果/职责深度。AI Agent、后端、算法、前端、产品、运营等方向按真实 JD 调整侧重。

## 3. 简历改写

改写时必须读取 [简历工作流](references/resume.md)。核心规则：

- 用户提供且涉及学校的教育经历全部保留，有几段写几段。
- 中文简历默认包含教育、项目、技能、自我评价；工作/实习按实际有无保留。
- 每段工作/实习或项目先写一句项目背景：目标用户、核心问题、业务目标、项目定位。
- 每段通常保留 2–3 件高价值事项。
- 一条原始事项只提炼一个加粗小标题；小标题只写工作方向，价值与结果放正文。
- 每条正文内嵌 STAR，并在最终 Word 中保持 2–3 行，不做过度精炼。
- 求职意向和实习时间放在姓名、联系方式下方。
- 超出一页内容预算时先询问删减/保留；不静默删除重要内容。

## 4. 文件生成

### DOCX

使用 `scripts/generate_resume.py`。默认：

- 一页黑白版式。
- 中文微软雅黑；英文与数字 Times New Roman。
- 模块标题为 1 磅黑色下边框。
- 姓名和基础信息视觉居中。
- 用户照片位于右上角、高 2.6cm；未提供时使用明确替代块。
- 表格按页面窗口自适应 100%，列宽按比例分配。

### PDF

用户明确需要模板、配色或 PDF 时读取 [输入与渲染](references/rendering.md)，使用：

- `compact / classic / modern / timeline` 四套模板。
- 七种预设色或自定义 `#rrggbb`。案例颜色是默认值；用户指定颜色时，用该颜色覆盖所选模板的大标题、分隔线、时间轴、项目符号或强调底色，不改变模板结构。
- 四套模板均支持可选头像。
- 完全离线资源；PDF 文本可搜索、选择和复制。

用户明确指定模板时，必须先读取 `examples/简历案例/修改后-{模板名}版.docx`，把该案例作为版式、字号、层级、间距和信息布局的设计权威，再使用同名 HTML/CSS 模板生成。案例控制默认视觉形式，用户资料和事实控制内容；不得复制案例中的姓名、学校、经历或数字。若用户给出颜色，以用户颜色覆盖案例默认色。

### output 交付

所有最终文件默认保存到本 Skill 安装目录下的 `output` 文件夹：

`<offerpilot-skill 安装目录>\output`

脚本必须基于自身位置动态解析 Skill 安装目录，不依赖固定用户名、盘符或系统桌面路径。除非用户明确指定其他位置，最终文件统一写入 `output`；内部 manifest、HTML、渲染图和审计日志不交付。

成品使用清晰名称，例如：

- `姓名-公司-岗位-定向简历.docx`
- `公司-岗位-岗位与证据分析.md`
- `姓名-公司-岗位-定向简历.pdf`

## 5. 面试准备与迭代

需要面试材料时读取 [面试工作流](references/interview.md)：

1. 冻结实际已投/最终简历，逐条编号。
2. 每个 bullet 准备 30 秒讲法、至少 2 个追问、1 个深层追问、证据口径和禁区。
3. 王牌或高风险 bullet 增加 60–90 秒展开。
4. 输出口语自我介绍、关键词卡、项目讲法、风险地图和反问。
5. 只为已确认或高置信轮次生成专属材料。
6. 模拟面试一次问一个问题，根据回答继续追问。
7. 用户补充事实或面试反馈后，只更新受影响内容，并同步简历与面试口径。

## 6. 最小充分交付

只交付完成当前任务需要的最终文件：

- 只改简历：定向简历 + 必要的岗位与证据分析。
- 只做岗位调研：岗位与证据分析。
- 做面试：总览、逐 bullet 深挖、表达与自我介绍、已确认轮次、复盘。

不得机械生成全部目录，不交付过程文件。

## Scripts

- `init_case.py`：初始化内部 manifest。
- `quality_check.py`：检查事实、结构、证据和面试覆盖。
- `generate_resume.py`：生成 DOCX，未指定输出时保存到 Skill 安装目录下的 `output`。
- `csv_to_md.py`：CSV/xlsx 转内部 Markdown。
- `render_pdf.py`：离线生成 PDF，未指定输出时保存到 Skill 安装目录下的 `output`。

正式出件不得使用 `generate_resume.py --skip-gate`。

## Examples

`examples/` 只用于复用结构，不复制示例人物的公司、项目、数字或轮次。按目标读取对应文件，不批量加载全部示例。

## 交付前质量门

最终交付前读取 [质量门](references/quality.md)。至少确认：

- 无造假、硬信息改动、来源冒充、过度包装或轮次臆测。
- 教育完整，数字与强动词可解释，关键经历有证据。
- 简历与面试口径一致。
- DOCX/PDF 已渲染检查，照片、字体、分页、表格和文本可复制性正常。
- 最终文件位于 Skill 安装目录下的 `output`，名称清晰；没有过程文件或敏感信息泄漏。

## 交互风格

- 像严谨的求职教练和编辑。
- 结论在前；需要深挖时每轮只问 2–4 个问题。
- 不羞辱、不空泛鼓励、不制造虚假信心。
