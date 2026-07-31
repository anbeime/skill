# Native调起支付

> 参考官方文档：https://pay.weixin.qq.com/doc/v3/merchant/4012791878

## 调起支付步骤

1. 通过 Native下单接口获取到发起支付的必要参数 `code_url`
2. 将 `code_url` 链接转换为二维码图片后，展示给用户
3. 用户打开微信"扫一扫"功能，扫描二维码，进行 Native 支付

## 示例

将 `weixin://pay.weixin.qq.com/bizpayurl/up?pr=NwY5Mz9&groupid=00` 生成二维码，展示给用户扫码即可。

## 注意事项

- Native 支付的 `code_url` 有效期为2小时，超时需重新调用下单接口获取新的 `code_url`
- 二维码仅支持微信"扫一扫"功能扫描，不支持长按识别或相册识别
- 商户需通过后端查单接口或支付成功回调通知来确认订单状态，不能仅依赖用户告知
