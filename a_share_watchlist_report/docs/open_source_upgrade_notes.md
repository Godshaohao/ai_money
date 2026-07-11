# 开源项目调研与吸收记录

日期：2026-07-11

本项目定位是个人 A 股投研复核工作台，不做自动交易、不输出买卖建议、不引入预测型 AI。开源项目只吸收工程结构、数据契约和可复核展示方式。

## 调研对象

- AKShare: https://github.com/akfamily/akshare
  - 借鉴点：一行取数、接口简单、明确提示数据风险。
  - 落地方式：继续保留 AKShare / EastMoney 作为当前主数据源，在 UI 中显式展示数据源状态、缓存降级和数据质量缺口。

- Microsoft Qlib: https://github.com/microsoft/qlib
  - 借鉴点：数据、模型、策略、分析松耦合；研究流程分阶段组织。
  - 落地方式：工作台新增“数据链路契约”，把数据获取、规格化、质量检查、策略复核、人工复盘分成可检查阶段。

- ZVT: https://github.com/zvtvz/zvt
  - 借鉴点：增量数据更新、历史数据复用、不同 provider 的稳定性设计。
  - 落地方式：当前不新增第二数据源，但显式展示本地缓存降级；后续如要增加 provider，必须先抽象 provider contract 和 provenance 字段。

- RQAlpha: https://github.com/ricequant/rqalpha
  - 借鉴点：模块化策略/分析器输出，可替换、可扩展。
  - 落地方式：策略详情从标签 chip 升级为“历史策略复核明细”，展示每条候选的日期、原因、风险标签和分项分数。

- vn.py: https://github.com/vnpy/vnpy
  - 借鉴点：交易系统中的清晰模块边界和事件/组件化思路。
  - 落地约束：本项目不接券商、不下单，只借鉴模块边界，不吸收交易执行模块。

## 本轮已落地

1. 工作台新增“数据链路契约”面板：
   - 数据源：AKShare / EastMoney
   - 数据源状态：实时接口正常 / 本地缓存降级 / 数据质量待复核
   - 阶段：数据获取、规格化、质量检查、策略复核、人工复盘
   - 指标：涨停复核数、排除股票数、警告数、产物数

2. 个股详情页策略模块升级：
   - 从“策略标签”改为“历史策略复核明细”
   - 展示每条历史涨停复核的日期、模块、标签、总分、原因、风险标签
   - 展示市场环境、涨停强度、连板分、封板质量、流动性、隔夜风险、数据质量等分项

## 明确不吸收

- 不吸收 Qlib 的机器学习预测、强化学习、组合优化。
- 不吸收 vn.py 的券商连接、订单、撮合、实盘交易。
- 不吸收 RQAlpha 的回测交易语义作为当前产品输出。
- 不把 WATCH_REVIEW / CORE_REVIEW 解释成买卖建议。

## 下一轮建议

优先做 provider contract，不急着接新数据源：

- `provider_name`
- `provider_endpoint`
- `requested_at`
- `status`
- `error_message`
- `cache_used`
- `row_count`
- `latest_trade_date`

这样后续无论继续用 AKShare，还是接入其他开源数据方案，都能保持同一套数据契约。
