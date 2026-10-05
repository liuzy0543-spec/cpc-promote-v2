# CPC-v1 二次审查提示词 · Agent 执行版（v2）

> **这份文档是给 agent 执行的任务书，不是给人读的介绍。**
> 你有 shell / git / python 工具。第 5 节每个阶段都给了可直接执行的命令、期望输出和判定标准。
> 请按阶段执行，不要跳步；跑不了的阶段按第 7 节写「无法判定」，不要猜。

---

## 0. 任务定义

| 项 | 值 |
|---|---|
| 任务 | 对 CellPainting-Claw 的重构版做**第二轮**独立审查 |
| 审查对象 | **commit `dd7c182`**（不是第一轮的 `3cc412c`） |
| 基线 | 官方 `59df377` |
| 仓库 | https://github.com/liuzy0543-spec/CPC-v1 |
| 本地路径（若可访问） | `D:\项目\cpc github v1 demo` |
| 交付物 | 一份报告（第 8 节格式）+ 一份机器可读 JSON |

### 为什么有第二轮

第一轮审查发现了 5 个真实缺陷和 6 个提示词缺口。修复者提交了 `dd7c182`。
**你的首要任务不是重新审查一遍，而是验证那些修复是否真的成立、有没有引入新问题。**

---

## 1. 项目背景（30 秒版）

CellPainting-Claw 把 Cell Painting 高内涵成像流水线封装成 **agent 可调用技能**：
45 个技能目录项（37 个可执行 + 8 个 legacy 占位），三种入口（Python API / 52 条 CLI 子命令 / MCP），
链路是 数据接入 → CellProfiler 分割测量 → pycytominer 经典特征 → DeepProfiler 深度特征 → 汇总。

重构做的事：把 `skills.py`(1647 行) 和 `cli.py`(1605 行) 两个巨型单文件拆成两个包，
新增 `ports.py`（副作用端口）/ `registry.py`（入口单一事实源）/ `capabilities.py`（能力清单）/
`errors.py`，以及后续追加的 `skills/outputs.py`（输出契约）。

学术背景（按数据流排序）：

| 环节 | 出处 |
|---|---|
| Cell Painting 实验方法 | Bray et al., *Nature Protocols* 2016 — https://www.nature.com/articles/nprot.2016.105 |
| 图像 → 形态学谱分析框架 | Caicedo et al., *Nature Methods* 2017 — https://www.nature.com/articles/nmeth.4397 |
| 分割与测量工具 | Carpenter et al., *Genome Biology* 2006 (CellProfiler) — https://genomebiology.biomedcentral.com/articles/10.1186/gb-2006-7-10-r100 |
| 深度特征 | Smith et al., *Cell Systems* 2018 (DeepProfiler) — https://doi.org/10.1016/j.cels.2018.06.005 |
| 预训练权重 | https://zenodo.org/records/7114558 |
| 经典特征库 | https://github.com/cytomining/pycytominer |
| 大规模数据背景 | Chandrasekaran et al., *Nature Methods* 2024 (JUMP-CP) — https://www.nature.com/articles/s41592-024-02241-6 |
| 官方文档站（19 个技能的输入输出契约） | https://cellpainting-claw.readthedocs.io/en/latest/index.html |

---

## 2. 环境准备

```bash
git clone https://github.com/liuzy0543-spec/CPC-v1.git && cd CPC-v1
git log --oneline -3          # 必须是 dd7c182 / 3cc412c / 59df377
python -m venv .venv && . .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -e . && pip install pytest
```

**取差异不需要克隆两个仓库**（重构版保留了上游全部 152 个提交）：

```bash
git diff 59df377 dd7c182 --stat          # 全部改动
git diff 3cc412c dd7c182 --stat          # 只看第二轮修复
git diff 59df377 dd7c182 -- src/ tests/  # 源码全文
```

**已知环境限制（两版都一样，不是重构引入的）**：

1. **CellProfiler 的 JVM 读不了非 ASCII 路径**。含中文的路径下它会写
   `OSError: Test for access to directory failed`，**而脚本仍以 `returncode=0` 结束**，
   技能会误报 `ok:true`。要跑分割相关技能必须先把仓库放到纯 ASCII 路径。
   官方原版的演示产物同样是在临时 ASCII 目录里跑出来的。
2. `dp-run-deep-feature-model` 需要联网取 Zenodo 权重（19,236,600 字节）。
3. CellProfiler 4.2 + JVM、DeepProfiler + TensorFlow 未安装时，分割/深度特征相关阶段**跳过并标注无法判定**。

---

## 3. 第一轮审查的 8 处勘误（v1 提示词错在哪）

第一轮审查者证伪了旧提示词里的多处内容。**请把这张表当作「不要重犯的错误清单」，
并顺手复核这张表本身是否准确。**

| # | v1 说 | 实际 | 性质 |
|---|---|---|---|
| 1 | 最大单文件 613 行 | **907 行**（`segmentation_native.py`）；613/619 只是 `skills/catalog.py` | 选择性口径 |
| 2 | 源码 13160 → 15451 行 | **13125 → 15619**（`src/cellpaint_pipeline/`），且 15451 是 `outputs.py` 之前的旧数 | 旧数 + 口径混 |
| 3 | 仓库已带演示产物，可直接对拍、不必重跑 | **`59df377` 里 `demo/workspace/outputs` 有 0 个文件**，产物全是重构版自己的 | **事实错误** |
| 4 | 间接层「11 处」 | 11 是**函数数**；真实调用点 `_impl(` **112** + `_native(` **25** + `_lazy(` **90** | 低估约 20 倍 |
| 5 | 函数级比对归一化只需处理 `_native` | 还需处理 `_impl(`、`_lazy(` 以及模块 `__getattr__` | 照 v1 跑会得到虚高的「实质改写」数 |
| 6 | 有意偏离 3 条 | 漏了 `evaluation.py` **新增 `matplotlib.use('Agg')`** 这个进程级副作用 | 披露不完整 |
| 7 | 丢失的公开名 13 个 | `skills` 13 + `evaluation` 6 + `runner` 6 + `adapters.deepprofiler_project` 1 + `cli` 5 = **31**（多为泄漏的 stdlib 导入） | 披露不完整 |
| 8 | 「加 workflow = 加一行」 | 需要改 **2 个文件 3 处**：`capabilities.py` 的 `WORKFLOW_KEYS`、`orchestration.py` 的 handler 与 `WORKFLOW_HANDLERS` | 不准确 |

**教训**：凡是数字，都要写明**统计口径**（哪个目录、哪个 commit、`.splitlines()` 还是 `wc -l`、是否含 `def` 行本身）。
凡是「两边一样」的结论，都要说明**基线从哪来**。

---

## 4. 第一轮的发现清单 —— 逐条验证是否真的修好

第一轮有 8 条可执行结论，逐条核对。**每条都要给出 `结论：已修复 / 未修复 / 部分修复 / 无法判定` 和证据。**

| # | 第一轮发现 | 声称的修法 | 你要验证什么 |
|---|---|---|---|
| F1 | `cli/commands/` 下 9 份逐字节相同的 `def _impl`（10 行 × 9） | 收敛为 `cli/helpers.py` 一份 | ① `def _impl` 是否只剩 1 处；② **112 个调用点行为是否不变**；③ `patch('cellpaint_pipeline.cli.<name>')` 是否仍有效 |
| F2 | 3 份 `def _native` | 收敛为 `skills/finalize.py` 一份 | 同上（25 个调用点） |
| F3 | `build_primary_outputs` fail-fast 只做一半：多传未声明键会 raise，少传必填键静默写 `null` | 必填项缺值也 raise | 构造两种输入各测一次 |
| F4 | `skills/dispatch.py` 漏 `TYPE_CHECKING` 守卫 | 已补 | 与 `context.py`/`inputs.py` 是否一致；`get_type_hints()` 是否因此能用了（**注意：正常应该仍然不能，因为 `TYPE_CHECKING` 块运行时不执行，这不是缺陷**） |
| F5 | `skills` 导入比原版慢（45.7ms/134 模块 vs 35.4ms/118） | `skills/__init__.py` 改 PEP 562 懒加载 | ① 复现导入耗时；② **`patch('cellpaint_pipeline.skills.<name>')` 是否仍有效**；③ `from ...skills import *` 是否仍可用；④ 未知属性是否抛 `AttributeError` |
| F6 | 演示产物记录的路径指向改名前的文件夹 | 已重新归一化 | 全部 manifest 路径是否可解析 |
| F7 | 公开名丢失未完整披露 | 未改代码 | 判断是否应该改代码（见 F7 的判断题） |
| F8 | `run_pipeline_skill` 仍是 37 个扁平参数 | **未修** | 确认是否仍未修；评估改与不改的取舍 |

### F7 的判断题（需要你的判断，不是核对）

第一轮建议「补回被删的公开名（至少 `cli.ProjectConfig`、`skills.ExecutionResult`）」。
但丢失的 122 个名字里绝大多数是**泄漏的 stdlib / 三方导入**（`Path`、`os`、`json`、`np`、`plt`、`dataclass`…）。
**补回去等于主动恢复命名空间污染。** 请判断：
- 哪些名字属于**真 API**（应该补回）？
- 哪些属于**历史事故**（应该写进 CHANGELOG 显式声明收窄，而不是补回）？
- 第一轮的实测已表明：57 个 `patch()` 目标里 56 个两版行为一致，唯一失效那个在基线 `59df377` 上同样失效。这对你的判断意味着什么？

---

## 5. 执行阶段

### P0 — 确认审查对象

```bash
git rev-parse HEAD                 # 期望 dd7c182...
git log --oneline -3
git status --porcelain             # 期望为空
git tag                            # 期望含 v0.1.0
```
**判定**：HEAD 不是 `dd7c182` → 停下来报告，别继续。

### P1 — 接口契约（黑盒）

两棵树都可用 git 取出：`git worktree add ../base 59df377` 与 `git worktree add ../ref dd7c182`。

逐项核对，**每项都要写出口径**：

| 检查项 | 方法 |
|---|---|
| 技能目录 | `available_pipeline_skills()` 的 **4 种开关组合**：`()`、`(include_advanced=True)`、`(include_legacy=True)`、两者都 True。期望 19 / 37 / 27 / 45 |
| 签名 | `inspect.signature(run_pipeline_skill)` 逐字段（名/kind/默认值/注解）比对，期望原 36 个全同 + 新增 1 个 |
| CLI 表面 | 内省 `build_parser()`，对每个 subparser 的每个 action 比 `option_strings/dest/required/nargs/default/choices/help/const` |
| pathlike 白名单 | `registry.pathlike_keywords()` = 16；确认基线的 MCP 侧 9 键是其真子集 |
| requires-config | 9 项逐条 |
| legacy 报错 | 实调 8 个 legacy key，比异常文本是否逐字节相同 |
| 入口映射 | `ENTRYPOINT_TARGETS` 10 条 / `RESULT_SERIALISERS` 8 条，比 `module:function` |

### P2 — 中间产物（黑盒，可离线）

跑一条**确定性链路**（不依赖网络与外部工具），两棵树各跑一遍：

```
data-plan-download → cp-build-single-cell-table → cyto-aggregate-profiles
  → cyto-annotate-profiles → cyto-normalize-profiles
  → cyto-select-profile-features → cyto-summarize-classical-profiles
```

产物做**归一化后 md5** 比对。归一化规则（**这里比 v1 完整**）：

- 绝对路径 → `<PATH>`（注意 JSON 里是转义的 `\\`，CSV 里是 `\`，两种都要覆盖）
- `generated_utc` / ISO 时间戳 → `<TS>`
- `Image.csv` 的 `ExecutionTime_*` 列（CellProfiler 自测墙钟，同一次跑两遍也不同）→ 单独列出，不算差异
- parquet 的 `Metadata_*` 路径列 → 单独列出

**判定**：归一化后应逐字节相同；有差异必须逐列诊断出「是否仅为计时/路径」。

### P3 — 函数级逻辑（白盒）

对两棵树的所有 `FunctionDef`/`AsyncFunctionDef` 做 `ast.unparse` 归一化后逐字比较。**归一化必须处理三种间接层**：

```python
_native('name')  ->  name      # skills 包
_impl('name')    ->  name      # cli 包
_lazy(...)       ->  ...       # cli 包延迟导入绑定
```

**不处理 `_impl(` 会把 112 个 CLI 调用点误判成「新增」，把 `_cmd_*` 拆分误判成「实质改写」。**

同时给出**两个口径**的数：**函数个数** 与 **调用点个数**。

### P4 — 依赖图与耦合（白盒）

用 AST 建 `src/cellpaint_pipeline/` 的模块级 import 图（区分 `TYPE_CHECKING` 块内的导入）：

- 是否存在**循环依赖**（基线应与重构版相同，期望 0）
- `reporting.py` 是否真的不再依赖 workflow 层
- 是否存在**为了类型注解而引入的运行期依赖**
- `skills/__init__.py` 的 `__getattr__` 是否让叶子模块真正成为叶子（验证 `import cellpaint_pipeline.skills.definitions` 拉了几个 `cellpaint_pipeline.*` 模块）

### P5 — 代码质量（白盒，量化）

**每个指标都必须写明口径**（目录 = `src/cellpaint_pipeline/`，行数用 `splitlines()`）：

| 指标 | 基线 59df377 | 修复前 3cc412c | 修复后 dd7c182 |
|---|---|---|---|
| 文件数 | 你测 | 你测 | 你测 |
| 源码总行 | 你测 | 你测 | 你测 |
| 最大单文件 | 你测 | 你测 | 你测 |
| >400 行文件数 | 你测 | 你测 | 你测 |
| 函数数 / 平均函数行 | 你测 | 你测 | 你测 |
| `If` 密度（每千行） | 你测 | 你测 | 你测 |
| 最大嵌套深度 | 你测 | 你测 | 你测 |
| `def _impl` / `def _native` 份数 | — | 9 / 3 | 期望 1 / 1 |
| 动态分发**份数**（`def _impl` / `def _native`） | — | 9 / 3 | 期望 1 / 1 |
| 动态分发**调用点数**（`_impl(` / `_native(` / `_lazy(`） | 90 | 你测 | 你测（**份数归 1 ≠ 成本归零**） |
| `import ...skills` 耗时/模块数 | 你测 | 你测 | 你测 |
| `import ...mcp_server` 耗时/模块数 | 你测 | 你测 | 你测 |
| pytest | 你测 | 你测 | 你测 |

**pytest 运行命令与环境前置**（第一轮因缺这个而得到与记录不同的失败数）：

```bash
pip install pytest pycytominer pandas pyarrow    # 可选依赖
python -m pytest tests -q --no-header -p no:cacheprovider
```

失败数会随可选依赖与平台变化。**关键是失败 node id 集合是否两版一致**，而不是绝对数量。

### P6 — 端到端全链（需外部工具，通常跑不了）

需要 CellProfiler 4.2 + JVM、DeepProfiler + TensorFlow、Zenodo 权重。**跑不了就按第 7 节标注。**

注意：仓库里的 `demo/workspace/outputs/`（199 个文件）**只是重构版自己的一次运行产物，
基线 `59df377` 里没有任何演示产物**。所以它只能用来做「内部自洽性」检查，
**不能**用来证明「与原版跑出来的一样」。第一轮的 v1 提示词在这里说错了。

---

## 6. 禁止事项

1. **不要把 `_cmd_*` 的拆分（`main` 855 行 → 9 个 handler）计为「实质改写」** —— 那是搬迁，不是改写。先做 `_impl` 归一化再判定。
2. **不要把「新增函数」等同于「新增复杂度」** —— 拆分必然增加函数数。要看的是平均函数长度、最大函数、分支密度。
3. **不要用绝对路径或时间戳判定产物不一致** —— 先归一化。
4. **不要把「文档少列了代码多产出的文件」当作行为差异** —— 要区分「行为变了」和「清单没列全」。
5. **不要在缺少基线的情况下说「与原版一致」** —— 说「无法判定」。
6. **不要引用本文档第 2、4 节的数字作为你自己的结论** —— 那些是待你核实的主张。

---

## 7. 无法判定协议

以下情况必须写 `无法判定` 并说明原因，**不要用推断代替实测**：

| 情况 | 你要写的 |
|---|---|
| 缺 CellProfiler / DeepProfiler / 权重 | 「阶段 P6 无法判定：缺少 X」 |
| 缺可选依赖导致测试无法收集 | 「pytest 结果无法与记录比对：缺少 X」 |
| 基线 commit 里没有对应产物 | 「无法做基线对拍：`59df377` 无产物」 |
| 网络不可达 | 「阶段 X 无法判定：网络不可达」 |

**「无法判定」不是失败**，把推断写成结论才是。

---

## 8. 输出格式

### 8.1 报告（Markdown）

```markdown
# CPC-v1 二次审查报告

## 0. 执行摘要
- 审查对象 commit / 环境 / 实际跑通了哪些阶段
- 一句话总判：第一轮的 8 条修复，修好了几条

## 1. 复现范围
| 阶段 | 状态（跑通/跳过） | 原因 |

## 2. 第一轮发现的验证结果
| # | 发现 | 结论（已修复/未修复/部分/无法判定） | 证据 |

## 3. 勘误表复核
| # | v1 说 | 你实测 | 是否同意勘误 |

## 4. 新发现（第一轮没提的）
逐条：位置(文件:行) / 复现步骤 / 实际输出 / 影响面

## 5. 代码质量量化
三列对比表（口径写清）+ 判断：更简洁 / 打平 / 更臃肿

## 6. 依赖图与耦合

## 7. 无法判定清单

## 8. 建议动作（按性价比排序）
| 优先级 | 问题 | 位置 | 建议 | 成本 | 收益 |

## 9. 总结论
1. 第一轮缺陷是否修净？
2. 是否引入了新缺陷？
3. 代码相比基线是否更简洁更优？
4. 一票：能否进主干？
```

### 8.2 机器可读摘要（JSON，方便回归对比）

```json
{
  "commit": "dd7c182",
  "stages_run": ["P0", "P1", "P2", "P3", "P4", "P5"],
  "stages_skipped": [{"stage": "P6", "reason": "no CellProfiler"}],
  "round1_findings": {
    "F1": "fixed", "F2": "fixed", "F3": "fixed", "F4": "fixed",
    "F5": "fixed", "F6": "fixed", "F7": "not-fixed", "F8": "not-fixed"
  },
  "new_findings": [{"id": "N1", "severity": "high|medium|low", "file": "path:line", "summary": "..."}],
  "metrics": {
    "skills_import_ms": 0.0, "skills_import_modules": 0,
    "mcp_import_ms": 0.0, "pytest_failed": 0, "pytest_passed": 0,
    "src_files": 0, "src_lines": 0, "max_file_lines": 0
  },
  "verdict": {"behavior_equivalent": "yes|no|partial|undetermined",
              "logic_equivalent": "yes|no|partial|undetermined",
              "code_better": "yes|no|partial|undetermined",
              "merge": "yes|no|conditional"}
}
```

---

## 9. 第二轮的已知主张（**待你核实，不是结论**）

修复者声称 `dd7c182` 达成了以下结果。**第一轮的经验表明这些数字需要全部复核。**

| 主张 | 声称值 |
|---|---|
| `def _impl` / `def _native` 份数 | 9 → **1** / 3 → **1** |
| 调用点 | `_impl(` 112、`_native(` 25（收敛前后不变） |
| `import ...skills` | 基线 35.4ms/118 模块 → 修复前 45.7ms/134 → **修复后 4.2ms/76** |
| `import ...mcp_server` | 基线 1464.7ms/1703 → 修复前 213.1ms/392 → **修复后 198.4ms/391** |
| 源码行数（`src/cellpaint_pipeline/`） | 15619 → **15538** |
| 最大单文件 | **907**（未变） |
| pytest | 13 failed / 126 passed（与修复前同一批失败） |
| 演示产物 | 199 文件；**`primary_outputs` 内** 122 条路径 0 悬空（放大到全部 53 个 JSON 是 426 条路径、24 条不可解析，均可解释：未来产物 / 后端配置回显 / `missing_script_path`） |
| patch 接缝 | 两个接缝（`skills.<native>` 与 `cli.<name>`）均仍有效 |

**特别请你挑战的 4 条**：
1. 「懒加载后 patch 接缝仍然有效」—— 用 `unittest.mock.patch` 实测，不要只看代码。
2. 「skills 导入 4.2ms」—— 独立复现，并解释**为什么**（是懒加载，还是别的）。
3. 「`_impl` 收敛后 112 个调用点行为不变」—— 抽查若干条 CLI 命令的实际行为。
4. 「演示产物 0 悬空」—— 自己遍历所有 manifest 验证。

---

## 10. 参考资料

| 资源 | 地址 |
|---|---|
| 官方原版代码 | https://github.com/Seniorious123/CellPainting-Claw （HEAD `59df377`，MIT） |
| 官方文档站 | https://cellpainting-claw.readthedocs.io/en/latest/index.html |
| 重构版（本次审查对象） | https://github.com/liuzy0543-spec/CPC-v1 |
| DeepProfiler 工具 | https://github.com/broadinstitute/DeepProfiler |
| 预训练权重 | https://zenodo.org/records/7114558 |

---

## 附：与 v1 的差异（如果你手上有 v1）

| v1 | v2 |
|---|---|
| 面向人读的说明文 | 面向 agent 执行的任务书（阶段 + 命令 + 判定） |
| 审查对象 `3cc412c` | **`dd7c182`** |
| 归一化只提 `_native` | 提 `_native` / `_impl` / `_lazy` **三者** |
| 「仓库已带产物可对拍」 | **删除**，改为明确说明基线无产物 |
| 未标口径的数字 | 每个指标强制标口径 |
| 无 pytest 命令 | 给出命令 + 可选依赖前置 |
| 无「禁止事项」 | 第 6 节 6 条 |
| 无「无法判定」协议 | 第 7 节 |
| 无机器可读输出 | 第 8.2 节 JSON |
| 只给函数数 | **函数数 + 调用点数双口径** |

---

## 11. 工具陷阱（第一轮实测踩到，务必避开）

本提示词里的归一化正则含 `[\\/]` 这类转义。**如果通过 shell heredoc 传给 Python，
反斜杠会被吞掉一层**（`[\\/]` → `[\/]`），导致 Windows 路径一条都匹配不上，
静默返回「0 条」的**假阴性**。

**任何附带的检查脚本，一律以 `.py` 文件形式给出，不要用 heredoc 内联。**

（文档结束）

