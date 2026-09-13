# 现场照片收货异常：Microsoft / Oracle 官方能力核查

访问日：2026-09-13（Pacific）。范围仅限六份厂商一手文档；没有登录竞品租户，也没有测准确率、时延、许可价格或实施成本。因此，“未证明”只表示这些页面没有证明该组合是开箱即用，**不是**对整个产品线或伙伴生态的不存在断言。

## 结论

微软和 Oracle 都已经提供收货时的原生质检、库存隔离或收货单据创建能力；Azure Vision 与 OCI Vision 也能成为照片分析的技术部件。现有材料没有证明任一厂商把“照片观察 → 由操作员关联到 ERP 批次 → 按客户承诺比较发运方案 → 人批准精确动作 → 执行后读回原生单据”作为同一个、无需集成的标准小分销商流程。

这不构成产品空白或竞争优越性的证明。LogisticPilot 应把自己的主张限制为：在一个明确的 ERPNext 分销场景中，照片只形成可复核的异常线索，库存数量和质量状态仍以 ERP 为准，人批准后才执行并读取结果。

## 已确认能力与边界

| 厂商能力 | 可用性口径 | 官方文档实际证明 | 对照片异常闭环的边界 |
| --- | --- | --- | --- |
| Dynamics 365 Supply Chain Management：Quality associations | **原生产品配置** | 可按采购、入库、销售或生产事件自动生成质量单；关联记录定义检验、AQL 和抽样计划。质量单未关闭时，库存会自动阻止发料；`Full blocking` 决定阻止质量单数量还是来源单据行数量。[Microsoft：Quality associations](https://learn.microsoft.com/en-us/dynamics365/supply-chain/inventory/quality-associations) | 页面没有说明照片模型会识别 ERP 批次、把视觉结论写入质量单，或连同客户承诺、运费方案和批准一并处理。 |
| Dynamics 365 Supply Chain Management：Quality check | **原生仓储功能，人工判定** | 收货人员扫描 license plate 后，对包装或容易识别的部件作快速目检并录入 pass/fail；失败会转至替代地点并创建质量单。模板可设为 `Prompt user` 或自动拒绝，且可配置创建质量单。[Microsoft：Quality check](https://learn.microsoft.com/en-us/dynamics365/supply-chain/warehousing/quality-check) | 这与“发现包装损伤后不要把货直接放行”的操作相近，但文档描述的是人员记录的 pass/fail，不是照片推理。license plate/序列等维度能否带入质量单也取决于抽样配置，不能把图片文字当成身份确定性。 |
| Azure Vision Image Analysis | **独立 Azure 平台服务；需集成** | Image Analysis 可通过 SDK 或 REST 调用，提供 OCR、caption、dense caption、tag、object detection 等视觉特征。文档同时说明 4.0 已弃用、将于 2028-09-25 退役；其 4.0 custom classification / custom object detection / product recognition preview 已于 2025-03-31 退役，文档建议迁移到 Azure AI Custom Vision。[Microsoft：Image Analysis 概览](https://learn.microsoft.com/en-us/azure/ai-services/computer-vision/overview-image-analysis) | 这证明有照片分析组件，不证明它天然了解 D365/任意 ERP 的批次、可用数量、质量政策或发运合同。以该版本作为长期基础还必须处理厂商给出的迁移约束。 |
| Oracle Fusion Cloud SCM：Receiving + Quality Management | **原生产品配置** | 启用 `Use quality inspection plan` 后，若收货行的 item 与 supplier 有适用检验计划，收货会进入 Quality Management UI；未启用时可作简单 pass/fail。收货时还可按设置覆盖路由目的地。[Oracle：Receipts and Quality Management](https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26b/fauqm/when-do-receipts-go-through-quality-management-for-quality.html) | 这是收货质检与路由的原生基础，但该页面没有给出照片/OCI Vision 输入、视觉结论到批次身份的绑定，或质量结论如何驱动客户订单的成本比较和人审发运。 |
| OCI Vision custom models | **独立 OCI 平台服务；需训练与集成** | 自定义 image classification / object detection 模型需要付费 OCI tenancy、Object Storage 知识和策略；使用项目、标注数据集及训练流程。推荐训练最长可达 24 小时，quick training 约一小时。[Oracle：Building a Custom Model](https://docs.oracle.com/en-us/iaas/Content/vision/using/custom_model_build.htm) | 这可以是包装/标签类视觉模型的候选技术部件。从 OCI Vision 与 Fusion Receiving 的分别文档只能推出需要架构集成；未证明 Fusion 收货质量流程原生接收其预测、自动决定整批质量或自动出货。 |
| Oracle Fusion：Receipt Creation Assistant | **预配置 Agent Studio 模板，仍需启用角色与权限** | 用户把 delivery-confirmation email 内容粘入聊天框，助手可为 PO、转移、ASN、RMA 等创建收货，支持 lot/serial 控制物料；成功后显示单据、行、数量、lot/serial，并可进入 Received Lines、摘要及交易历史。文档列出启用、Agent Studio 和收货权限要求。[Oracle：Receipt Creation Assistant](https://docs.oracle.com/en/cloud/saas/readiness/scm/26a/inv26a/26A-inventory-wn-f41429.htm) | 它证明 Oracle 有“辅助创建收货并读回单据”的产品路径，但输入是粘贴的交付确认邮件，不是现场照片；该说明也没有把视觉异常、质量隔离、合同发运选项和人工批准串成同一流程。 |

## 对当前分销商闭环的含义

| 工作环节 | LogisticPilot 应保持的事实边界 | 以上资料可支持的相邻能力 |
| --- | --- | --- |
| 照片观察 | 模型只报告可见损伤、可读标签或需要重拍等观察；不从未校准照片推出尺寸、批次身份、整批缺陷或实际数量。 | D365 的 Quality check 已把包装等明显外观列为人工快速检查对象；Azure/OCI 分别提供通用或自训视觉部件。 |
| ERP 关联和隔离 | 由操作员选择并验证当前配置的 lot；图片是证据附件，ERP 的现存量、批次状态与质检规则才决定是否 hold。 | D365 可将 quality order 关联到来源和受配置控制的维度，并阻止库存；Fusion 可按 item/supplier 的检验计划把收货引至质检。 |
| 合同发运比较和批准 | 只对当前 ERP 可执行的数量生成精确 proposal；证据、合同、时间或库存变动须使旧 proposal 失效；人批准才产生原生写入。 | 本次六页没有证明这个交叉环节在任一厂商中以照片驱动、合同感知的开箱组合出现。不能由此断言厂商或其伙伴没有实现。 |
| 原生执行与读回 | 显示 Pick / Delivery / Shipment 等实际单据和数量；没有写入就不能称已执行。 | Oracle Receipt Creation Assistant 已展示收货创建后的行、批次/序列与交易历史入口。此处没有竞品实测，不能比较成功率或速度。 |

## 架构与伙伴口径

- **原生产品**：D365 的质量关联和仓库质量检查、Fusion 的收货质检，以及 Oracle 的收货助手都有明确产品文档；它们不应被描述成“竞争者没有”。
- **平台服务**：Azure Vision 与 OCI Vision 是视觉能力来源，文档所示的调用、训练、策略和数据集要求意味着仍要把模型结果、ERP 身份、质量规则与权限接起来。
- **架构工作**：把照片 digest/观察绑定到操作员确认的 lot，保持 ERP 为数量与质量权威，将合同/成本建议锁定到可审的 revision，并在批准后读回原生单据，是本 demo 要实际展示的集成边界；不是从上述单页可推得的厂商标准功能。
- **伙伴方案**：本轮未检索或验证任何 Microsoft/Oracle ISV、SI 或 marketplace 实现，因此不把“伙伴可以做”计入原生能力，也不以未列出伙伴方案作反向结论。

对小分销商的比较应聚焦同一异常能否少查一次账、少误放一批货、且让批准与执行事实可复核。没有同一任务的竞品租户实测、费用和实施数据，不应声称 LogisticPilot 比 Microsoft 或 Oracle 更便宜、更快或更准确。
