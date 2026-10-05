# 代码与提示词审核任务书 · v5.1（针对 `cpc github v2`）

> **审核对象：`D:\项目\cpc github v2`**
>
> 本任务书同时要求审核**代码**与**提示词文档**两部分。

---

## 0. 阅读约定（**请先读这一节**）

### 0.1 语气标注

| 标注 | 含义 | 你的义务 |
|---|---|---|
| **【事实】** | 本环境实测，且**紧邻给出了可复现命令** | 抽样复核；**若发现是假的，列为最高优先级发现** |
| **【主张】** | 声称但未实测，**或无法给出复现命令** | 独立复算，不得直接引用 |
| **【未知】** | 写就时没有验证 | 有条件就测，否则按 §9 标注 |

### 0.2 硬规则：无命令不成【事实】

> **凡标【事实】者，必须紧邻附可复现命令；给不出命令的一律降为【主张】。**

这条规则是四轮迭代的产物：

| 轮次 | 暴露的缺陷类型 | 例子 |
|---|---|---|
| 第 3 轮 | **主张伪装成事实** | v3.1 两处「已写进 CHANGELOG」，实测 `dd7c182`/`3295122` 根本没碰过该文件 |
| 第 4 轮 | **推导伪装成实测** | v4 写「实测 331 / 429」，但 297 = 331−11−23 是**倒推**，11 与 23 又来自首版自己的声称 |
| 第 4 轮 | **文档工程失控** | v4.1 出现两个 `## 7`、重复的 `### 6.1`、位置错乱的表格 |

本版针对第三类加了生成期检查：**每个标题只可能输出一次**（见文末 §12 的结构自检）。

---

## 1. 审核对象

| 项 | 值 |
|---|---|
| 本地路径 | `D:\项目\cpc github v2` |
| git | 工作区 clean。**HEAD 与提交数请用 `git rev-parse HEAD` / `git rev-list --count HEAD` 取**——本文件不硬编码它们，因为它自己也在提交历史里（上游基线 152 个提交） |
| 基线 | 官方 `59df377` |
| 上游仓库 | https://github.com/Seniorious123/CellPainting-Claw |
| 官方文档站 | https://cellpainting-claw.readthedocs.io/en/latest/index.html |

### 1.1 ⚠️ 本任务书自身也在被审核目录里

本文件即 `D:\项目\cpc github v2\docs\review_prompt.md`，**它是交付物的一部分，因此也是审核对象**。

第一步就运行（**计数类断言一律用命令，不要肉眼点数** —— 一份前序任务书曾把 8 个 `??` 数成 7 个）：

```bash
cd "D:\项目\cpc github v2" && git status --porcelain | cut -c1-2 | sort | uniq -c
```

### 1.2 如何取出官方基线树

```bash
mkdir -p ../base
git -C "D:\项目\cpc github v2" archive 59df377 src/cellpaint_pipeline | tar -x -C ../base   # 方式 A：只取源码
git -C "D:\项目\cpc github v2" worktree add ../base 59df377                                # 方式 B：整棵树
```

---

## 2. 项目背景

**CellPainting-Claw** 把 Cell Painting 高内涵成像流水线封装成 agent 可调用技能：45 个技能目录项
（37 个可执行 + 8 个 legacy 占位），三种入口（Python API / 52 条 CLI 子命令 / MCP），
链路为 数据接入 → CellProfiler 分割测量 → pycytominer 经典特征 → DeepProfiler 深度特征 → 汇总。

本次交付：把 `skills.py` 与 `cli.py` 拆成 `skills/` 与 `cli/` 两个包，
新增 `ports.py` / `registry.py` / `capabilities.py` / `errors.py` / `skills/outputs.py`。

学术背景：Bray 2016 https://www.nature.com/articles/nprot.2016.105 ｜
Caicedo 2017 https://www.nature.com/articles/nmeth.4397 ｜
Carpenter 2006 https://genomebiology.biomedcentral.com/articles/10.1186/gb-2006-7-10-r100 ｜
Smith 2018 DeepProfiler https://doi.org/10.1016/j.cels.2018.06.005 ｜
权重 https://zenodo.org/records/7114558 ｜
pycytominer https://github.com/cytomining/pycytominer ｜
JUMP-CP https://www.nature.com/articles/s41592-024-02241-6

---

## 3. 基线事实

### 3.1 静态代码指标 【事实】

口径：目录 `src/cellpaint_pipeline/`；行数 `len(text.splitlines())`；函数与 `If` 用 `ast.walk`。

| 指标 | 官方 `59df377` | `cpc github v1` | **本目录** |
|---|---|---|---|
| 源文件数 | 35 | 65 | **65** |
| 源码总行 | 13125 | 15619 | **15477**（+18%） |
| 最大单文件 | 1646（`skills.py`） | 907 | **907** |
| >400 行文件数 | 11 | 11 | **11** |
| 函数总数 | 348 | 477 | **470** |
| 最长函数 | 855 行 | 201 行 | **201 行** |
| `If` 密度（每千行） | 38.6 | 29.8 | **30.4** |
| `def _impl` / `_native` / `_lazy` | 0 / 0 / 1 | 9 / 3 / 1 | **1 / 1 / 1** |
| 动态分发调用点 | 90 | 227 | **227** |
| `run_pipeline_skill` 参数 | 36 | 37 | **4** |
| 循环依赖 | 0 | 0 | **0** |

复现命令（存为 `metrics.py` 后 `python metrics.py <树根>`）：

```python
# metrics.py  —— 存成文件再跑；不要用 heredoc（见 §8 第 8 条）
import ast, pathlib, sys
root = pathlib.Path(sys.argv[1]) / 'src' / 'cellpaint_pipeline'
files = sorted(p for p in root.rglob('*.py') if '__pycache__' not in str(p))
sizes = {p: len(p.read_text(encoding='utf-8').splitlines()) for p in files}
funcs = ifs = 0
for p in files:
    tree = ast.parse(p.read_text(encoding='utf-8'))
    ifs += sum(1 for n in ast.walk(tree) if isinstance(n, ast.If))
    funcs += sum(1 for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
lines = sum(sizes.values())
print('files', len(files), 'lines', lines, 'funcs', funcs, 'if/kloc', round(ifs * 1000 / lines, 1))
print('max', max(sizes.items(), key=lambda kv: kv[1]))
print('over400', sum(1 for v in sizes.values() if v > 400))
print('nest_max', max(len(list(ast.walk(n))) for p in files
                      for n in ast.walk(ast.parse(p.read_text(encoding='utf-8')))
                      if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))) if files else 0)
```

### 3.2 运行性能 【事实，但环境强相关，绝对值不可跨环境比较】

| 指标 | 官方 `59df377` | `cpc github v1` | `cpc github v2` |
|---|---|---|---|
| `import cellpaint_pipeline.skills` | 37.7ms / 118 模块 | 45.7ms / 134 | **4.7ms / 76** |
| `import cellpaint_pipeline.mcp_server` | 1564ms / 1703 模块 | 213ms / 392 | **217ms / 391** |

复现命令：

```bash
python -c "import time,sys;t=time.perf_counter();import cellpaint_pipeline.skills;print(round((time.perf_counter()-t)*1000,1), len(sys.modules))"
```

**写就环境（必须一并报告，否则数字不可比）**：Python 3.11.5；`pycytominer`/`pandas`/`pyarrow` 已装，
`boto3`/CellProfiler/TensorFlow 未装；独立子进程 11 次取最小值，`.pyc` 已预热。

> **已有反例**：一轮独立审核在缺 `tifffile` 的 Python 3.13.12 环境测得官方 **58.0ms / 138 模块**。
> **趋势一致（v2 比官方快约一个数量级），绝对值不可复现。**
> 绝对值不同**不是造假，是环境差异** —— 请报告你的环境口径，再比较量级与趋势。

### 3.3 环境限制 【事实】

1. **CellProfiler 的 JVM 读不了非 ASCII 路径**：含中文路径下写
   `OSError: Test for access to directory failed`，**而脚本仍以 `returncode=0` 结束**，技能报 `ok:true`。
   要跑分割类技能必须先把仓库放到纯 ASCII 路径。见 §7.2 的 D2。
2. `dp-run-deep-feature-model` 需联网取 Zenodo 权重（19,236,600 字节）。

### 3.4 pytest 【事实】

```bash
pip install pytest pycytominer pandas pyarrow
python -m pytest tests -q --no-header -p no:cacheprovider
```

**失败数随平台与可选依赖变化，关键看失败 node id 集合是否各版一致，而非绝对数量。**

| 来源（已注明出处） | 官方 | v1 | v2 |
|---|---|---|---|
| 本任务书写就环境（Python 3.11.5） | 未测 | 未测 | 13 failed / 126 passed |
| **第二轮代码审核报告**（Python 3.10.11，缺可选依赖） | 14 failed / 117 passed | 14 failed / 125 passed | 14 failed / 125 passed |

> 第二行的出处是**第二轮代码审核报告**（它实测三棵树的失败 node id 集合完全一致）。
> v4 曾引用这组数字却没标来源，被第四轮审核指出 —— 现已补上出处。

---

## 4. 路径表（**请逐条验证存在性**）

| 路径 | 说明 |
|---|---|
| `D:\项目\cpc github v2` | 本任务书要审的目录 |
| `D:\项目\cpc github v2\docs\review_prompt.md` | **本任务书自身**（已提交） |
| `D:\项目\cpc github v2\CHANGELOG.md` | 含 `Unreleased - modular refactor line` 一节 |
| `D:\项目\cpc github v1` | 首版重构（**改动未提交**） |
| `D:\项目\cpc github v1 demo` | 同一份代码 + 199 个 demo 产物 |
| `D:\项目\CPC-v1-审查提示词.md` | 首版提示词（已知 8 处被证伪） |
| `D:\项目\CPC-v1-审查提示词-v5.md` | 对照版，针对 v1 目录 |

复现命令（把路径表里的每条粘进 `p`）：

```bash
for p in "D:\项目\cpc github v1" "D:\项目\cpc github v2"; do [ -e "$p" ] && echo "OK   $p" || echo "MISS $p"; done
```

---

## 5. 审核任务 A / B：代码

### 5.1 行为等价（黑盒）

| 检查项 | 符号定位 | 方法 |
|---|---|---|
| 技能目录 | `cellpaint_pipeline.skills:catalog.available_pipeline_skills` | **4 种开关组合**：无参 / `include_advanced=True` / `include_legacy=True` / 两者都 True |
| 入口签名 | `cellpaint_pipeline.skills:dispatch.run_pipeline_skill` | `inspect.signature` 逐字段 |
| CLI 表面 | `cellpaint_pipeline.cli:build_parser` | 全部 subparser 的每个 action：`option_strings/dest/required/nargs/default/choices/help/const` |
| pathlike 白名单 | `cellpaint_pipeline.registry:pathlike_keywords` | 确认基线的 MCP 侧是它的真子集 |
| 入口映射 | `cellpaint_pipeline.registry:ENTRYPOINT_TARGETS` / `RESULT_SERIALISERS` | 逐条比 `module:function` |
| legacy 报错 | 8 个 legacy key | 实调并比异常文本 |
| 输入形态 | `cellpaint_pipeline.skills:inputs.assemble_skill_inputs` | **六种路径**：扁平 / `inputs=` 对象 / 混用 / 未知名 / 废弃参数 / 同字段重复 |

**中间产物**：跑一条不依赖网络的确定性链路，两棵树各一遍，**归一化后 md5** 比对：

```
data-plan-download → cp-build-single-cell-table → cyto-aggregate-profiles
  → cyto-annotate-profiles → cyto-normalize-profiles → cyto-select-profile-features
  → cyto-summarize-classical-profiles
```

归一化必须覆盖：绝对路径（JSON 转义 `\\` 与 CSV 的 `\` **两种**）、时间戳、
`Image.csv` 的 `ExecutionTime_*`、parquet 的 `Metadata_*` 路径列。

### 5.2 逻辑等价（白盒）

`ast.unparse` 归一化后逐字比较全部 `FunctionDef`/`AsyncFunctionDef`。
**归一化必须处理三种间接层**，否则会把搬迁误判成改写：

```python
_native('name')  ->  name      # skills 包
_impl('name')    ->  name      # cli 包
_lazy(...)       ->  ...       # cli 包延迟导入绑定
```

**两个口径都要给，且都含 `_lazy`**。复现命令：

```bash
grep -rc '^def _impl' src; grep -rc '^def _native' src; grep -rc '^def _lazy' src
grep -ro '_impl(' src | wc -l; grep -ro '_native(' src | wc -l; grep -ro '_lazy(' src | wc -l   # 减去定义行
```

| 口径 | 定义 | 官方 | v1 | v2 |
|---|---|---|---|---|
| 定义处份数 | `def _impl` + `def _native` + `def _lazy` | **1** | 13 | **3** |
| 调用点数 | 上述三个的调用扣除定义行 | **90** | 227 | **227** |

> v3.1 曾写「份数 0/12/2」—— 漏了 `_lazy`，且把官方的 1 写成 0。**份数归 1 不等于成本归零。**

### 5.3 需要重点核查语义的改写点

| 改写 | 要查什么 |
|---|---|
| `run_command` → `SubprocessCommandRunner` | 空命令 `ValueError`、CWD 不存在 `FileNotFoundError`、`OSError → CommandExecutionError`、非零返回码、输出尾行数、日志命名，**6 项是否全保留** |
| `run_workflow` → `WORKFLOW_HANDLERS` | 7 个 key 一一对应；未知 key 报错文本；**异常包装范围** |
| `_public_api_result_to_dict` → `RESULT_SERIALISERS` | 8 条映射逐条相同；默认分支 |
| `evaluation.py` 延迟导入 | **导入副作用是否改变**（官方无 `matplotlib.use`，重构版新增了 `matplotlib.use('Agg')`） |
| 新增可选 `locator` 参数 | 默认值是否严格等于历史行为 |
| `skills/__init__.py` 的 `__getattr__` | 叶子化是否成立；**`patch()` 接缝是否仍有效**；未知属性是否抛 `AttributeError`；`from ... import *` 是否仍可用 |
| `run_pipeline_skill` 的 `**legacy_kwargs` | **未知名参数是否仍抛 `TypeError`**（最容易退化的地方） |

### 5.4 代码质量（量化）

1. 是否更简洁？（总行数增减 + **新增行的构成**：空行 / docstring / 注解 / 实码各占多少）
2. 是否降低了复杂度？（最大文件、>400 行文件数、最长函数、`If` 密度）
3. 耦合是否真的降低？（**自行画依赖图并检测环**）
4. **227 个动态分发调用点**（官方 90）这笔交易划算吗？有没有更好的做法？
5. 是否有过度设计？ 6. 是否存在 SSOT 违反？
7. **文档与代码是否同步？** 运行 `git log --oneline -- CHANGELOG.md`，把 CHANGELOG 声称的改动逐条与实测对照。

> 第 7 条是被审核出来的：v3.1 曾两处断言「已写进 CHANGELOG」，实测两次重构提交**都没碰过该文件**。

---

## 6. 审核任务 C：提示词文档

| 文档 | 位置 | 状态 |
|---|---|---|
| **本任务书** | `cpc github v2\docs\review_prompt.md` | 本文件 |
| 第二版任务书 | `cpc github v2\docs\review_prompt_v2.md` | 已修正 4 处数字 |
| 第三版 | `D:\项目\CPC-v1-审查提示词-v3.md` | 已知 3 处 P0 错误 |
| 第三版之二 | `D:\项目\CPC-v1-审查提示词-v3.1.md` | 已知 3 处 P0 错误 |
| 第四版 | `D:\项目\CPC-v1-审查提示词-v4.md` **与** `-v4.1.md` | 已知结构损坏（两个 `## 7`、重复 `### 6.1`） |

### 6.1 审核维度

| 维度 | 具体要求 | 反面教材 |
|---|---|---|
| 数字准确性 | 每个数字能否复现？口径写明？**命令给了吗**？ | v3 同文档混用 1647 与 1646 两种行数口径 |
| 内部一致性 | 同一编号/数字在不同章节是否一致？ | v4.1 出现两个 `## 7` 与重复的 `### 6.1` |
| 事实正确性 | 有没有断言了不成立的事实？ | v3.1 两处「已写进 CHANGELOG」，实测没写 |
| **标注正确性** | 标【事实】的，真的紧邻附了可复现命令吗？ | v4 把倒推值 297 = 331−11−23 标成了【事实】 |
| **归属正确性** | 批评某份文档时，被引用的内容**真的在那份文档里**吗？ | v3 指控首版有「113/26/91 vs 112/25/90」的矛盾，实测首版中 `113`/`112` 出现 **0 次** |
| **自指完整性** | 任务书是否把自己列为审核对象？ | v3 说「本目录没有提示词文档」，而它自己就在该目录 |
| **可执行性** | 命令能否直接跑？前置条件交代？ | v3/v3.1 都要求双树对拍，却都没给取基线树的命令 |

### 6.2 前序提示词已被证伪的条目

| 提示词 | 它说 | 实测 | 性质 |
|---|---|---|---|
| v3.1 | 参数文案变更「已写进 CHANGELOG」 | `dd7c182`/`3295122` **均未碰过 CHANGELOG.md** | 事实错误 |
| v3.1 | 29 个命名空间名「写进 CHANGELOG 的 Removed 节」 | 当时 CHANGELOG 仅 24 行，Removed 只有 2 条无关条目 | 事实错误 |
| v3.1 | §0「全部已知问题已修复」 | 同文档 §5.2 列了 4 条未修复 | 自相矛盾 |
| v3 | 指控首版「§3 说 113/26/91，§9 说 112/25/90」 | 首版中 `113`/`112` 出现 **0 次**；该数字在 v2 提示词里 | 数字错 + 归属错 + 性质错 |
| v3 | 「本目录没有任何提示词文档」 | `cpc github v1\docs\review_prompt.md` 存在 | 自指盲区 |
| v3 | §1 写 1647 / §2 写 1646 | 同一文档混用两种行数口径 | 口径混用 |
| v3.1 | 动态分发份数「0 / 12 / 2」 | 应为 **1 / 13 / 3**（含 `_lazy`） | 口径不一致 |
| v3 / v3.1 | 要求双树对拍 | **都没给出取基线树的命令** | 可执行性缺失 |
| v4 | 「实测 331 / 429 / 297」 | 297 = 331−11−23 是**倒推**；另一轮实测为 431 / 296 | 推导伪装成实测 |
| v4.1 | 两个 `## 7` + 重复 `### 6.1` + 错位表格 | 生成期无重复检查 | 文档工程失控 |
| v4.1 | 引用「14 failed / 117 passed」未标来源 | 出自第二轮代码审核报告 | 来源缺失 |
| v4.1 | §7.1「已修复」漏列 D3 | CHANGELOG 的 Fixed 节写了 D3 | 遗漏 |

### 6.3 首版提示词的真实一致性缺陷（v3 漏检，且自己举错了例子）

**【事实】** 首版 §9 的函数分类计数**不闭合**。复现命令：

```bash
grep -n '301 逐字节相同\|23 实质改写\|348 个原函数\|98 新增' "D:\项目\CPC-v1-审查提示词.md"
```

它会显示首版同时写着「348 个原函数」「301 逐字节相同」「23 实质改写」「98 新增」。算术：

```
301 + 11 + 23 + 0 = 335  ≠ 348
331 + 98          = 429  ≠ 475
```

**【主张】** 首版把 **331/429 口径的分类计数**与 **348/475 口径的函数总数**写进了同一条。
依据：**331** 已被两轮独立审核分别复现（按函数名匹配 + `ast.walk` 全量）。
**本任务书不给出 331 的复现脚本**（前序版本给不出，故降级为【主张】）。

**【主张】** 首版分类里的**逐字节相同 = 297** 是 **297 = 331 − 11 − 23** 的**倒推**，**不是实测**；
且 11 与 23 直接来自首版自己的声称。一轮独立审核实测为 **296**（重构侧总数 **431**、新增 **100**，而非 429/98）。
**双方都没给出可复现脚本，所以整项标【主张】。**

> **这里是本任务书自己的反面教材记录**：v4 把上述倒推值标成了【事实】，违反 §0.2 的硬规则。
> 保留这段是为了让你检查本节还有没有同类问题。

---

## 7. 已知问题清单（**这是下界，不是上界**）

### 7.1 已修复（**逐条给出「验证命令 + 期望输出」，不要只看表格**）

| # | 原问题 | 修法 | 验证命令 / 期望 |
|---|---|---|---|
| F1 | 9 份重复 `def _impl` | 收敛为 `cli/helpers.py:147` | `grep -rc '^def _impl' src` → 1 |
| F2 | 3 份重复 `def _native` | 收敛为 `skills/finalize.py:109` | 同上 → 1 |
| F3 | fail-fast 只做一半 | 必填缺值也 raise | 缺键 → `ValueError: required output(s) were not produced: …` |
| F4 | `dispatch.py` 漏 `TYPE_CHECKING` | 已补，三处一致 | `get_type_hints()` **仍会失败，这是正常的** |
| F5 | `skills` 导入比官方慢 | PEP 562 懒加载 | 4.7ms/76（环境见 §3.2） |
| F6 | 演示产物路径指向旧名 | 已归一化 | **本目录不含 demo 产物**，需到 `cpc github v1 demo` 验证 |
| F8 | 37 个扁平参数 | `(config, skill_key, *, inputs, **legacy_kwargs)` | 签名 4 参数；**六种输入路径逐一实测** |
| P1 | 命名空间收窄披露不完整 | 回填 2 个 + CHANGELOG 列 29 个 | `hasattr` → True；`git log --oneline -- CHANGELOG.md` 应含修复提交 |
| D3 | cache root 解析成 `demo/demo/...` | 改为 workspace 相对 | `grep -o '"data_cache_root": "[^"]*"' configs/*.json` → `cache/data` |

### 7.2 **未修复**（请评估影响面与优先级）

| # | 问题 | 说明 |
|---|---|---|
| D2 | **CellProfiler 失败被静默吞掉** | 脚本 `returncode=0`、技能报 `ok:true`，只有日志有 `pipeline_exception`。**两版均未修** |
| D4 | 源码总量 +18%、>400 行文件数 11→11 | `segmentation_native.py` 907 行、`orchestration.py` 805 行仍很大 |
| N1 | 227 个动态分发调用点 | 官方 90。为保 `patch()` 接缝而保留，**份数归 1 ≠ 成本归零** |
| N2 | `outputs.py` 的 SSOT 只覆盖 6/37 个技能 | 其余 31 个仍是手写双份；机制已就绪，可增量迁移 |

### 7.3 关于总结性断言（前车之鉴）

v3.1 在文档最顶部写了「**全部已知问题已修复**」，与它自己 §5.2 的 4 条未修复直接冲突。
**本版不写这种总结性断言** —— 已修复与未修复两类都在上面列全，请以实测为准。

---

## 8. 禁止事项

1. 不要把 `main`(855 行) 拆成 9 个 handler 计为「实质改写」——那是搬迁。先归一化再判定。
2. 不要把「函数数增加」等同于「复杂度增加」。
3. 不要用绝对路径或时间戳判定产物不一致——先归一化。
4. 不要把「文档少列了代码多产出的文件」当作行为差异。
5. 不要在缺少基线的情况下说「与原版一致」——说「无法判定」。
6. **不要引用本任务书的数字作为你自己的结论**（重复一遍，因为这是最容易犯的）。
7. 不要把 `get_type_hints()` 失败当作缺陷（`TYPE_CHECKING` 块运行时不执行，属正常）。
8. **含转义正则（`[\\/]` 之类）的脚本一律写成 `.py` 文件，不要用 heredoc 内联**：
   反斜杠会掉一层，导致 Windows 路径一条都匹配不上、静默返回「0 条」的**假阴性**。
   一轮独立审核正是这样先得到错误的「0 条悬空」，改成文件后才查出真实的 24 条。

---

## 9. 无法判定协议

| 情况 | 你要写的 |
|---|---|
| 缺 CellProfiler / DeepProfiler / 权重 | 「阶段 X 无法判定：缺少 …」 |
| 缺可选依赖导致无法 import | 「指标 X 无法判定：缺少 …」 |
| 基线 commit 无对应产物 | 「无法基线对拍：`59df377` 无产物」 |
| 网络不可达 | 「阶段 X 无法判定：网络不可达」 |
| 环境与 §3.2 不同 | 「性能数字不可比，环境差异为 …；仅比较量级」 |

**「无法判定」不是失败；把推断写成结论才是。**

---

## 10. 输出格式

```markdown
# 审核报告
## 0. 执行摘要（跑通了什么、没跑通什么、环境口径）
## 1. 复现范围表
## 2. 第 3 节【事实】的复核结果（逐条：证实 / 证伪 / 无法判定）
## 3. 行为等价结论（逐项 + 证据）
## 4. 逻辑等价结论（两个口径的计数 + 每处实质改写的判定）
## 5. 代码质量量化（口径写清 + 依赖图 + 文档同步检查）
## 6. 提示词审核结论（逐维，含标注/归属/自指三项）
## 7. 新发现（位置:行 + 复现步骤 + 实际输出 + 影响面 + 严重度）
## 8. 无法判定清单
## 9. 建议动作（优先级 / 位置 / 建议 / 成本 / 收益）
## 10. 总结论（行为是否等价 / 逻辑是否等价 / 是否更优 / 能否进主干）
```

---

## 11. 参考资料

| 资源 | 地址 |
|---|---|
| 官方原版 | https://github.com/Seniorious123/CellPainting-Claw |
| 官方文档 | https://cellpainting-claw.readthedocs.io/en/latest/index.html |
| 重构版（含 demo 产物） | https://github.com/liuzy0543-spec/CPC-v1 |
| DeepProfiler | https://github.com/broadinstitute/DeepProfiler |
| 预训练权重 | https://zenodo.org/records/7114558 |

---

## 12. 本任务书的结构自检（生成期保证）

本文件由模板一次性渲染，**每个标题只输出一次**。生成后运行的检查：

```bash
# 排除围栏代码块，再抽取编号 —— 直接 grep '^## ' 会把 §10 输出格式模板里的标题也算进来，产生假重复
awk '/^```/{f=!f;next} !f && /^#{2,3} /{print}' docs/review_prompt.md \
  | sed 's/^\(#\{2,3\} [0-9][0-9.]*\).*/\1/' | sort | uniq -d
# 期望：无输出（没有重复编号）
```

**如果你发现本文件仍有重复编号或空壳章节，请作为最高优先级发现报告** ——
那意味着生成期检查失效，v4.1 正是这样损坏的。

（任务书结束）
