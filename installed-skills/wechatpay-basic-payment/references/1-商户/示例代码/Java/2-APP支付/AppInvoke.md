# APP调起支付

> 参考官方文档：https://pay.weixin.qq.com/doc/v3/merchant/4013070351

## 说明

商户通过APP下单接口获取到发起支付的必要参数 `prepay_id` 后，商户APP再通过 OpenSDK 的 `sendReq` 方法拉起微信支付。

**注意**：需严格遵循 OpenSDK 接入指引（[Android](https://developers.weixin.qq.com/doc/oplatform/Mobile_App/Access_Guide/Android.html) / [iOS](https://developers.weixin.qq.com/doc/oplatform/Mobile_App/Access_Guide/iOS.html) / [鸿蒙](https://developers.weixin.qq.com/doc/oplatform/Mobile_App/Access_Guide/ohos.html)）接入SDK以及配置开发环境。

## 请求参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `appId` | 是 | 下单时传入的应用ID |
| `partnerId` | 是 | 下单时传入的商户号 |
| `prepayId` | 是 | APP下单接口返回的 prepay_id，有效期2小时 |
| `packageValue` | 是 | 固定值 `Sign=WXPay`（iOS 中字段名为 `package`） |
| `nonceStr` | 是 | 随机字符串，不长于32位 |
| `timeStamp` | 是 | Unix 秒级时间戳 |
| `sign` | 是 | 使用 appId、timeStamp、nonceStr、prepayId + 商户API证书私钥生成的 RSA 签名 |

## iOS 示例代码

```objectivec
PayReq *request = [[[PayReq alloc] init] autorelease];
request.appId = "wxd930ea5d5a258f4f";
request.partnerId = "1900000109";
request.prepayId= "1101000000140415649af9fc314aa427",;
request.package = "Sign=WXPay";
request.nonceStr= "1101000000140429eb40476f8896f4c9";
request.timeStamp= "1398746574";
request.sign= "oR9d8PuhnIc+YZ8cBHFCwfgpaK9gd7vaRvkYD7rthRAZ\/X+QBhcCYL21N7cHCTUxbQ+EAt6Uy+lwSN22f5YZvI45MLko8Pfso0jm46v5hqcVwrk6uddkGuT+Cdvu4WBqDzaDjnNa5UK3GfE1Wfl2gHxIIY5lLdUgWFts17D4WuolLLkiFZV+JSHMvH7eaLdT9N5GBovBwu5yYKUR7skR8Fu+LozcSqQixnlEZUfyE55feLOQTUYzLmR9pNtPbPsu6WVhbNHMS3Ss2+AehHvz+n64GDmXxbX++IOBvm2olHu3PsOUGRwhudhVf7UcGcunXt8cqNjKNqZLhLw4jq\/xDg==";
[WXApi sendReq：request];
```

## Android 示例代码

```java
IWXAPI api;
PayReq request = new PayReq();
request.appId = "wxd930ea5d5a258f4f";
request.partnerId = "1900000109";
request.prepayId= "1101000000140415649af9fc314aa427",;
request.packageValue = "Sign=WXPay";
request.nonceStr= "1101000000140429eb40476f8896f4c9";
request.timeStamp= "1398746574";
request.sign= "oR9d8PuhnIc+YZ8cBHFCwfgpaK9gd7vaRvkYD7rthRAZ\/X+QBhcCYL21N7cHCTUxbQ+EAt6Uy+lwSN22f5YZvI45MLko8Pfso0jm46v5hqcVwrk6uddkGuT+Cdvu4WBqDzaDjnNa5UK3GfE1Wfl2gHxIIY5lLdUgWFts17D4WuolLLkiFZV+JSHMvH7eaLdT9N5GBovBwu5yYKUR7skR8Fu+LozcSqQixnlEZUfyE55feLOQTUYzLmR9pNtPbPsu6WVhbNHMS3Ss2+AehHvz+n64GDmXxbX++IOBvm2olHu3PsOUGRwhudhVf7UcGcunXt8cqNjKNqZLhLw4jq\/xDg==";
api.sendReq(request);
```

## 鸿蒙示例代码

```typescript
IWXAPI api;
let req = new wxopensdk.PayReq
req.appId = 'wxd930ea5d5a258f4f'
req.partnerId = '1900000109'
req.prepayId = '1101000000140415649af9fc314aa427'
req.packageValue = 'Sign=WXPay'
req.nonceStr = '1101000000140429eb40476f8896f4c9'
req.timeStamp = '1398746574'
req.sign = 'oR9d8PuhnIc+YZ8cBHFCwfgpaK9gd7vaRvkYD7rthRAZ\/X+QBhcCYL21N7cHCTUxbQ+EAt6Uy+lwSN22f5YZvI45MLko8Pfso0jm46v5hqcVwrk6uddkGuT+Cdvu4WBqDzaDjnNa5UK3GfE1Wfl2gHxIIY5lLdUgWFts17D4WuolLLkiFZV+JSHMvH7eaLdT9N5GBovBwu5yYKUR7skR8Fu+LozcSqQixnlEZUfyE55feLOQTUYzLmR9pNtPbPsu6WVhbNHMS3Ss2+AehHvz+n64GDmXxbX++IOBvm2olHu3PsOUGRwhudhVf7UcGcunXt8cqNjKNqZLhLw4jq\/xDg=='
api.sendReq(context: common.UIAbilityContext, req)
```

## 回调 errCode 说明

| errCode | 描述 | 商户APP处理方案 |
|---------|------|---------------|
| 0 | 成功 | 调用后端查单接口，订单已支付则展示支付成功页面 |
| -1 | 错误 | 可能原因：签名错误、未注册AppID、AppID不匹配等 |
| -2 | 取消支付 | 用户取消支付返回App，商户自行处理展示 |

> **重要**：前端回调不保证绝对可靠，不可只依赖前端回调判断订单支付状态，订单状态需以后端查询订单和支付成功回调通知为准。
