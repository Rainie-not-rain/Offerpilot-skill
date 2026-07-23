# 输入格式与离线渲染

## Markdown 数据结构

`resume.md` 使用 YAML front matter + Markdown 分节：

```yaml
---
name: 姓名
phone: 电话
email: 邮箱
location: 城市
intent: 求职意向
intent_detail: 每周5天 · 连续3个月
summary: 自我评价
photo: ./avatar.jpg
---
```

身份证号、银行卡号和详细家庭住址等敏感字段默认忽略，不进入 front matter 或正文。

正文使用：

```markdown
## 教育背景
### 学校 · 专业 · 学历 | 2024.09 – 2027.06
- 补充信息

## 项目经历
### 项目名称 · 角色 | 时间
- **工作方向** 项目背景、动作、方法和结果
```

CSV/xlsx 使用“分类、字段名、值”三列，通过：

```bash
python scripts/csv_to_md.py input.xlsx -o resume.md
```

旧 `.xls` 先转为 `.xlsx` 或 CSV。转换结果只是内部骨架，必须经过完整性、事实和 JD 定向检查。

## 四套 PDF 模板

| 模板 | 用途 |
| --- | --- |
| `compact` | 紧凑单栏，中文校招和技术岗 |
| `classic` | 黑白、ATS 稳定、海投 |
| `modern` | 侧栏式，互联网、产品和运营 |
| `timeline` | 时间线，经历密集或强调成长 |

四套均支持可选头像。预设色为 `blue / teal / wine / ink / purple / green / orange`，也支持 `#rrggbb`。未指定颜色时沿用对应案例的默认色；指定颜色时，四套模板（包括 `classic`）都会相应替换大标题、模块标题、分隔线、时间轴、项目符号或强调底色。

### 案例与模板映射

当用户说“生成某个模板”“使用某个版本”或同义表达时，先读取对应案例，再调用同名模板：

| 用户选择 | 版式权威案例 | 生成模板 |
| --- | --- | --- |
| `compact` | `examples/简历案例/修改后-compact版.docx` | `assets/templates/compact/` |
| `classic` | `examples/简历案例/修改后-classic版.docx` | `assets/templates/classic/` |
| `modern` | `examples/简历案例/修改后-modern版.docx` | `assets/templates/modern/` |
| `timeline` | `examples/简历案例/修改后-timeline版.docx` | `assets/templates/timeline/` |

执行要求：

1. 案例决定默认页面结构、页边距、栏宽、字体层级、分隔线、项目符号、头像位置、视觉密度和默认颜色。
2. 用户内容决定所有正文事实，不得把案例中的个人信息、学校、公司、项目或成果迁移到新简历。
3. 用户明确提出配色时，通过 `--accent` 覆盖案例默认色，并将该颜色用于大标题、模块标题、分隔线、时间轴、项目符号或强调底色；不得同时改变结构和字号。头像或排版变化同样以用户要求覆盖案例默认值；未指定时沿用案例默认样式。
4. 生成后必须检查页面数量、溢出、错位、乱码和信息缺失；一页目标不得以删除教育经历或虚构内容为代价。

```bash
python scripts/render_pdf.py resume.md --template compact --accent teal
```

未指定 `--out` 时，最终 PDF 保存到 Skill 安装目录下的 `output`。模板、CSS、图片和字体回退均为本地资源，不加载 CDN、远程字体或在线网站。优先 WeasyPrint；缺少原生库时回退到本机 Chrome/Edge 无头打印。PDF 正文必须可搜索、选择和复制。

## 资产结构

```text
assets/
  resume-base.css
  resume.example.md
  resume.example.csv
  templates/
    compact/
    classic/
    modern/
    timeline/
```

## 验收

- A4 页尺寸，中文不乱码。
- 姓名、联系方式、日期和照片不重叠。
- 一页/两页自然分页，经历条目不被异常截断。
- 移除照片后无空白占位。
- 自定义色只影响装饰层级，不降低正文对比度。
- PDF 可搜索、复制，不将整页转为图片。
