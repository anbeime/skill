# H5 调起支付

> 服务商模式与商户模式的 H5 调起支付完全一致。

## 调起步骤

1. 服务商通过 H5 下单接口获取 `h5_url`
2. 在配置了 H5 支付域名的网页中跳转 `h5_url`，调起微信支付收银台中间页
3. 微信支付收银台进行 H5 权限校验和安全性检查，校验通过后用户正常支付

## 支付后返回指定页面

用户支付完成后默认返回发起支付的页面。如需返回指定页面，在 `h5_url` 后拼接 `redirect_url` 参数：

```
h5_url=https://wx.tenpay.com/cgi-bin/mmpayweb-bin/checkmweb?prepay_id=wx20161110163838f231619da20804912345&package=1037687096&redirect_url=https%3A%2F%2Fwww.wechatpay.com.cn
```

> `redirect_url` 的域名必须为商户配置的 H5 支付域名，且需对 `redirect_url` 进行 urlencode 处理。

## 返回商户 H5 页面后查单

用户点击"取消支付"或支付成功后点击"完成"时，会返回服务商的支付页面（或指定的 `redirect_url` 页面）。建议在回跳页面中增设"确认支付情况"按钮，用户点击后触发查单操作，确保及时了解订单状态。
