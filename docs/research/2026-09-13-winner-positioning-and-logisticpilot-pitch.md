# LogisticPilot：让评委先听懂，再看到价值

研究日期：2026-09-13。范围是一句话定位与演示叙事，不是新增功能规格。

## 推荐定位

**LogisticPilot 是小型分销商的 AI 跟单员，帮你处理到货异常，让订单继续走、少花冤枉钱。**

English: **An AI teammate for small distributors that resolves receiving problems, keeps orders moving, and helps avoid unnecessary costs.**

这是建议的产品定位；其中降低费用是待演示验证的价值主张，不代表已经取得真实客户节省。第一句话交代用户、工作和结果，不塞入 ERP、批次编号、模型名称或 multi-agent 架构。

随后用一句话解释具体场景：

> 货少了、坏了，老板不用自己翻单据、查库存、反复协调；Agent 查清影响，比较处理方案，经你批准后执行，并核对结果。

这句描述目标演示。当前已验证的履约执行与读回可以支撑其中一部分；经济方案比较仍需接入验证，不能把目标描述当成已完成清单。

## 往届获奖作品实际怎么讲

本届 Agents for Humans 尚未评奖。这里参考的是上一场 AWS AI Agent Global Hackathon，不能称为本届的往年冠军，也不能断言某句文案导致获奖。[主办方获奖公告](https://aws-agent-hackathon.devpost.com/updates/38140-congratulations-to-the-winners-of-the-aws-ai-agent-global-hackathon)确认以下奖项。

以下为自己的中文概括，不是作品原文翻译引语：

| 作品与奖项 | 一听就懂的任务／结果 | 可借鉴之处 |
|---|---|---|
| [EcoLafaek](https://devpost.com/software/ecolafaek)，第一名 | 居民拍摄垃圾，AI 帮管理者识别污染热点、安排治理优先级 | 有明确的地方、受益人和可见问题；其短口号强调守护当地环境，没有量化财务 ROI。不要把规划中的清理结果追踪算成已实现能力。 |
| [AegisAgent](https://devpost.com/software/aegisagent-an-insurance-claim-app-fully-developed-by-kiro)，第二名 | 把人工保险理赔审核变成可解释的证据、保单与合规审查 | 先给出熟悉的职业任务；多 agent 是分工手段。页面呈现 POC，不能等同于已经自动赔款。 |
| [Province](https://devpost.com/software/province)，第三名 | 用户通过对话和上传税务资料完成报税准备 | 让人立即理解从复杂手续到可用结果；经济门槛是辅助理由。 |
| [AgentShell](https://devpost.com/software/agent-shell)，最佳 Strands SDK 实现 | 用廉价可转动摄像头，让云端 agent 看、听、说并控制视角 | 清楚的硬件成本对比有助于呈现价值；成本优势是作者主张，不是独立验证的客户 ROI。 |

Province 与 AgentShell 的短原文摘录、费用主张归属见[来源笔记](2026-09-13-winner-tagline-source-notes.md)。

结论不是“获奖作品都有一句完美口号”或“必须展示巨大节省金额”。这些作品的原始介绍有的也很技术化。值得学习的是：读完场景后，评委能知道谁原本在做什么困难工作，以及 agent 带来了什么可见变化。

[本届官方说明](https://agentsforhumans.devpost.com/)强调用 Strands 处理重复工作；Professional Agents 明确包含小企业经营者，要求解释问题、服务对象和意义。AI 跟单员因此比泛化的供应链智能平台更贴近这次主题。

## 演示必须兑现的三件事

1. **问题有代价：** 一笔订单因到货异常面临延误或额外费用。用订单、到货记录和约定说明影响，不能仅靠红色警报制造紧张感。
2. **Agent 改变处理方式：** 它跨单据查证，找出仍能履约的部分，比较满足约定的方案。展示选择依据、缺失条件和必要的人类决定。
3. **行动有结果：** 批准后真实执行并读回；展示订单推进了多少、哪些风险仍未解除，以及采用相同口径计算的费用差额。

合成订单、合同与费用输入适合 POC，明确标注即可。模型调用、运算、ERP 操作和读回必须真实；金额标注为演示场景估算，不能说成真实客户已经省下的钱。

目前的 [LP-POC-COST-01 证据包](../demo-data/economic-poc/README.md)估算少寄一箱可减少 $24.80 邮费，适合作为计算与条件验证输入。**这笔小差额本身不足以担当主故事。** 主故事应是受影响订单如何继续履约；成本比较给它提供可核对的经济证据。不能把订单金额、潜在损失和节省邮费相加包装成收益。

## 文案边界

- 不写“首个”“保证准时交付”“自主解决所有供应链问题”或未经测量的效率倍数。
- 不靠把场景扩展到所有行业获得规模感。先证明一类小分销商的重复工作，再说明其他 ERP／行业适配仍需验证。
- 不把技术名词当作首页卖点。Strands、多 agent、evidence 与 readback 放在演示中证明为何这项工作值得交给 agent。
- 下一步投入应优先兑现这段故事，不因本研究增加 UI 单元测试、企业级配置或更多无关指标。

## 当前交付范围

本次仅完成定位研究与推荐文案；没有更改应用、Devpost 在线提交或经济方案执行逻辑。
