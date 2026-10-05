# 代码与提示词审核任务书 · v3.1（针对 `cpc github v2`）

> **审核对象：`D:\项目\cpc github v2`**（当前版本，**全部已知问题已修复**）
> 本任务书同时要求审核**代码**与**提示词文档**两部分。
> 你不必相信本文件里的任何数字——第 2 节全部标注了来源，请逐条复核。

---

## 0. 审核对象

| 项 | 值 |
|---|---|
| 本地路径 | `D:\项目\cpc github v2` |
| git | 工作区 clean，**156 个提交**（上游 152 + 3 次重构提交 + 1 次文档提交） |
| 当前 HEAD | **请自行执行 `git rev-parse HEAD` 获取**——本文件不硬编码提交号，因为它自己也在提交历史里 |
| 形态 | **纯代码版**（不含 demo 运行产物） |
| 前一个版本 | `D:\项目\cpc github v1`（首版重构，改动未提交） |
| 带 demo 产物的版本 | `D:\项目\cpc github v1 demo`（已发布到 GitHub） |
| 基线 | 官方 `59df377` |
| 上游仓库 | https://github.com/Seniorious123/CellPainting-Claw |
| 已发布仓库 | https://github.com/liuzy0543-spec/CPC-v1 |

### 取差异

```bash
git log --oneline -5      # 应为 <文档提交> / 3295122 / dd7c182 / 3cc412c / 59df377
git diff 59df377 HEAD --stat             # 相对官方基线
git diff dd7c182 3295122 --stat          # 只看 v2 的代码动作
git diff 59df377 HEAD -- src/ tests/     # 源码全文
```

---

## 1. 交付历史（三轮）

| 轮次 | 产物 | 内容 |
|---|---|---|
| 首版 `3cc412c` | `cpc github v1` | 拆包重构（`skills/` + `cli/` + 4 个新模块） |
| 一轮评审 | — | 找出 8 条问题（F1–F8）+ 5 条提示词缺口 |
| 修复 `dd7c182` | demo 树 | F1–F6 修复（`_impl`/`_native` 收敛、fail-fast 补全、`TYPE_CHECKING`、PEP 562 懒加载、产物路径归一化） |
| 二轮评审 | — | 复核修复成立；另找出 5 条新问题（4 条是提示词数字错、1 条是产物口径不全） |
| **本版（`cpc github v2`）** | **`cpc github v2`** | **二轮评审的 P1/P4 动作 + 一个历史 bug 修复 + CHANGELOG 显式披露 + 提示词修正** |

---

## 2. 基线事实（**口径已标注，请复核**）

代码指标口径：目录 `src/cellpaint_pipeline/`，行数 `len(text.splitlines())`，函数用 `ast.walk`。

| 指标 | 官方 `59df377` | 首版 `3cc412c` | **本版** |
|---|---|---|---|
| 源文件数 | 35 | 65 | **65** |
| 源码总行 | 13125 | 15619 | **15477**（相对官方 +18%） |
| 最大单文件 | 1646（`skills.py`） | 907 | **907**（`segmentation_native.py`，未变） |
| >400 行文件数 | 11 | 11 | **11**（未变） |
| 函数总数 | 348 | 477 | **470** |
| 最长函数 | 855 行（`cli.py:main`） | 201 行 | **201 行** |
| `If` 密度（每千行） | 38.6 | 29.8 | **30.4** |
| `def _impl` / `def _native` 份数 | — / — | 9 / 3 | **1 / 1** |
| 动态分发份数（`def` 计数） | 0 | 12 | **2** |
| 动态分发**调用点**数（`_impl(` + `_native(` + `_lazy(`） | 90 | 227 | **227**（未减，见下） |
| `import ...skills` | 37.7ms / 118 模块 | 45.7ms / 134 | **4.7ms / 76** |
| `import ...mcp_server` | 1564ms / 1703 模块 | 213ms / 392 | **217ms / 391** |
| `run_pipeline_skill` 参数 | 36 | 37 | **4** |
| 循环依赖 | 0 | 0 | **0** |
| pytest | 14F / 117P | 14F / 125P | **13F / 126P** |

> **`run_pipeline_skill` 参数的准确说明**：官方 36 个显式关键字参数；本版为
> `(config, skill_key, *, inputs=None, **legacy_kwargs)` —— `inspect.signature` 报 4 个参数。
> 所有历史关键字仍然可用。**但有一个行为差异**：未知名参数的错误文案从解释器默认
> 变成项目自定义（`Unexpected keyword argument for run_pipeline_skill: <name>`），已写进 CHANGELOG。

**环境限制（两版相同，非本次引入）**：

1. CellProfiler 的 JVM 读不了非 ASCII 路径：含中文路径下会写
   `OSError: Test for access to directory failed`，**而脚本仍以 `returncode=0` 结束**，技能误报 `ok:true`。
   **这是本版仍未修复的问题（D2）**，请评估其影响面。
2. `dp-run-deep-feature-model` 需联网取 Zenodo 权重（19,236,600 字节）。

**pytest**（失败数随平台与可选依赖变化，**关键看失败 node id 集合是否各版一致**）：

```bash
pip install pytest pycytominer pandas pyarrow
python -m pytest tests -q --no-header -p no:cacheprovider
```

---

## 3. 审核任务 A：代码

### A1 行为等价（黑盒）

| 检查项 | 方法 |
|---|---|
| 技能目录 | `available_pipeline_skills()` 的 **4 种开关组合**：无参 / `include_advanced=True` / `include_legacy=True` / 两者都 True |
| 签名 | `inspect.signature` 逐字段比对（**注意本版参数已合并，会比官方少 33 个**） |
| CLI 表面 | 内省 `build_parser()` 全部 subparser 的每个 action：`option_strings/dest/required/nargs/default/choices/help/const` |
| pathlike 白名单 | `registry.pathlike_keywords()`；确认基线的 MCP 侧是它的真子集 |
| legacy 报错 | 实调 8 个 legacy key，比异常文本 |
| 入口映射 | `ENTRYPOINT_TARGETS` / `RESULT_SERIALISERS` 逐条比 `module:function` |
| `run_pipeline_skill` 输入形态 | 扁平关键字 / `inputs=SkillInputs(...)` / 两者混用 / 未知名 / 废弃参数 / 同字段重复，**六种路径** |

**中间产物**：跑一条不依赖网络的确定性链路，基线与本版各一遍，**归一化后 md5** 比对：

```
data-plan-download → cp-build-single-cell-table → cyto-aggregate-profiles
  → cyto-annotate-profiles → cyto-normalize-profiles → cyto-select-profile-features
  → cyto-summarize-classical-profiles
```

归一化必须覆盖：绝对路径（JSON 转义 `\\` 与 CSV 的 `\` 两种）、时间戳、
`Image.csv` 的 `ExecutionTime_*`、parquet 的 `Metadata_*` 路径列。

### A2 逻辑等价（白盒）

`ast.unparse` 归一化后逐字比较。归一化必须处理三种间接层，否则会把搬迁误判成改写：

```python
_native('name')  ->  name      # skills 包
_impl('name')    ->  name      # cli 包
_lazy(...)       ->  ...       # cli 包延迟导入绑定
```

**请同时给出「函数个数」与「调用点个数」两个口径。**

### 需要重点核查语义的改写点

| 改写 | 要查什么 |
|---|---|
| `run_command` → `SubprocessCommandRunner` | 空命令 `ValueError`、CWD 不存在 `FileNotFoundError`、`OSError → CommandExecutionError`、非零返回码、输出尾行数、日志命名，**6 项是否全保留** |
| `run_workflow` → `WORKFLOW_HANDLERS` | 7 个 key 一一对应；未知 key 报错文本；**异常包装范围** |
| `_public_api_result_to_dict` → `RESULT_SERIALISERS` | 8 条映射逐条相同；默认分支 |
| `evaluation.py` 延迟导入 | **是否改变了导入副作用**（matplotlib backend 是重点：官方无 `matplotlib.use`，重构版新增了 `matplotlib.use('Agg')`） |
| 新增可选 `locator` 参数 | 默认值是否严格等于历史行为 |
| `skills/__init__.py` 的 `__getattr__` | 是否让叶子模块真正成为叶子；**`patch()` 接缝是否仍有效**；未知属性是否抛 `AttributeError`；`from ... import *` 是否仍可用 |
| `run_pipeline_skill` 的 `**legacy_kwargs` | **未知名参数是否仍抛 `TypeError`**（这是最容易退化的地方） |

### A3 代码质量（量化）

请自行采集并**逐项标注口径**，然后回答：
1. 是否更简洁？（总行数 +18%，请分析新增行的构成：空行/docstring/注解/实码各占多少）
2. 是否降低了复杂度？（最大文件 907 未变、>400 行文件数 11→11 未变，请判断「切碎」与「降复杂度」的区别）
3. 耦合是否真的降低？（**自行画依赖图并检测环**）
4. **227 个动态分发调用点**（相对官方 90）是否值得？它换来了 `patch()` 接缝的保持。**这笔交易划算吗？有没有更好的做法？**
5. 是否有过度设计？
6. 是否存在 SSOT 违反？（提示：`skills/outputs.py` 只覆盖 **6 个** skill，其余 31 个仍是手写双份——这是文档承认过的范围限制）

---

## 4. 审核任务 B：提示词文档本身

本目录携带两份提示词，**它们也是审核对象**：

| 文档 | 位置 | 说明 |
|---|---|---|
| **本任务书的上一版** | `docs/review_prompt_v2.md` | 二轮评审任务书，**已按二轮反馈修正 4 处数字** |
| 更早的版本 | `D:\项目\CPC-v1-审查提示词.md` | 首版提示词，**已被证伪 8 处** |

对每份提示词回答：

| 维度 | 具体要求 |
|---|---|
| 数字准确性 | 每个数字能否复现？口径是否写明？ |
| 内部一致性 | 同一数字在不同章节是否一致？（首版提示词犯过 §3 与 §9 自相矛盾的错） |
| 事实正确性 | 有没有断言了不成立的事实？（首版说过「仓库已带产物可对拍」，实际基线产物数为 0） |
| 引导偏差 | 有没有让审查者得出错误结论的措辞？ |
| 可执行性 | 命令能否直接跑？前置条件是否交代？ |
| 遗漏 | 有没有该查但没提的项？ |

> **已知的一类系统性偏差**：提示词里的归一化正则含 `[\\/]` 这类转义，
> 若通过 shell heredoc 传给 Python 会掉一层反斜杠，导致 Windows 路径一条都匹配不上、
> 静默返回「0 条」的**假阴性**。首版的全 JSON 悬空检查就是这样得出错误的 0。
> **请检查现在的提示词是否已经把这条写清楚。**

---

## 5. 已知问题清单（**这是下界，不是上界**）

### 5.1 已修复（请验证是否真的修好、有无引入新问题）

| # | 原问题 | 本版的修法 | 你要验证什么 |
|---|---|---|---|
| F1 | `cli/commands/` 9 份逐字节相同的 `def _impl` | 收敛为 `cli/helpers.py` 一份 | `def _impl` 是否只剩 1 处；**112 个调用点行为是否不变**；`patch('cellpaint_pipeline.cli.<name>')` 是否仍有效 |
| F2 | 3 份 `def _native` | 收敛为 `skills/finalize.py` 一份 | 同上（25 个调用点） |
| F3 | fail-fast 只做一半 | 必填项缺值也 raise | 构造输入实测两个方向 |
| F4 | `dispatch.py` 漏 `TYPE_CHECKING` | 已补，与另两处一致 | **`get_type_hints()` 仍会失败，这是正常的**（`TYPE_CHECKING` 块运行时不执行），不要当成缺陷 |
| F5 | `skills` 导入比官方慢 | PEP 562 懒加载 | 复现耗时；**`patch()` 接缝是否仍有效**；未知属性是否抛 `AttributeError` |
| F6 | 演示产物路径指向旧文件夹 | 已归一化 | 但注意**本版不含 demo 产物**，需到 `cpc github v1 demo` 验证 |
| F8 | `run_pipeline_skill` 37 个扁平参数 | 改为 `(config, skill_key, *, inputs, **legacy_kwargs)` | **六种输入路径逐一实测**，尤其未知名参数是否仍报错 |
| P1 | 命名空间收窄披露不完整 | `skills.ExecutionResult` + `cli.ProjectConfig` 回填；其余 **29 个**写进 CHANGELOG 的 `Removed` 节 | 核对 CHANGELOG 的名单与实测是否一致 |
| P4 | 同 F8 | 同上 | 同上 |

### 5.2 **未修复**（请评估其影响面与优先级）

| # | 问题 | 说明 |
|---|---|---|
| D2 | **CellProfiler 失败被静默吞掉** | 脚本 `returncode=0`、技能报 `ok:true`，只有日志里有 `pipeline_exception`。**两版都有，非本次引入，但本版也没修。** 这会让自动化流水线在分割失败时仍然「成功」。请评估严重度 |
| D4 | 源码总量 +18%、>400 行文件数 11→11 | 巨型文件被切碎但没变少；`segmentation_native.py` 907 行、`orchestration.py` 805 行仍然很大 |
| N1 | 227 个动态分发调用点 | 相对官方 90。为保 `patch()` 接缝而保留，**份数归 1 ≠ 成本归零** |
| N2 | `outputs.py` 的 SSOT 只覆盖 6/37 个技能 | 其余 31 个仍是手写双份 `primary_outputs` + `typical_outputs`。文档承认过范围，但机制已就绪可增量迁移 |

> **本清单的作用是让你不要重复劳动，不是让你停止寻找。**
> 前两轮的经验是：每一轮都在「已确认无误」的部分里又找出了新问题。

---

## 6. 禁止事项

1. 不要把 `main`(855 行) 拆成 9 个 handler 计为「实质改写」——那是搬迁。先归一化再判定。
2. 不要把「函数数增加」等同于「复杂度增加」。
3. 不要用绝对路径或时间戳判定产物不一致——先归一化。
4. 不要把「文档少列了代码多产出的文件」当作行为差异。
5. 不要在缺少基线的情况下说「与原版一致」——说「无法判定」。
6. 不要引用本任务书的数字作为你自己的结论。
7. 不要把 `get_type_hints()` 失败当作缺陷（见 F4）。
8. **任何附带的检查脚本一律以 `.py` 文件形式给出，不要用 heredoc 内联**（见第 4 节末的陷阱说明）。

---

## 7. 无法判定协议

| 情况 | 你要写的 |
|---|---|
| 缺 CellProfiler / DeepProfiler / 权重 | 「阶段 X 无法判定：缺少 …」 |
| 缺可选依赖 | 「pytest 结果无法比对：缺少 …」 |
| 基线 commit 无对应产物 | 「无法基线对拍：`59df377` 无产物」 |
| 网络不可达 | 「阶段 X 无法判定：网络不可达」 |

**「无法判定」不是失败；把推断写成结论才是。**

---

## 8. 输出格式

```markdown
# 审核报告
## 0. 执行摘要（你实际跑通了什么、没跑通什么）
## 1. 复现范围表
## 2. 行为等价结论（逐项 + 证据）
## 3. 逻辑等价结论（逐函数分类计数 + 每处实质改写的判定）
## 4. 已修复项的验证结果（F1–F6、F8、P1、P4 逐条：已修复/未修复/部分/无法判定）
## 5. 未修复项的影响面评估（D2、D4、N1、N2）
## 6. 代码质量量化（口径写清 + 你画的依赖图）
## 7. 提示词审核结论（逐份、逐维度）
## 8. 新发现（位置:行 + 复现步骤 + 实际输出 + 影响面 + 严重度）
## 9. 无法判定清单
## 10. 建议动作（优先级 / 位置 / 建议 / 成本 / 收益）
## 11. 总结论（行为是否等价 / 逻辑是否等价 / 是否更优 / 能否进主干）
```

---

## 9. 参考资料

| 资源 | 地址 |
|---|---|
| 官方原版 | https://github.com/Seniorious123/CellPainting-Claw |
| 官方文档 | https://cellpainting-claw.readthedocs.io/en/latest/index.html |
| 重构版（含 demo 产物） | https://github.com/liuzy0543-spec/CPC-v1 |
| DeepProfiler 工具 | https://github.com/broadinstitute/DeepProfiler |
| 预训练权重 | https://zenodo.org/records/7114558 |

（任务书结束）
