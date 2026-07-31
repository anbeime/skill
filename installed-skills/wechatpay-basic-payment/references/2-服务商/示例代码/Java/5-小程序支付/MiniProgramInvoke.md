# 小程序调起支付

> 服务商模式与商户模式的小程序调起支付代码完全一致，区别仅在于签名使用的 `appid`：
> - 在服务商小程序中调起支付时，签名用 `sp_appid`
> - 在子商户小程序中调起支付时，签名用 `sub_appid`
>
> 微信支付会校验下单与调起支付所使用的 `appid` 的一致性。

## 请求示例

```javascript
wx.requestPayment(
  {
    "timeStamp": "1414561699",
    "nonceStr": "5K8264ILTKCH16CQ2502SI8ZNMTM67VS",
    "package": "prepay_id=wxYOUR_PREPAY_ID",
    "signType": "RSA",
    "paySign": "oR9d8PuhnIc+YZ8cBHFCwfgpaK9gd7vaRvkYD7rthRAZ\/X+QBhcCYL21N7cHCTUxbQ+EAt6Uy+lwSN22f5YZvI45MLko8Pfso0jm46v5hqcVwrk6uddkGuT+Cdvu4WBqDzaDjnNa5UK3GfE1Wfl2gHxIIY5lLdUgWFts17D4WuolLLkiFZV+JSHMvH7eaLdT9N5GBovBwu5yYKUR7skR8Fu+LozcSqQixnlEZUfyE55feLOQTUYzLmR9pNtPbPsu6WVhbNHMS3Ss2+AehHvz+n64GDmXxbX++IOBvm2olHu3PsOUGRwhudhVf7UcGcunXt8cqNjKNqZLhLw4jq\/xDg==",
    "success":function(res){},
    "fail":function(res){},
    "complete":function(res){}
  }
)
```

## 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| `timeStamp` | 是 | 时间戳（秒级，10位数字） |
| `nonceStr` | 是 | 随机字符串，不长于32位 |
| `package` | 是 | 预支付交易会话标识，格式：`prepay_id=***` |
| `signType` | 是 | 固定为 `RSA` |
| `paySign` | 是 | 使用 `appid`、`timeStamp`、`nonceStr`、`package` 计算的签名值 |

## 回调结果

| 回调类型 | errMsg | 说明 |
|---------|--------|------|
| success | `requestPayment:ok` | 调用支付成功 |
| fail | `requestPayment:fail cancel` | 用户取消支付 |
| fail | `requestPayment:fail (detail message)` | 调用支付失败，detail message 为详细原因 |

> ⚠️ 前端回调不绝对可靠，订单状态需以后端查询订单和支付成功回调通知为准。
> 若为交易类小程序，需满足《交易类小程序运营规范》并接入订单发货管理功能，否则可能被限制支付权限。
