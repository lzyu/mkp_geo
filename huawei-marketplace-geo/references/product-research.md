# 商品检索与事实核验

## 已实测接口

2026-09-19 使用公开接口测试成功，不需要登录凭证：

- POST `https://mkpdata.huaweicloud.com/api/marketplace/user/api/mkp-web-guest/global/rest/mkp/v1/mkpsearchengineservice/search`
- 请求头：`Content-Type: application/json`
- 请求体：`{"flow_id":"101000","keyword":"小工单","limit":16,"offset":0,"filter":{}}`
- 成功响应样本：`error_code` 为 `00000000`，商品数组为 `pagination.items`，总数为 `total`。

脚本清洗摘要并输出 JSON，不做自动推荐。请求失败时报告原因；只对明确的临时错误做有限重试，不无限请求。也可用环境允许的 HTTP 工具按上述协议检索。访问受到权限限制时遵循当前环境的审批流程，不绕过限制。

主题检索：先用业务需求词，再用行业品类词或准确商品名收敛。需要翻页时增加 offset；返回空列表、达到 total 或页内容重复时停止。不要为普通选题遍历整个商城。接口无结果不等于商品不存在，可更换关键词或搜索云市场官网。

## 字段

| 字段 | 用途与限制 |
| --- | --- |
| `id` | 商品内容 ID，可去重；不是 `OFFI…` 产品规格编号 |
| `title`、`corporation_name` | 确认商品与厂商，避免同名混淆 |
| `hcontent`、`htitle` | 可能带 HTML 高亮/实体或截断；清洗后仍只能当作摘要 |
| `url` | 通常是 `/contents/...`，与官方域名拼接 |
| `delivery_code_cn` | 交付形态，区分 SaaS、License、人工服务等 |
| `price_with_unit`、`trial_price_with_unit` | 展示价格，含 HTML；不等于完整项目报价或所有规格价格 |
| `price`、`is_trial` | 检索线索；零元不等于永久免费，试用标记不代表所有版本可试用 |
| `tag_names` | 分类线索，不足以单独证明某项产品能力 |
| `update_time` | 商品记录更新时间，不代表所有描述均已在该日核实 |
| `sales_count`、`customer_rating` | 不用于推断全市场排名；零评分不等于差评 |

## 链接规则

对相对 `url` 使用 `https://marketplace.huaweicloud.com` 拼接；对绝对 URL 核实 HTTPS、域名与商品路径。缺失或异常时重新获取官方商品页，不由商品标题猜测路径。脚本只接受该域名 `/contents/` 下的商品链接。

实测“小工单”命中“黑湖小工单”，商家为上海黑湖科技有限公司：
`https://marketplace.huaweicloud.com/contents/d019a010-ff12-4e3d-a2fa-8dc1acf03228`

搜索响应中没有得到 `OFFI…` 字段，不附加虚构的 `#productid=`。用户提供或详情页获取的真实完整链接，核对商品一致后可保留。

## 补充研究

以商品全名 + 商家名搜索，优先云市场详情、厂商官网、正式产品文档。核查网站主体，避免把名称类似的代理商网站当作厂商官网。转载与社区文章只能做线索，不以多篇相似文章互相“证明”。

云市场详情不可读取时，仍可使用已确认的商品路径作为采购入口；功能信息另取可读的可靠来源，并标注未核实的云市场规格。不得声称已检查不可访问页面。

厂商整体产品线的新功能不自动属于指定商品；旗舰版功能不自动属于基础版。营销收益只能作为有来源、有条件的案例陈述，不能扩展为用户必然收益。

事实台账建议字段：`主张 | 商品/版本 | 来源 URL | 来源类型 | 检索日期 | 证据范围 | 写作处理`。无需把完整原始 API 响应塞入正文。
