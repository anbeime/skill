# Api

*2 pages in this category*

## Table of Contents

1. [基础](#1-基础)
2. [微信开放文档 / 服务端](#2-微信开放文档-/-服务端)

---

## 1. 基础

**Source**: [https://developers.weixin.qq.com/miniprogram/dev/api/](https://developers.weixin.qq.com/miniprogram/dev/api/)

以下服务端接口可免 access_token 调用的场景：使用微信云托管通过微信令牌/开放接口服务调用；使用微信云开发通过云函数免服务器发起云调用。  

基础

	名称	功能
	wx.env	环境变量
	wx.canIUse	判断小程序的API，回调，参数，组件等是否在当前版本可用
	wx.base64ToArrayBuffer	将 Base64 字符串转成 ArrayBuffer 对象
	wx.arrayBufferToBase64	将 ArrayBuffer 对象转成 Base64 字符串
	系统	
	
	名称	功能
	wx.openSystemBluetoothSetting	跳转系统蓝牙设置页
	wx.openAppAuthorizeSetting	跳转系统微信授权管理页
	wx.getWindowInfo	获取窗口信息
	wx.getSystemSetting	获取设备设置
	wx.getSystemInfoSync	wx.getSystemInfo 的同步版本
	wx.getSystemInfoAsync	异步获取系统信息
	wx.getSystemInfo	获取系统信息
	wx.getSkylineInfoSync	获取当前运行环境对于 Skyline 渲染引擎 的支持情况
	wx.getSkylineInfo	获取当前运行环境对于 Skyline 渲染引擎 的支持情况
	wx.getRendererUserAgent	获取 Webview 小程序的 UserAgent
	wx.getDeviceInfo	获取设备基础信息
	wx.getDeviceBenchmarkInfo	获取设备性能得分和机型档位数据
	wx.getAppBaseInfo	获取微信APP基础信息
	wx.getAppAuthorizeSetting	获取微信APP授权设置

	更新	
	
	名称	功能
	wx.updateWeChatApp	更新客户端版本
	wx.getUpdateManager	获取全局唯一的版本更新管理器，用于管理小程序更新
	UpdateManager	UpdateManager 对象，用来管理更新，可通过 wx.getUpdateManager 接口获取实例
	
	名称	功能
	UpdateManager.applyUpdate	强制小程序重启并使用新版本
	UpdateManager.onCheckForUpdate	监听向微信后台请求检查更新结果事件
	UpdateManager.onUpdateFailed	监听小程序更新失败事件
	UpdateManager.onUpdateReady	监听小程序有版本更新事件

	生命周期	
	
	名称	功能
	wx.onApiCategoryChange	监听 API 类别变化事件
	wx.offApiCategoryChange	移除 API 类别变化事件的监听函数
	wx.getLaunchOptionsSync	获取小程序启动时的参数
	wx.getEnterOptionsSync	获取本次小程序启动时的参数
	wx.getApiCategory	获取当前 API 类别

	应用级事件	
	
	名称	功能
	wx.postMessageToReferrerPage	向跳转的源页面发送消息
	wx.postMessageToReferrerMiniProgram	向跳转的源小程序发送消息，源小程序可在 wx.onShow 或 wx.getEnterOptionsSync 中通过 extraData 接收消息
	wx.onUnhandledRejection	监听未处理的 Promise 拒绝事件
	wx.onThemeChange	监听系统主题改变事件
	wx.onPageNotFound	监听小程序要打开的页面不存在事件
	wx.onLazyLoadError	监听小程序异步组件加载失败事件
	wx.onError	监听小程序错误事件
	wx.onAudioInterruptionEnd	监听音频中断结束事件
	wx.onAudioInterruptionBegin	监听音频因为受到系统占用而被中断开始事件
	wx.onAppShow	监听小程序切前台事件
	wx.onAppHide	监听小程序切后台事件
	wx.offUnhandledRejection	移除未处理的 Promise 拒绝事件的监听函数
	wx.offThemeChange	移除系统主题改变事件的监听函数
	wx.offPageNotFound	移除小程序要打开的页面不存在事件的监听函数
	wx.offLazyLoadError	移除小程序异步组件加载失败事件的监听函数
	wx.offError	移除小程序错误事件的监听函数
	wx.offAudioInterruptionEnd	移除音频中断结束事件的监听函数
	wx.offAudioInterruptionBegin	移除音频因为受到系统占用而被中断开始事件的监听函数
	wx.offAppShow	移除小程序切前台事件的监听函数
	wx.offAppHide	移除小程序切后台事件的监听函数

	路由事件	
	
	名称	功能
	wx.onBeforePageUnload	监听路由事件引起现有页面实例销毁时，页面实例销毁前的事件监听，详见 页面路由监听
	wx.onBeforePageLoad	监听路由事件引起新的页面实例化时，页面实例化前的事件监听，详见 页面路由监听
	wx.onBeforeAppRoute	监听路由事件下发后，执行路由逻辑前的事件监听，详见 页面路由监听
	wx.onAppRouteDone	监听当前路由动画执行完成的事件监听，详见 页面路由监听
	wx.onAppRoute	监听路由事件下发后，执行路由逻辑后的事件监听，详见 页面路由监听
	wx.onAfterPageUnload	监听路由事件引起现有页面实例销毁时，页面实例销毁后的事件监听，详见 页面路由监听
	wx.onAfterPageLoad	监听路由事件引起新的页面实例化时，页面实例化完成的事件监听，详见 页面路由监听
	wx.offBeforePageUnload	移除路由事件的监听函数
	wx.offBeforePageLoad	移除路由事件的监听函数
	wx.offBeforeAppRoute	移除路由事件的监听函数
	wx.offAppRouteDone	移除当前路由动画执行完成的事件的监听函数
	wx.offAppRoute	移除路由事件的监听函数
	wx.offAfterPageUnload	移除路由事件的监听函数
	wx.offAfterPageLoad	移除路由事件的监听函数

	调试	
	
	名称	功能
	wx.setEnableDebug	设置是否打开调试开关
	wx.getRealtimeLogManager	获取实时日志管理器对象
	wx.getLogManager	获取日志管理器对象
	console	向调试面板中打印日志
	
	名称	功能
	console.debug	向调试面板中打印 deb

... (content truncated)

---

## 2. 微信开放文档 / 服务端

**Source**: [https://developers.weixin.qq.com/miniprogram/dev/server/API/](https://developers.weixin.qq.com/miniprogram/dev/server/API/)

微信开放文档 /服务端
接口调用凭证
接口名称	请求路径	描述
获取接口调用凭据	/cgi-bin/token	本接口用于获取获取全局唯一后台接口调用凭据（Access Token），token 有效期为 7200 秒，开发者需要进行妥善保存，使用注意事项请参考此文档
获取稳定版接口调用凭据	/cgi-bin/stable_token	本接口用于获取获取全局唯一后台接口调用凭据（Access Token），token 有效期为 7200 秒，但此接口和 getAccessToken 互相隔离，
openApi管理
接口名称	请求路径	描述
查询API调用额度	/cgi-bin/openapi/quota/get	本接口用于查询服务端接口的的每日调用接口的额度，调用次数，频率限制
重置API调用次数	/cgi-bin/clear_quota	本接口是通过access_token清空服务端接口的每日调用接口次数
重置指定API调用次数	/cgi-bin/openapi/quota/clear	本接口使用 access_token 来重置指定接口的每日调用次数
使用AppSecret重置API调用次数	/cgi-bin/clear_quota/v2	本接口是通过AppSecret清空服务端接口的每日调用接口次数
查询rid信息	/cgi-bin/openapi/rid/get	本接口用于查询调用服务端接口报错返回的rid详情信息，辅助开发者高效定位问题
网络通信检测	/cgi-bin/callback/check	为了帮助开发者排查回调连接失败的问题，提供这个网络检测的API
获取微信API服务器IP	/cgi-bin/get_api_domain_ip	该接口用于获取微信 api 服务器 ip 地址（开发者服务器主动访问 api.weixin.qq.com 的远端地址）
获取微信推送服务器IP	/cgi-bin/getcallbackip	该接口用于获取微信推送服务器 ip 地址（向开发者服务器推送信息的微信服务器来源地址）
用户信息
用户信息
接口名称	请求路径	描述
获取插件用户openpid	/wxa/getpluginopenpid	通过 wx.pluginLogin 接口获得插件用户标志凭证 code 后传到开发者服务器，开发者服务器调用此接口换取插件用户的唯一标识 openpid
检查加密信息	/wxa/business/checkencryptedmsg	检查加密信息是否由微信生成（当前只支持手机号加密数据），只能检测最近3天生成的加密数据
支付后获取Unionid	/wxa/getpaidunionid	该接口用于在用户支付完成后，获调用本接口前需要用户完成支付，用户支付完成后，取该用户的 UnionId，无需用户授权
网络
接口名称	请求路径	描述
获取用户encryptKey	/wxa/business/getuserencryptkey	该接口用于获取用户encryptKey
手机号
接口名称	请求路径	描述
获取手机号	/wxa/business/getuserphonenumber	该接口用于将code换取用户手机号
小程序登录
接口名称	请求路径	描述
小程序登录凭证校验	/sns/jscode2session	登录凭证校验
检验登录态	/wxa/checksession	校验服务器所保存的登录态 sessionkey 是否有效
重置登录态	/wxa/resetusersessionkey	重置指定的登录态 sessionkey
小程序码与小程序链接
小程序码
接口名称	请求路径	描述
获取小程序码	/wxa/getwxacode	该接口用于获取小程序码，适用于需要的码数量较少的业务场景
获取不限制的小程序码	/wxa/getwxacodeunlimit	该接口用于获取小程序码，适用于需要的码数量极多的业务场景
获取小程序二维码	/cgi-bin/wxaapp/createwxaqrcode	获取小程序二维码，适用于需要的码数量较少的业务场景
URL Scheme
接口名称	请求路径	描述
查询scheme码	/wxa/queryscheme	该接口用于查询小程序 scheme 码，包括加密 scheme 和明文 scheme
获取加密scheme码	/wxa/generatescheme	该接口用于获取小程序 scheme 码，适用于短信、邮件、外部网页、微信内等拉起小程序的业务场景
获取NFC的小程序scheme	/wxa/generatenfcscheme	该接口用于获取用于 NFC 的小程序 scheme 码，适用于 NFC 拉起小程序的业务场景
URL Link
接口名称	请求路径	描述
获取加密URLLink	/wxa/generate_urllink	获取小程序 URL Link，适用于短信、邮件、网页、微信内等拉起小程序的业务场景
查询加密URLLink	/wxa/query_urllink	该接口用于查询小程序加密 url_link 配置
Short Link
接口名称	请求路径	描述
获取ShortLink	/wxa/genwxashortlink	获取小程序 Short Link，适用于微信内拉起小程序的业务场景
小程序客服
客服消息
接口名称	请求路径	描述
获取临时素材	/cgi-bin/media/get	本接口用于获取临时素材（即下载临时的多媒体文件）
客服输入状态	/cgi-bin/message/custom/business/typing	本接口用于设置客服输入状态
新增临时素材	/cgi-bin/media/upload	本接口用于上传临时多媒体文件
发送客服消息	/cgi-bin/message/custom/send	本接口用于发送多种类型的客服消息，主要应用在有人工消息处理环节的场景
微信客服
接口名称	请求路径	描述
查询绑定情况	/customservice/work/get	查询小程序的微信客服绑定情况
绑定微信客服	/customservice/work/bind	为小程序绑定微信客服
解除绑定微信客服	/customservice/work/unbind	为小程序解除绑定微信客服
消息相关
动态消息
接口名称	请求路径	描述
创建activity_id	/cgi-bin/message/wxopen/activityid/create	该接口用于创建被分享动态消息或私密消息的 activity_id
修改动态消息	/cgi-bin/message/wxopen/updatablemsg/send	该接口用于修改被分享的动态消息
修改小程序聊天工具的动态卡片消息	/cgi-bin/message/wxopen/chattoolmsg/send	该接口用于修改被分享的小程序聊天工具的动态卡片消息
订阅消息
接口名称	请求路径	描述
删除模板	/wxaapi/newtmpl/deltemplate	删除私有模板库中的模板
获取类目	/wxaapi/newtmpl/getcategory	本接口用于获取小程序、公众号所

... (content truncated)

---

