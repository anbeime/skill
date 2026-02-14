# Output Language Guide

Use the **contract’s dominant language** for all outputs: comment labels, summary headings, opinion text, and flowchart node text.

## Language Selection Rules

1. **Detect dominant language** by character ratio in the contract body:
   - If Chinese (CJK) characters are the clear majority (≈60%+), use Chinese.
   - If Latin letters are the clear majority (≈60%+), use English.
2. **If bilingual**, follow the language used in section headings/titles.
3. **If still ambiguous**, ask the user; if no response, default to English.

**Do not mix languages** within the same output.

## Comment Label Mapping

**English**
- `[Issue Type]`
- `[Risk Reason]`
- `[Revision Suggestion]`

**Chinese**
- `【问题类型】`
- `【风险原因】`
- `【修订建议】`

## Summary Heading Mapping (Chinese)

When the contract is Chinese, use these headings/labels exactly:

- `一、合同基本信息`
  - `项目` / `内容`
  - `合同名称` / `合同类型` / `合同当事人` / `签订时间` / `合同期限` / `合同金额`
- `二、业务模式概述`
  - `简要描述：...`
- `三、核心条款要素`
  - `3.1 交易要素`
    - `要素` / `具体内容`
    - `标的物/服务内容` / `数量规格` / `价格构成` / `支付方式` / `交付方式`
  - `3.2 权利义务分配`
    - `甲方主要权利义务：...`
    - `乙方主要权利义务：...`
  - `3.3 履行保障条款`
    - `条款类型` / `具体约定`
    - `违约责任` / `担保措施` / `验收标准` / `质量保证`
  - `3.4 风险分担与特殊约定`
    - `风险分担：...`
    - `特殊约定：...`
  - `3.5 争议解决与合同终止`
    - `项目` / `约定内容`
    - `争议解决方式` / `合同变更` / `合同解除` / `适用法律`
- `四、关键时间节点`

## Opinion Wording (Chinese)

For the second paragraph, use a lead-in similar to:
- `经审核，本合同存在以下几项主要风险需提请关注：`

Then list numbered items in separate paragraphs.
