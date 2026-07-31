# JSAPI 调起支付

> 服务商模式与商户模式的调起支付代码完全一致，区别仅在于 `appId` 的取值：
> - 在服务商的公众号/网页中调起支付时，`appId` 传 `sp_appid`
> - 在子商户的公众号/网页中调起支付时，`appId` 传 `sub_appid`

```javascript
function onBridgeReady() {
    WeixinJSBridge.invoke('getBrandWCPayRequest', {
        "appId": "wxYOUR_APPID",     //公众号ID，由商户传入     
        "timeStamp": "1395712654",     //时间戳，自1970年以来的秒数     
        "nonceStr": "e61463f8efa94090b1f366cccfbbb444",      //随机串     
        "package": "prepay_id=wx21201855730335ac86f8c43d1889123400",
        "signType": "RSA",     //微信签名方式：     
        "paySign": "oR9d8PuhnIc+YZ8cBHFCwfgpaK9gd7vaRvkYD7rthRAZ\/X+QBhcCYL21N7cHCTUxbQ+EAt6Uy+lwSN22f5YZvI45MLko8Pfso0jm46v5hqcVwrk6uddkGuT+Cdvu4WBqDzaDjnNa5UK3GfE1Wfl2gHxIIY5lLdUgWFts17D4WuolLLkiFZV+JSHMvH7eaLdT9N5GBovBwu5yYKUR7skR8Fu+LozcSqQixnlEZUfyE55feLOQTUYzLmR9pNtPbPsu6WVhbNHMS3Ss2+AehHvz+n64GDmXxbX++IOBvm2olHu3PsOUGRwhudhVf7UcGcunXt8cqNjKNqZLhLw4jq\/xDg==" //微信签名 
    },
    function(res) {
        if (res.err_msg == "get_brand_wcpay_request:ok") {
            // 使用以上方式判断前端返回,微信团队郑重提示：
            //res.err_msg将在用户支付成功后返回ok，但并不保证它绝对可靠，商户需进一步调用后端查单确认支付结果。
        }
    });
}
if (typeof WeixinJSBridge == "undefined") {
    if (document.addEventListener) {
        document.addEventListener('WeixinJSBridgeReady', onBridgeReady, false);
    } else if (document.attachEvent) {
        document.attachEvent('WeixinJSBridgeReady', onBridgeReady);
        document.attachEvent('onWeixinJSBridgeReady', onBridgeReady);
    }
} else {
    onBridgeReady();
}
```
