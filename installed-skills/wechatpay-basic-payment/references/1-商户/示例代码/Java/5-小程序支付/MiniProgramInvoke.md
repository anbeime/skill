# 小程序调起支付

## 说明

商户通过JSAPI/小程序下单接口获取到发起支付的必要参数 `prepay_id` 后，在小程序中通过 `wx.requestPayment` 调起微信支付收银台。

小程序和JSAPI共用同一个下单接口（`/v3/pay/transactions/jsapi`），区别在于调起支付的前端方式不同：小程序用 `wx.requestPayment`，JSAPI 用 `WeixinJSBridge`。

## 示例代码

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

> **重要**：前端回调不保证绝对可靠，商户需通过后端查单接口或支付成功回调通知来确认订单状态。
