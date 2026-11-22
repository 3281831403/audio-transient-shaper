# audio-transient-shaper

## 题面

给鼓组加瞬态整形后，打击感没变强、整体却开始削顶：包络用均值，瞬态被抹平；攻击与释放共用同一时间常数，释放太慢；上升沿用绝对阈值，响度变化就失效；增益段不按 width 扩展，只有单样本；软膝不生效，增益跳变；施加后不钳制，削顶；灵敏度越界不校验，检测不到；amount 超过 1 不钳制，反相；批量共用包络，轨之间串；width_ms=0 不校验，除零。transient/shaper.py 是核心，tests/test_shaper.py 15个红。要修的是：峰值包络与分离的攻击/释放时间常数、相对上升沿检测、按宽度扩展的增益段、软膝、输出钳制、灵敏度与 amount 校验、批量隔离、width_ms 校验。

## 运行方式

在仓库根目录执行：

```powershell
cd D:\gsb-20261119\audio-transient-shaper
python -m pytest tests -q
```

初始状态必须恰好是：

```text
15 failed
```

且没有 collection error、import error 或 syntax error；15 个失败都应来自尚未实现的桩（`NotImplementedError`）。

## 字段表

| 字段 | 取值 |
| --- | --- |
| 所属领域 | 游戏、图形与多媒体 |
| 子方向 | 音视频处理 |
| 任务类型 | Bugfix |
| 语言/框架 | Python 3, pytest |
| 环境可复现等级 | 无外部依赖 |

## 约束

- 只用 Python 标准库（`math`）与 pytest；离线运行，不使用随机数，不调用 `sleep`。
- 音频统一使用 `list[float]`，标称样本范围为 `-1.0..1.0`；数值断言容差为 `1e-6`。
- 8 个公开函数当前都是 `raise NotImplementedError` 的桩，契约写在各自的 docstring 中。
- `tests/test_shaper.py` 是验收契约，**不可修改**；实现不得改变测试期望。
