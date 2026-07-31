# Other

*6 pages in this category*

## Table of Contents

1. [微信开放文档 / 商业能力](#1-微信开放文档-/-商业能力)
2. [微信开放文档 / 城市服务](#2-微信开放文档-/-城市服务)
3. [微信开放文档 / 服务市场](#3-微信开放文档-/-服务市场)
4. [微信开放文档 / 付费能力](#4-微信开放文档-/-付费能力)
5. [介绍](#5-介绍)
6. [微信开放文档 / 行业能力](#6-微信开放文档-/-行业能力)

---

## 1. 微信开放文档 / 商业能力

**Source**: [https://developers.weixin.qq.com/miniprogram/dev/platform-capabilities/business-capabilities/](https://developers.weixin.qq.com/miniprogram/dev/platform-capabilities/business-capabilities/)

微信开放文档 /商业能力
商业能力

本章为商业能力相关文档

小程序购物订单


小程序购物订单收纳用户通过小程序进行购物的相关订单信息，为用户提供查看/管理订单的统一入口。用户可以从微信「我」-「购物订单与卡包」-「小程序购物订单」中进入查看订单列表与订单详情信息。

交易保障


小程序交易保障是小程序官方针对交易类小程序提供的保障服务。 在微信生态内，为消费者保障权益、提升交易体验；同时为优质小程序背书，帮助小程序与消费者建立交易信任。

交易组件


为了保障用户的交易购物体验、打通微信生态场景，小程序开放了交易组件。接入组件可以实现与视频号的关联及直播带货等。包含标准版交易组件组件介绍及自定义版交易组件组件介绍。

小程序联盟


小程序联盟是微信官方提供的商品推广工具，具有“推广成交后再计费”的特点。商家可以发布想要推广的商品和服务，后续经过联盟渠道的推广，最终提高小程序成交量。 提高小程序商品成交量。

卡券


小程序卡券接口支持在小程序中领取/查看/使用公众号 AppId 创建的会员卡、票、券（含通用卡）。

小程序支付管理服务


为了优化消费者的支付体验，微信小程序提供了小程序支付管理服务。你可以在小程序后台或通过接口申请微信支付商户号。成功申请商户号后，即可在小程序中使用微信支付收款，以及在小程序后台查看流水、管理资金。

小程序发货信息管理服务


根据《商家自营类小程序运营规范》,特定类型的小程序需要在平完成发货信息录入及确认收货流程后方可进行资金结算。 开发者可以通过该接入服务，完成商品发货信息录入、提醒用户确认收货、在小程序内调起确认收货组件等功能，提升发货信息录入效率，优化用户体验。

全球收银


Tenpay Global 全球收银台，为微信小程序商户一站式接入全球支付方式，便捷接收各地消费者在小程序场景下的付款

购物订单


购物订单收纳用户线上购物相关订单信息，可帮助用户查看/管理订单，追踪订单进展、获取售后服务等。用户可以从微信「我」-「服务」-「钱包」-「账单」中进入，也可以从支付凭证消息进入账单详情页查看购物订单。(该功能已停止维护)

关于腾讯 文档中心 辟谣中心 客服中心

Copyright © 2012-2026 Tencent. All Rights Reserved.

---

## 2. 微信开放文档 / 城市服务

**Source**: [https://developers.weixin.qq.com/miniprogram/dev/platform-capabilities/cityservice/](https://developers.weixin.qq.com/miniprogram/dev/platform-capabilities/cityservice/)

微信开放文档 /城市服务
城市服务开放互联能力

为满足用户多场景使用服务的需求，城市服务提供开放互联能力。 符合条件的业务方可通过MP端或者API配置，实现多场景跳转微信城市服务限定页面。



能力说明
1. 支持跳转的页面类型

目前支持外部业务方跳转城市服务首页、专题页、服务列表页和服务主页。

页面定义

首页

指城市服务首页，访问路径：打开微信-我-服务-城市服务。

专题页：

指热门民生话题的服务聚合页，访问路径：打开微信-我-服务-城市服务-专题。
专题在全国各地陆续上线，包括：养老、结婚生子、医疗保健、交通出行、就业创业、购房落户、升学考试。

服务列表页

指城市服务内某城市某类目下的所有服务列表，访问路径：打开微信-我-服务-城市服务-热门服务/办事大厅二级类目。
每个类目均配有服务列表页，举例：社保、公积金、医疗、出行、交管、公安办证、税务综合等。

服务主页：

指入驻服务方在城市服务的主页，结构化提供服务简介、服务链接、相关账号、联系信息等。
已入驻城市服务的服务均配有服务主页，举例：全国住房公积金、全国教育服务、X省社保缴纳、X市挂号平台、X省城乡居民养老保险等。



2. 支持跳转的场景举例

目前支持业务方在多个场景跳转打开城市服务的限定页面，举例：其他小程序跳转、公众号菜单跳转、公众号客服/小程序客服/H5客服场景跳转、短信跳转、安卓桌面打开城市服务。 





3. 满足条件的账号可申请该能力

已进驻城市服务且已开通服务主页的账号（公众号、小程序、OPEN账号均支持）



4. 申请流程

第一步：获得账号授权

发送申请邮件至 wx_city@tencent.com ，标题格式为【城市服务开放互联能力申请+主体名称+APPID】，并在正文列明以下信息，后台工作人员将在收到邮件后尽快处理并回复结果。


	申请信息
主体名	
调用APPID	
跳转场景	
跳转页面类型	
联系单位	
联系人及电话	
联系人微信	



第二步：调用接口获得对应的动态页面路径

通过下述方式调用接口，获得对应的动态页面路径。


第三步：完成配置和测试发布



5. 调用方式

第一类：API调用

第二类：MP配置



如有疑问，可在微信开放社区留言，或联系微信城市服务官方邮箱 wx_city@tencent.com 。

关于腾讯 文档中心 辟谣中心 客服中心

Copyright © 2012-2026 Tencent. All Rights Reserved.

---

## 3. 微信开放文档 / 服务市场

**Source**: [https://developers.weixin.qq.com/miniprogram/dev/platform-capabilities/service-market/](https://developers.weixin.qq.com/miniprogram/dev/platform-capabilities/service-market/)

微信开放文档 /服务市场
服务市场

除基础组件与接口能力外，「小程序·服务市场」还为小程序开发者提供更丰富的增值能力，开发者可根据需求，选购不同规格的资源包。购买后，通过调用小程序原生快捷接入服务平台内的能力，丰富小程序的功能。

AI
微信OCR识别
微信OCR识别能力是微信团队推出的一套提升移动端快捷信息录入 的工具，目前支持身份证、银行卡、行驶证、营业执照的 OCR 识别。
智能对话服务
微信智能对话服务是以对话交互为核心, 为有客服需求的个人、企业和组织提供智能对话系统的搭建。
夸夸话术服务
夸夸话术服务是以对话交互为基础，为用户提供花式夸人的互动娱乐服务。用户接入服务后，可以通过相关的描述语句来唤醒夸夸技能。开发者可以将该技能应用到智能对话、客服等场景中。
商品二分类
商品二分类服务提供可灵活调用的接口，能够判断用户输入的自然语言文本是否与商品相关。开发者可以利用该接口赋能自己的智能搜索、商品服务等场景。
多语言翻译
提供多语言翻译能力
讲笑话情话服务
讲笑话情话服务是以对话交互为基础，为用户提供普通笑话、冷笑话、情话等互动娱乐服务。用户接入服务后，可以通过相关的触发语句来唤醒对应技能。开发者可以将该服务应用到智能对话、客服等场景中。
情感分析服务
情感分析服务是以自然语言处理技术为基础，为有文本分析需求的个人、企业或组织提供识别给定语句的情感状态的能力。具体包括正面、负面、无情感三类。开发者可以将该服务应用到商品评论分析、智能对话、舆情监控等场景中。
商品关键词抽取
商品关键词抽取服务提供可灵活调用的接口，能够从电商商品标题中抽取关键词，包括商品名、品牌名、修饰词、营销词、颜色、材质、时间季节、地点、型号、尺寸规格单位共10类。开发者可以利用该接口赋能自己的智能客服、商品服务等场景。
安全
黑产情报应急响应
可以通过该接口将黑产微信账号信息上报给微信安全团队，有微信安全团队应急响应，协同治理安全问题。
营销活动反作弊
在商户进行补贴、优惠等商业营销活动时，保护三方产品的营销资源，降低业务安全问题给产品带来的损失，为商家活动保驾护航。
账号风险识别
通过该能力，商户和开发者可以快速识别授权登录用户在微信内的恶意等级，以便快速的指定安全策略，保证业务安全。
地图
地点搜索
基于腾讯位置服务千万级鲜活地点(POI)数据，提供结合搜索关键词的周边、城市范围、矩形范围（屏幕视野内）等多种地理位置搜索能力，同时提供分类筛选功能，满足不同场景的地点搜索需要。
坐标转换
实现从其它地图供应商坐标系或标准GPS坐标系，批量转换到腾讯地图坐标系，使之可以在微信小程序地图中准确标注与使用。
关键词输入提示
用于获取输入地点关键字的补完与提示，提供了面向创建收货/服务地址、打车目的地搜索及位置签到搜索等多种场景策略。服务基于海量点击行为挖掘、训练，准确命中用户所想，平均输入3.2个字即可获取准确结果。
驾车路线规划
基于驾车场景的智能路线计算引擎，支持多途经点、结合实时路况、不走高速、少收费等多种偏好设置功能，支持车牌限行避让策略，并专为网约车提供接驾、送驾场景的路线规划策略。
步行路线规划
结合海量步行道路、过街天桥、地下通道及人行出入口等设施数据，提供智能步行路线规划服务。
地址解析
提供由文字地址到经纬度坐标的转换的能力，可一定程度上兼容地址本身不规范的问题（如错别字，省市区与门牌、地点不匹配、各类干扰词等情况），同时支持返回省市区、行政区划代码信息。
逆地址解析
提供经纬度坐标到结构化地址的转换能力，结果包含对坐标位置的文字描述、省市区等行政区划信息、门牌号、商圈、道路与交叉口以及周边地点列表等，服务响应快速稳定，对微信、美团、快手等超级APP提供可靠支撑。
内容
腾讯云正版曲库直通车
正版曲库直通车是基于腾讯音乐娱乐集团海量线上背景音乐专用曲库资源，结合腾讯云存储、内容加速分发等基础能力，为解决内容创作过程中的正版背景音乐素材应用问题设计的 PaaS 产品。
视频剪辑插件——微剪
为小程序提供视频剪辑能力：接入即用，支持多视频图片拼接，还有丰富的音乐、滤镜资源，炫酷生动的特效。给小程序生态的内容制作提供得力工具。
关于腾讯 文档中心 辟谣中心 客服中心

Copyright © 2012-2026 Tencent. All Rights Reserved.

---

## 4. 微信开放文档 / 付费能力

**Source**: [https://developers.weixin.qq.com/miniprogram/dev/platform-capabilities/charge/](https://developers.weixin.qq.com/miniprogram/dev/platform-capabilities/charge/)

微信开放文档 /付费能力
付费管理

小程序有丰富的开放能力。其中，由于技术服务与运营成本原因，部分能力需付费使用，开发者可根据小程序自身业务场景需要而选择购买。付费管理模块，承载开发者在小程序里购买各项付费能力，管理订单和用量，开具发票的功能。

了解各项付费能力
登录小程序MP平台；
点击左侧菜单「付费管理」；
查看可以购买的各项能力、用量；
查看文档或查看详情，了解各项能力用法，以及计费规则。

购买付费能力
在“能力购买”里，选择所需购买的能力，点击“购买”；
参考【最近三个月平均用量】，选择所需购买的资源包。

点击【支付】，完成付款。支持微信支付和网银支付两种方式，如需对公账户付款，可以使用网银支付方式。后续将支持线下打款等更多付款方式。

查看订单、开具发票
在「我的订单」中可查看订单列表，并开具发票；
在「发票」中可查看开过的发票列表；
可以申请增值税专用发票，将通过邮寄方式送达；
发票开具时间预计为5-10个工作日。

查看用量

在「我的用量」中可查看各项能力的用量情况

用量提醒

当资源包将要到期、将要用完时，平台将对小程序管理员、运营人员发送用量预警的消息通知，请及时关注和补充用量。 平台将在资源包余量不足20%、10%、5%及用完时发送模板消息预警。

SPU ID
小程序付费能力	SPU ID
小程序音视频通话	10000058
手机号快速验证组件	10000077
手机号实时验证组件	10000086
地图个性化样式组件	10000092
关于腾讯 文档中心 辟谣中心 客服中心

Copyright © 2012-2026 Tencent. All Rights Reserved.

---

## 5. 介绍

**Source**: [https://developers.weixin.qq.com/miniprogram/dev/platform-capabilities/extended/](https://developers.weixin.qq.com/miniprogram/dev/platform-capabilities/extended/)

本章为小程序扩展能力相关文档

WeUI组件库
扩展组件
Kbone 解决方案
框架扩展
工具类库
插件服务
微信同声传译
OCR 支持
自然语言理解
关于腾讯 文档中心 辟谣中心 客服中心

Copyright © 2012-2026 Tencent. All Rights Reserved.

---

## 6. 微信开放文档 / 行业能力

**Source**: [https://developers.weixin.qq.com/miniprogram/dev/platform-capabilities/industry/](https://developers.weixin.qq.com/miniprogram/dev/platform-capabilities/industry/)

微信开放文档 /行业能力
交易评价-评价管理接口

「小程序交易评价」是小程序官方提供的真实公正的评价系统。在小程序的交易用户可针对某次交易体验进行评价打分、发表建议和感受。 以下接口提供给小程序开发者用于查询、回复、处理小程序用户交易评价。

查询
1.1 查询评价列表
1.2 查询评论列表
1.3 查询评价详情
评论
2.1 创建评论
2.2 删除评论
回复
3.1 创建回复
3.2 删除回复
差评客服会话
4.1 差评通知CallBack
4.2 重置Api客服quota
确认和解
1、查询

使用该接口可以查询某小程序下，所有评价相关内容。

1.1查询评价列表

查询某小程序下面所有的评价。

请求方式

GET

请求 URL
https://api.weixin.qq.com/wxaapi/comment/mpcommentlist/get

请求参数示例： Javascript

https://api.weixin.qq.com/wxaapi/comment/mpcommentlist/get?filterType=1&offset=0&limit=8&startTime=1588237130&endTime=1588237131&access_token=xxxx

query 参数包括

{
    startTime: "1588237130",  
    endTime: "1588237131",    
    filterType: 1,
    offset: 0,
    limit: 8,
    access_token: 'xxxx'
}

请求参数含义
参数	类型	必填	说明
startTime	String	是	查询时间段的开始时间
endTime	String	是	查询时间段的结束时间
filterType	Number	否	过滤的数据类型，枚举参考下方表格
offset	Number	否	查询的偏移数（从offset开始计数拉取)，默认值为 0 代表首页拉取
limit	Number	否	查询每页中的数量，默认值为 8
评价类型筛选枚举（filterType）
值	说明
1	全部差评，所有评价分数为1星、2星的评价
2	全部好评，所有评价分数为4星、5星的评价
3	差评待处理，所有未提交「和解挽回」的评价
4	开发者待回复，所有待开发者回复的评价
5	差评已改评
6	全部评价，所有好评、差评、中评（3星）部评价
正确返回示例
{
  errcode: 0,
  success: true,
  commentList: [{
    commentId: "2797755680173111111",
    amount: 100,
    orderId: "payorder@_4200001761202302096311111111",
    payTime: "1675915718",
    wxPayId: "4200001761202302096311111111",
    orderInfo: {
      busiOrderId: 'xxxxxx'
    },
    userInfo: {
      openid: "xxxxxxxxxx",
      headImg: "http://wx.qlogo.cn/mmhead/xxxxxxxxxxx",
      nickName: "test"
    },
    bizInfo: {
        appid: "wx1234567890",
        headImg: "http://wx.qlogo.cn/mmhead/xxxxxxxxxxxx",
        nickName: "xxx"
    },
    score: 200, // 200分对应2星，每100分就是1星
    createTime: "1676351504",
    content: {
      media: [{img: 'http://xxx', thumbImg: 'http://xxx'}],
      txt: "一般吧 我总感觉这个成分很伤皮肤，用了之后一直很干燥，不是很喜欢这款产品"
    },
    extInfo: {
      isAlreadySendTmpl: false,
    },
    productInfo: {
      productList: [
        {
            name: "纸巾一张",
            picUrl: "https://xxxxxx",
        }
      ]
    }
  }],
  total: 3,
  offset: 0,
}

返回参数含义
	属性	类型	说明
	errcode	Number	错误码
	offset	Number	查询的偏移数（从offset开始计数拉取)
	total	Number	评价总数
	commentList	Array < Object >	评价的列表具体如下
	
属性	类型	说明
commentId	String	评价id
amount	Number	金额,单位是分
orderId	String	订单id
createTime	String	创建时间，单位是秒
payTime	String	支付时间，单位是秒
wxPayId	String	微信支付交易单号，一般以420开头，是微信支付接口文档中的transaction_id
orderInfo	Object	商家订单信息，详情看下表
userInfo	Object	评价用户信息
bizInfo	Object	商家小程序信息
score	Number	评价分数（每100分对应1星）
content	Object	评价内容
extInfo	Object	评价额外信息
productInfo	Object	评价商品信息

userInfo 的具体参数

参数	类型	说明
openid	String	评价用户openid
headImg	String	评价用户的头像
nickName	String	评价用户的昵称

orderInfo 的具体参数

参数	类型	说明
busiOrderId	String	商户单号：商户系统内部订单号，只能是数字、大小写字母_-*且在同一个商户号下唯一；是微信支付接口文档中的 out_trade_no

bizInfo 的具体参数

参数	类型	说明
appid	String	商家小程序的appid
headImg	String	商家小程序的头像
nickName	String	商家小程序的昵称

content 的具体参数

	属性	类型	说明
	txt	String	评价内容
	media	Array< Object >	评价的媒体文件，如图片、视频, 视频跟图片只能存在一种，不同时存在，如果是图片可以有多张图，如果是视频只会有一个视频
	
属性	类型	说明
img	String	图片cdn
thumbImg	St

... (content truncated)

```http
https://api.weixin.qq.com/wxaapi/comment/mpcommentlist/get

```

```javascript
{
    startTime: "1588237130",  
    endTime: "1588237131",    
    filterType: 1,
    offset: 0,
    limit: 8,
    access_token: 'xxxx'
}

```

```javascript
{
  errcode: 0,
  success: true,
  commentList: [{
    commentId: "2797755680173111111",
    amount: 100,
    orderId: "payorder@_4200001761202302096311111111",
    payTime: "1675915718",
    wxPayId: "4200001761202302096311111111",
    orderInfo: {
      busiOrderId: 'xxxxxx'
    },
    userInfo: {
      openid: "xxxxxxxxxx",
      headImg: "http://wx.qlogo.cn/mmhead/xxxxxxxxxxx",
      nickName: "test"
    },
    bizInfo: {
        appid: "wx1234567890",
        headImg: "http://wx.qlogo.cn/mmhead/xxxxxxxxxxxx",
        nickName: "xxx"
    },
    score: 200, // 200分对应2星，每100分就是1星
    createTime: "1676351504",
    content: {
      media: [{img: 'http://xxx', thumbImg: 'http://xxx'}],
      txt: "一般吧 我总感觉这个成分很伤皮肤，用了之后一直很干燥，不是很喜欢这款产品"
    },
    extInfo: {
      isAlreadySendTmpl: false,
    },
    productInfo: {
      productList: [
        {
            name: "纸巾一张",
            picUrl: "https://xxxxxx",
        }
      ]
    }
  }],
  total: 3,
  offset: 0,
}

```

---

