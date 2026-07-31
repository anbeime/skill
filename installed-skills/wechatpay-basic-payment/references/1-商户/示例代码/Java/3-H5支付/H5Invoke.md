# H5调起支付

> 参考官方文档：https://pay.weixin.qq.com/doc/v3/merchant/4012791835

## 调起支付步骤

1. 商户通过H5下单接口获取到发起支付的必要参数 `h5_url`
2. 商户在配置了H5支付域名的网页中跳转 `h5_url`，调起微信支付收银台中间页
3. 微信支付收银台中间页会进行H5权限的校验和安全性检查，校验通过后用户可正常支付

## 支付后返回指定页面

用户支付完成后默认返回发起支付的页面。如需返回指定页面，可在 `h5_url` 后拼接 `redirect_url` 参数：

```
h5_url=https://wx.tenpay.com/cgi-bin/mmpayweb-bin/checkmweb?prepay_id=wx20161110163838f231619da20804912345&package=1037687096&redirect_url=https%3A%2F%2Fwww.wechatpay.com.cn
```

**注意**：
- `redirect_url` 的域名必须为商户配置的H5支付域名
- 需对 `redirect_url` 进行 urlencode 处理

## 返回商户页面后查单

用户点击"取消支付"或支付成功后点击"完成"时，会返回商户支付页面（或指定的 redirect_url 页面）。建议：

在回跳页面中增设"确认支付情况"按钮，用户点击后触发查单操作，确保用户能及时了解订单状态。

> **重要**：H5支付不像JSAPI/APP有前端回调，商户必须通过后端查单接口或支付成功回调通知来确认订单状态。
