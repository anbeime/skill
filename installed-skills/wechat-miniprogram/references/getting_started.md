# Getting Started

*11 pages in this category*

## Table of Contents

1. [起步](#1-起步)
2. [开放能力 / 用工关系](#2-开放能力-/-用工关系)
3. [glass-easel 组件框架 / 介绍](#3-glass-easel-组件框架-/-介绍)
4. [起步 / 小程序代码构成](#4-起步-/-小程序代码构成)
5. [连接硬件能力 / 音视频通话+摄像头（for 硬件） / VoIP 通话插件 / 接口文档 / 发起通话 / 介绍](#5-连接硬件能力-/-音视频通话+摄像头（for-硬件）-/-v)
6. [健康运营指引 / 用户隐私保护 / 插件用户隐私保护说明内容介绍](#6-健康运营指引-/-用户隐私保护-/-插件用户隐私保护说明内容)
7. [产品简介 / 多端框架概述](#7-产品简介-/-多端框架概述)
8. [健康运营指引 / 用户隐私保护 / 小程序用户隐私保护指引内容介绍](#8-健康运营指引-/-用户隐私保护-/-小程序用户隐私保护指引内)
9. [产品简介](#9-产品简介)
10. [Skyline 渲染引擎 / 概览 / 介绍](#10-skyline-渲染引擎-/-概览-/-介绍)
11. [Skyline 渲染引擎 / 从 WebView 迁移 / 起步](#11-skyline-渲染引擎-/-从-webview-迁移-/-)

---

## 1. 起步

**Source**: [https://developers.weixin.qq.com/miniprogram/dev/framework/quickstart/](https://developers.weixin.qq.com/miniprogram/dev/framework/quickstart/)

小程序简介

小程序是一种全新的连接用户与服务的方式，它可以在微信内被便捷地获取和传播，同时具有出色的使用体验。

小程序技术发展史

​小程序并非凭空冒出来的一个概念。当微信中的 WebView 逐渐成为移动 Web 的一个重要入口时，微信就有相关的 JS API 了。

代码清单1-1 使用 WeixinJSBridge 预览图片

WeixinJSBridge.invoke('imagePreview', {
    current: 'http://inews.gtimg.com/newsapp_bt/0/1693121381/641',
    urls: [ // 所有图片的URL列表，数组格式
        'https://img1.gtimg.com/10/1048/104857/10485731_980x1200_0.jpg',
        'https://img1.gtimg.com/10/1048/104857/10485726_980x1200_0.jpg',
        'https://img1.gtimg.com/10/1048/104857/10485729_980x1200_0.jpg'
    ]
}, function(res) {
    console.log(res.err_msg)
})


​代码1-1是一个调用微信原生组件浏览图片的JS API，相比于额外引入一个JS图片预览组件库，这种调用方式显得非常简洁和高效。

​实际上，微信官方是没有对外暴露过如此调用的，此类 API 最初是提供给腾讯内部一些业务使用，很多外部开发者发现了之后，依葫芦画瓢地使用了，逐渐成为微信中网页的事实标准。2015年初，微信发布了一整套网页开发工具包，称之为 JS-SDK，开放了拍摄、录音、语音识别、二维码、地图、支付、分享、卡券等几十个API。给所有的 Web 开发者打开了一扇全新的窗户，让所有开发者都可以使用到微信的原生能力，去完成一些之前做不到或者难以做到的事情。

同样是调用原生的浏览图片，调用方式如代码清单1-2所示。

代码清单1-2 使用 JS-SDK 调用图片预览组件

wx.previewImage({
  current: 'https://img1.gtimg.com/10/1048/104857/10485726_980x1200_0.jpg',
  urls: [ // 所有图片的URL列表，数组格式
    'https://img1.gtimg.com/10/1048/104857/10485731_980x1200_0.jpg',
    'https://img1.gtimg.com/10/1048/104857/10485726_980x1200_0.jpg',
    'https://img1.gtimg.com/10/1048/104857/10485729_980x1200_0.jpg'
  ],
  success: function(res) {
    console.log(res)
  }
})


​JS-SDK是对之前的 WeixinJSBridge 的一个包装，以及新能力的释放，并且由对内开放转为了对所有开发者开放，在很短的时间内获得了极大的关注。从数据监控来看，绝大部分在微信内传播的移动网页都使用到了相关的接口。

​JS-SDK 解决了移动网页能力不足的问题，通过暴露微信的接口使得 Web 开发者能够拥有更多的能力，然而在更多的能力之外，JS-SDK 的模式并没有解决使用移动网页遇到的体验不良的问题。用户在访问网页的时候，在浏览器开始显示之前都会有一个白屏的过程，在移动端，受限于设备性能和网络速度，白屏会更加明显。我们团队把很多技术精力放置在如何帮助平台上的Web开发者解决这个问题。因此我们设计了一个 JS-SDK 的增强版本，其中有一个重要的功能，称之为“微信 Web 资源离线存储”。

​以下文字引用自内部的文档（没有最终对外开放）：

微信 Web 资源离线存储是面向 Web 开发者提供的基于微信内的 Web 加速方案。

通过使用微信离线存储，Web 开发者可借助微信提供的资源存储能力，直接从微信本地加载 Web 资源而不需要再从服务端拉取，从而减少网页加载时间，为微信用户提供更优质的网页浏览体验。每个公众号下所有 Web App 累计最多可缓存 5M 的资源。

​这个设计有点类似 HTML5 的 Application Cache，但在设计上规避了一些 Application Cache的不足。

​在内部测试中，我们发现 离线存储 能够解决一些问题，但对于一些复杂的页面依然会有白屏问题，例如页面加载了大量的 CSS 或者是 JavaScript 文件。​除了白屏，影响 Web 体验的问题还有缺少操作的反馈，主要表现在两个方面：页面切换的生硬和点击的迟滞感。

​微信面临的问题是如何设计一个比较好的系统，使得所有开发者在微信中都能获得比较好的体验。这个问题是之前的 JS-SDK 所处理不了的，需要一个全新的系统来完成，它需要使得所有的开发者都能做到：

- 快速的加载

- 更强大的能力

- 原生的体验

- 易用且安全的微信数据开放

- 高效和简单的开发

这就是小程序的由来。

小程序与普通网页开发的区别

​小程序的主要开发语言是 JavaScript。小程序的开发与普通的网页开发有不少相似之处，对于前端开发者来说，从网页开发迁移到小程序开发的成本并不高，但是二者还是有些许区别的。

​网页开发中， 渲染任务和脚本任务是互斥的，这也是为什么长时间的脚本运行可能会导致页面失去响应，而在小程序中，二者是分开的，分别运行在不同的线程中。网页开发者可以使用到各种浏览器暴露出来的 DOM API，进行 DOM 选中和操作。而如上文所述，小程序的逻辑层和渲染层是分开的，逻辑层运行在不同于渲染层的独立 JS 运行时中，因此并不能直接使用 DOM API 和 BOM API。这一区别导致了前端开发非常熟悉的一些库，例如 jQuery、 Zepto 等，在小程序中是无法运行的。同时逻辑层的 JS 运行时与 NodeJS 环境也不尽相同，所以一些 NPM 的包在小程序中也是无法运行的。

​网页开发者需要面对的环境是各式各样的浏览器，PC 端需要面对 IE、Chrome、QQ浏览器等，在移动端需要面对Safari、Chrome以及 iOS、Android 系统中的各式 WebView 。而小程序开发过程中需要面对的是两大操作系统 iOS 和 Android 的微信客户端，以及用于辅助开发的小程序开发者工具，小程序中三大运行环境也是有所区别的，如表1-1所示。

表1-1 小程序的运行环境

运行环境	逻辑层	渲染层
iOS	JavaScriptCore	WKWebView
安卓	V8	chromium定制内核
小程序开发者工具	NWJS	Chrome WebView

​网页开发者在开发网页的时候，只需要使用到浏览器，并且搭配上一些辅助工具或者编辑器即可。小程序的开发则有所不同，需

... (content truncated)

```javascript
WeixinJSBridge.invoke('imagePreview', {
    current: 'http://inews.gtimg.com/newsapp_bt/0/1693121381/641',
    urls: [ // 所有图片的URL列表，数组格式
        'https://img1.gtimg.com/10/1048/104857/10485731_980x1200_0.jpg',
        'https://img1.gtimg.com/10/1048/104857/10485726_980x1200_0.jpg',
        'https://img1.gtimg.com/10/1048/104857/10485729_980x1200_0.jpg'
    ]
}, function(res) {
    console.log(res.err_msg)
})

```

```javascript
wx.previewImage({
  current: 'https://img1.gtimg.com/10/1048/104857/10485726_980x1200_0.jpg',
  urls: [ // 所有图片的URL列表，数组格式
    'https://img1.gtimg.com/10/1048/104857/10485731_980x1200_0.jpg',
    'https://img1.gtimg.com/10/1048/104857/10485726_980x1200_0.jpg',
    'https://img1.gtimg.com/10/1048/104857/10485729_980x1200_0.jpg'
  ],
  success: function(res) {
    console.log(res)
  }
})

```

---

## 2. 开放能力 / 用工关系

**Source**: [https://developers.weixin.qq.com/miniprogram/dev/framework/open-ability/laboruse/intro.html](https://developers.weixin.qq.com/miniprogram/dev/framework/open-ability/laboruse/intro.html)

开放能力 /用工关系
用工关系
一、功能简介

用工关系功能，支持与小程序有用工关系的用户能与对应的小程序进行绑定。绑定后

小程序可以向已绑定的用户推送用工关系消息通知
绑定用户将能在微信「小程序助手」中接收用工关系消息通知

通过这个功能，确保小程序在用工场景下的关键业务信息高效触达。 

二、功能详情

支持基础库版本：3.10.0以上
支持微信版本：8.0.62以上

1、开通功能

此功能只支持非个人主体下的物流服务/医疗服务/政务民生/金融业/教育服务/交通服务/房地产服务/生活服务/IT科技/餐饮服务/旅游服务/商家自营/商业服务类目下的小程序

这些类目下的，可登录微信公众平台，符合类目要求即可在侧边栏找到「用工关系」，点击开通，填写申请内容后，等待审核（审核时长平均<24h）。

2、新增用工消息模版

在微信公众平台开通了用工关系功能后，可以新增所需要的用工消息模版，模版审核通过后即可使用。 

3、用工关系管理接口

绑定用工关系接口：wx.bindEmployeeRelation
开发者可以通过接口，给与小程序有用工关系的用户调用订阅弹窗，允许后的用户，可以在「小程序助手」插件中收到绑定系统消息。

解绑接口：UnbindUserB2CAuthInfo
开发者可以通过接口，直接解绑已与小程序有用工关系的用户，用户可以在「小程序助手」插件中收到解绑的系统消息。

检查关系接口：wx.checkEmployeeRelation
开发者可以通过接口，检查小程序用工关系功能和用户之间的绑定关系

4、用工消息订阅

拉起用工消息订阅有两个时机


在用户确认绑定用工关系后，可直接让用户订阅消息，详细可见技术文档wx. bindEmployeeRelation。
已绑定用工关系后，可调用接口让用户订阅消息，详细可见技术文档wx.requestSubscribeEmployeeMessage。
5、发送用工消息

在用户已绑定用工关系，且订阅了对应用工消息的前提下，开发者可以通过SendEmployeeRelationMsg 向用户发送用工消息。用户将在「小程序助手」中接收到对应的消息。

三、注意事项

务必确保正确使用该功能


此功能仅支持小程序在用工场景下的消息传递诉求，若在开发者其他场景滥用，则功能会被回收。
绑定关系弹窗和订阅消息弹窗都为强监控行为场景，请提前告知用工关系的用户，确保绑定弹窗的通过率。请勿给无用工关系的用户滥发消息，滥发会回收该功能。
关于腾讯 文档中心 辟谣中心 客服中心

Copyright © 2012-2026 Tencent. All Rights Reserved.

---

## 3. glass-easel 组件框架 / 介绍

**Source**: [https://developers.weixin.qq.com/miniprogram/dev/framework/custom-component/glass-easel/introduction.html](https://developers.weixin.qq.com/miniprogram/dev/framework/custom-component/glass-easel/introduction.html)

glass-easel 组件框架 /介绍
glass-easel ：新版微信小程序组件框架

glass-easel 是小程序组件框架的核心实现。它实质上是一个 JavaScript 的组件化界面框架，用来进行组件化、定义式的界面开发。

glass-easel 是对旧版小程序组件框架的重写，保持对旧版小程序组件框架特性的兼容，并添加了一些新特性。它运行时并不依赖于小程序环境，可以独立运行在 web 或其他 JavaScript 环境下。

主要特点

glass-easel 可以让同样的组件代码运行在 web 、小程序等不同环境下。

后端 是 glass-easel 的一个重要概念，表示组件系统的运行环境。在 web 环境下运行时，后端是浏览器的 DOM 接口；在小程序环境下运行时，后端则是小程序环境接口。这使得（后端无关的）组件代码可以运行在不同环境下。

glass-easel 完整具备小程序自定义组件相关特性，如组件模板、通信与事件、生命周期等等。此外， glass-easel 还实现了一些实用的新特性，也具有更好的 TypeScript 支持。

glass-easel 采用单组件节点树更新算法（大体上沿用了旧版小程序组件框架的更新算法），具有均衡的性能表现，适合高度组件化开发。





glass-easel 组件框架在 GitHub 上开源，代码和更详细的文档、示例等可以在 GitHub 上找到。

适配指引

glass-easel 适配指引 中列举了一些相较于现有组件框架 exparser 需要变更的逻辑，可以用于将现有的小程序迁移到新的框架，也可以用于快速了解新旧框架之间的差异。

关于腾讯 文档中心 辟谣中心 客服中心

Copyright © 2012-2026 Tencent. All Rights Reserved.

---

## 4. 起步 / 小程序代码构成

**Source**: [https://developers.weixin.qq.com/miniprogram/dev/framework/quickstart/code.html](https://developers.weixin.qq.com/miniprogram/dev/framework/quickstart/code.html)

起步 /小程序代码构成
小程序代码构成

​在上一章中，我们通过开发者工具快速创建了一个 QuickStart 项目。你可以留意到这个项目里边生成了不同类型的文件:

.json 后缀的 JSON 配置文件
.wxml 后缀的 WXML 模板文件
.wxss 后缀的 WXSS 样式文件
.js 后缀的 JS 脚本逻辑文件

接下来我们分别看看这4种文件的作用。

JSON 配置

JSON 是一种数据格式，并不是编程语言，在小程序中，JSON扮演的静态配置的角色。

我们可以看到在项目的根目录有一个 app.json 和 project.config.json，此外在 pages/logs 目录下还有一个 logs.json，我们依次来说明一下它们的用途。

小程序配置 app.json

app.json 是当前小程序的全局配置，包括了小程序的所有页面路径、界面表现、网络超时时间、底部 tab 等。QuickStart 项目里边的 app.json 配置内容如下：

{
  "pages":[
    "pages/index/index",
    "pages/logs/logs"
  ],
  "window":{
    "backgroundTextStyle":"light",
    "navigationBarBackgroundColor": "#fff",
    "navigationBarTitleText": "Weixin",
    "navigationBarTextStyle":"black"
  }
}


我们简单说一下这个配置各个项的含义:

pages字段 —— 用于描述当前小程序所有页面路径，这是为了让微信客户端知道当前你的小程序页面定义在哪个目录。
window字段 —— 定义小程序所有页面的顶部背景颜色，文字颜色定义等。

其他配置项细节可以参考文档 小程序的配置 app.json 。

工具配置 project.config.json

通常大家在使用一个工具的时候，都会针对各自喜好做一些个性化配置，例如界面颜色、编译配置等等，当你换了另外一台电脑重新安装工具的时候，你还要重新配置。

考虑到这点，小程序开发者工具在每个项目的根目录都会生成一个 project.config.json，你在工具上做的任何配置都会写入到这个文件，当你重新安装工具或者换电脑工作时，你只要载入同一个项目的代码包，开发者工具就自动会帮你恢复到当时你开发项目时的个性化配置，其中会包括编辑器的颜色、代码上传时自动压缩等等一系列选项。

其他配置项细节可以参考文档 开发者工具的配置 。

页面配置 page.json

这里的 page.json 其实用来表示 pages/logs 目录下的 logs.json 这类和小程序页面相关的配置。

如果你整个小程序的风格是蓝色调，那么你可以在 app.json 里边声明顶部颜色是蓝色即可。实际情况可能不是这样，可能你小程序里边的每个页面都有不一样的色调来区分不同功能模块，因此我们提供了 page.json，让开发者可以独立定义每个页面的一些属性，例如刚刚说的顶部颜色、是否允许下拉刷新等等。

其他配置项细节可以参考文档 页面配置 。

JSON 语法

这里说一下小程序里JSON配置的一些注意事项。

JSON文件都是被包裹在一个大括号中 {}，通过key-value的方式来表达数据。JSON的Key必须包裹在一个双引号中，在实践中，编写 JSON 的时候，忘了给 Key 值加双引号或者是把双引号写成单引号是常见错误。

JSON的值只能是以下几种数据格式，其他任何格式都会触发报错，例如 JavaScript 中的 undefined。

数字，包含浮点数和整数
字符串，需要包裹在双引号中
Bool值，true 或者 false
数组，需要包裹在方括号中 []
对象，需要包裹在大括号中 {}
Null

还需要注意的是 JSON 文件中无法使用注释，试图添加注释将会引发报错。

WXML 模板

从事过网页编程的人知道，网页编程采用的是 HTML + CSS + JS 这样的组合，其中 HTML 是用来描述当前这个页面的结构，CSS 用来描述页面的样子，JS 通常是用来处理这个页面和用户的交互。

同样道理，在小程序中也有同样的角色，其中 WXML 充当的就是类似 HTML 的角色。打开 pages/index/index.wxml，你会看到以下的内容:

<view class="container">
  <view class="userinfo">
    <button wx:if="{{!hasUserInfo && canIUse}}"> 获取头像昵称 </button>
    <block wx:else>
      <image src="{{userInfo.avatarUrl}}" background-size="cover"></image>
      <text class="userinfo-nickname">{{userInfo.nickName}}</text>
    </block>
  </view>
  <view class="usermotto">
    <text class="user-motto">{{motto}}</text>
  </view>
</view>


和 HTML 非常相似，WXML 由标签、属性等等构成。但是也有很多不一样的地方，我们来一一阐述一下：

标签名字有点不一样

往往写 HTML 的时候，经常会用到的标签是 div, p, span，开发者在写一个页面的时候可以根据这些基础的标签组合出不一样的组件，例如日历、弹窗等等。换个思路，既然大家都需要这些组件，为什么我们不能把这些常用的组件包装起来，大大提高我们的开发效率。

从上边的例子可以看到，小程序的 WXML 用的标签是 view, button, text 等等，这些标签就是小程序给开发者包装好的基本能力，我们还提供了地图、视频、音频等等组件能力。

更多详细的组件讲述参考下个章节 小程序的能力

多了一些 wx:if 这样的属性以及 {{ }} 这样的表达式

在网页的一般开发流程中，我们通常会通过 JS 操作 DOM (对应 HTML 的描述产生的树)，以引起界面的一些变化响应用户的行为。例如，用户点击某个按钮的时候，JS 会记录一些状态到 JS 变量里边，同时通过 DOM API 操控 DOM 的属性或者行为，进而引起界面一些变化。当项目越来越大的时候，你的代码会充斥着非常多的界面交互逻辑和程序的各种状态变量，显然这不是一个很好的开发模式，因此就有了 MVVM 的开发模式（例如 React, Vue），提倡把渲染和逻辑分离。简单来说就是不要再让 JS 直接操控 DOM，JS 只需要管理状态即可，然后再通过一种模板语法来描述状态和界面结构的关系即可。

小程序的框架也是用到了这个思路，如果你需要把一个 Hello World 的字符串显示在界面上。

WXML 是这么写 :

... (content truncated)

```json
{
  "pages":[
    "pages/index/index",
    "pages/logs/logs"
  ],
  "window":{
    "backgroundTextStyle":"light",
    "navigationBarBackgroundColor": "#fff",
    "navigationBarTitleText": "Weixin",
    "navigationBarTextStyle":"black"
  }
}

```

```html
<view class="container">
  <view class="userinfo">
    <button wx:if="{{!hasUserInfo && canIUse}}"> 获取头像昵称 </button>
    <block wx:else>
      <image src="{{userInfo.avatarUrl}}" background-size="cover"></image>
      <text class="userinfo-nickname">{{userInfo.nickName}}</text>
    </block>
  </view>
  <view class="usermotto">
    <text class="user-motto">{{motto}}</text>
  </view>
</view>

```

```html
<text>{{msg}}</text>

```

---

## 5. 连接硬件能力 / 音视频通话+摄像头（for 硬件） / VoIP 通话插件 / 接口文档 / 发起通话 / 介绍

**Source**: [https://developers.weixin.qq.com/miniprogram/dev/framework/device/voip-plugin/api/call-intro.html](https://developers.weixin.qq.com/miniprogram/dev/framework/device/voip-plugin/api/call-intro.html)

连接硬件能力 /音视频通话+摄像头（for 硬件） /VoIP 通话插件 /接口文档 /发起通话 /介绍
发起通话接口介绍

插件提供设备端和微信用户直接通话的能力。

1. 选择接口

开发者请根据场景选择不同的通话接口。

1.1 安卓 WMPF 设备呼叫手机微信

使用 initByCaller 接口，businessType 传 1。

1.2 Linux 设备呼叫手机微信

Linux 设备不运行小程序插件，请使用小程序音视频通话 SDK (Linux 设备)。

1.3 手机微信呼叫安卓 WMPF 设备
推荐：使用 callWMPF 接口。需插件 2.4.0 开始支持。若使用 license 计费，必须使用本接口。
使用 initByCaller 接口，businessType 传 2。此方式不支持 license 计费。
1.4 手机微信呼叫 Linux 设备

使用 callDevice 接口。需插件 2.4.0 开始支持。

请注意：呼叫 Linux 设备时，微信不进行消息推送，需要开发者自行将设备端加入房间所需参数（如 roomId 等）从微信端推送到设备端。

2. 使用前必读
2.1 进入通话页面

发起通话的几个接口即可以在小程序页面，也可以在插件页面调用。但是最终通话流程必须在插件页面才能进行。

如果发起通话时在小程序页面，接口调用成功后，开发者需要手动跳转到插件页面，插件页面加载完成后进入通话流程。
如果发起通话时在插件页面，接口调用成功后就会直接进入通话流程。此时请勿重复进行页面跳转，否则当前通话会被中断。
不建议页面栈内存在多个插件页面实例。
// 发起通话成功后，仅在当前不是插件页面的情况下需进行跳转。
wx.redirectTo({
  // 此处只需要传入 path 即可，如果开发者有其他参数需要传递给小程序，也可以自行拼接 query，并通过插件 getPluginOnloadOptions 接口获取。
  url: wmpfVoip.CALL_PAGE_PATH,
  // 插件 2.3.9 开始支持 CALL_PAGE_PATH, 低版本请传入 'plugin-private://wxf830863afde621eb/pages/call-page-plugin/call-page-plugin',
})

2.2 最大通话时长

为了降低开发者的开发成本，插件提供了限制最大通话时长的能力。最大通话时长应为 > 0 的数字。

通话时长从 startVoip 事件开始计时，超时后通话自动结束并弹 toast 提示用户，同时触发 hangUpVoip 事件，origin 为 'timeLimit'。

2.3 groupId 与 roomId

在插件 2.4.0 以下版本中，通话房间 ID 被称为 groupId，这个名字比较容易与设备组的 ID 产生混淆，因此从 2.4.0 开始，房间号统一更名为 roomId，但为保持向下兼容，groupId 参数仍予以保留。

二者除名字不同外，无其他差异。

关于腾讯 文档中心 辟谣中心 客服中心

Copyright © 2012-2026 Tencent. All Rights Reserved.

```js
// 发起通话成功后，仅在当前不是插件页面的情况下需进行跳转。
wx.redirectTo({
  // 此处只需要传入 path 即可，如果开发者有其他参数需要传递给小程序，也可以自行拼接 query，并通过插件 getPluginOnloadOptions 接口获取。
  url: wmpfVoip.CALL_PAGE_PATH,
  // 插件 2.3.9 开始支持 CALL_PAGE_PATH, 低版本请传入 'plugin-private://wxf830863afde621eb/pages/call-page-plugin/call-page-plugin',
})

```

---

## 6. 健康运营指引 / 用户隐私保护 / 插件用户隐私保护说明内容介绍

**Source**: [https://developers.weixin.qq.com/miniprogram/dev/framework/user-privacy/plugin-intro.html](https://developers.weixin.qq.com/miniprogram/dev/framework/user-privacy/plugin-intro.html)

健康运营指引 /用户隐私保护 /插件用户隐私保护说明内容介绍
插件用户隐私保护说明内容介绍

插件用户隐私保护说明包括下列板块，其中具体的说明仅为示例。

插件基本信息

包括插件名称、插件提供方名称。

  插件名称：客服助手
  插件提供方名称: 深圳市腾讯计算机系统有限公司

插件处理的信息

开发者需在此板块声明所处理的用户信息，微信会根据插件版本隐私接口调用情况展示必填项，开发者可自主勾选其他项目。

  - 开发者收集你选中的照片或视频信息，用于在客服会话中发送图片或视频类型的聊天内容。
  - 为了发送语音类型的聊天内容，开发者将在获取你的明示同意后，访问你的麦克风。


隐私接口与对应的处理的信息关系如下：

处理的信息	接口或组件
收集你的昵称、头像	<button open-type="chooseAvatar">、<input type="nickname">、<functional-page-navigator name="loginAndGetUserInfo">、wx.getUserInfo (已回收)
收集你的位置信息	wx.authorizeForMiniProgram({scope:'scope.userLocation'})、wx.getLocation、wx.startLocationUpdate、wx.getFuzzyLocation
收集你选择的位置信息	wx.choosePoi、wx.chooseLocation
收集你的地址	wx.chooseAddress
收集你的发票信息	wx.chooseInvoiceTitle、wx.chooseInvoice
收集你选中的照片或视频信息	wx.chooseImage、wx.chooseMedia、wx.chooseVideo
访问你的麦克风	wx.authorizeForMiniProgram({scope: 'scope.record'})、wx.startRecord、RecorderManager.start、<live-pusher>、wx.joinVoIPChat
访问你的摄像头	wx.authorizeForMiniProgram({scope: 'scope.camera'})、wx.createVKSession、<camera>、<live-pusher>、<voip-room>
访问你的蓝牙	wx.openBluetoothAdapter、wx.createBLEPeripheralServer
使用你的相册（仅写入）权限	wx.authorizeForMiniProgram({scope: 'scope.writePhotosAlbum'})、wx.saveImageToPhotosAlbum、wx.saveVideoToPhotosAlbum
使用你的通讯录（仅写入）权限	wx.addPhoneContact
调用你的加速传感器	wx.startAccelerometer
调用你的磁场传感器	wx.startCompass
调用你的方向传感器	wx.startDeviceMotionListening
调用你的陀螺仪传感器	wx.startGyroscope
读取你的剪切板	wx.setClipboardData、wx.getClipboardData
关于腾讯 文档中心 辟谣中心 客服中心

Copyright © 2012-2026 Tencent. All Rights Reserved.

```text
  插件名称：客服助手
  插件提供方名称: 深圳市腾讯计算机系统有限公司

```

```text
  - 开发者收集你选中的照片或视频信息，用于在客服会话中发送图片或视频类型的聊天内容。
  - 为了发送语音类型的聊天内容，开发者将在获取你的明示同意后，访问你的麦克风。

```

---

## 7. 产品简介 / 多端框架概述

**Source**: [https://developers.weixin.qq.com/miniprogram/dev/platform-capabilities/miniapp/intro/intro](https://developers.weixin.qq.com/miniprogram/dev/platform-capabilities/miniapp/intro/intro)

产品简介 /多端框架概述
小程序多端框架概述

小程序多端框架是支持使用微信小程序技术和微信开发者工具开发移动应用的框架，开发者可以一次编码，分别编译为微信小程序和 Android、 iOS 以及 HarmonyOS 应用，实现多端开发；能帮助企业有效降低多端应用开发的技术门槛和研发成本，以及提升开发效率和开发体验。更多介绍可前往官网查看。

核心特性

基于该框架开发者可以将小程序构建成 Android、 iOS 以及 HarmonyOS 应用

该框架支持条件编译，开发者可灵活兼容小程序和移动应用，可更好地满足企业在不同业务场景下搭建移动应用的需求

此外，基于该框架构建的移动应用可实现接近 iOS 和 Android 原生界面和交互体验，可为用户提供高质量的体验

功能亮点
极致的低门槛。使用微信开发者工具，基于已有的小程序项目，一键即可构建出 Android 与 iOS 应用。
一致的开发体验。支持使用小程序原生语法开发多端应用，支持在微信开发者工具调试、构建多端应用，与开发小程序保持一致开发体验。
完善的工具链与生态服务。微信开发者工具覆盖了多端应用开发、编译、调试、内测分发等完善工具链，并且多端框架内置支持小程序生态服务和腾讯生态服务，一站式为开发者提供全开发生命周期所需的工具与服务。
优秀的用户体验。基于小程序多端框架构建的 Android 与 iOS 应用 可获得媲美原生的交互体验，为用户提供高质量优秀的用户体验。
海量开发者验证。成熟的小程序容器技术与产品方案，经海量的开发者和小程序应用的验证，成熟稳定可靠。
适用范围
可构建为多端应用的小程序：支持使用原生语法开发的微信小程序以及使用其他第三方开发框架开发的微信小程序
如遇到使用其他框架开发的微信小程序无法构建为多端应用，可前往社区联系小助手协助定位问题
免费使用说明
使用小程序多端框架与微信开发者工具的开发、编译、调试、预览等基础版功能永久免费；云构建安装包需消耗较多资源，我们已提供基础发布与更新所需的免费次数。
专业版于公测期可免费升级，详情可查看升级至专业版
部分已上架案例
当前已有较多开发者基于小程序多端框架开发并上架应用，详情可查看部分已上架案例
问题反馈
可前往社区反馈问题，或者向多端应用智能助手咨询。
关于腾讯 文档中心 辟谣中心 客服中心

Copyright © 2012-2026 Tencent. All Rights Reserved.

---

## 8. 健康运营指引 / 用户隐私保护 / 小程序用户隐私保护指引内容介绍

**Source**: [https://developers.weixin.qq.com/miniprogram/dev/framework/user-privacy/miniprogram-intro.html](https://developers.weixin.qq.com/miniprogram/dev/framework/user-privacy/miniprogram-intro.html)

健康运营指引 /用户隐私保护 /小程序用户隐私保护指引内容介绍
小程序用户隐私保护指引内容介绍

本指引依据适用的个人信息保护相关法律法规制定，包括但不限于《中华人民共和国个人信息保护法》等，由开发者根据实际情况填写。

小程序用户隐私保护指引包括下列板块，其中具体的说明仅为示例。

引导语
  本指引是小程序示例小程序开发者”深圳市腾讯计算机系统有限公司“（以下简称“开发者”）为处理你的个人信息而制定。

开发者处理的信息
  根据法律规定，开发者仅处理实现小程序功能所必要的信息。
  - 开发者收集你选中的照片或视频信息，用于用户上传提交代码审核所需要的截图。


开发者需在此板块声明所处理的用户信息，微信会根据小程序版本隐私接口调用情况展示必填项，开发者可自主勾选其他项目。隐私接口与对应的处理的信息关系如下：

处理的信息	接口或组件
收集你的昵称、头像	<button open-type="chooseAvatar">、<input type="nickname">、wx.getUserInfo (已回收)、wx.getUserProfile (已回收)、<button open-type="userInfo">(已回收)
收集你的位置信息	wx.authorize({scope:'scope.userLocation'})、wx.authorize({scope: 'scope.userLocationBackground'})、wx.authorize({scope: 'scope.userFuzzyLocation'})、wx.getLocation、wx.startLocationUpdate、wx.startLocationUpdateBackground、wx.getFuzzyLocation、MapContext.moveToLocation
收集你选择的位置信息	wx.choosePoi、wx.chooseLocation
收集你的地址	wx.chooseAddress
收集你的发票信息	wx.chooseInvoiceTitle、wx.chooseInvoice
收集你的微信运动步数	wx.authorize({scope: 'scope.werun'})、wx.getWeRunData
收集你的手机号	<button open-type="getPhoneNumber">、<button open-type="getRealtimePhoneNumber">
收集你的车牌号	wx.chooseLicensePlate
收集你选中的照片或视频信息	wx.chooseImage、wx.chooseMedia、wx.chooseVideo
收集你选中的文件	wx.chooseMessageFile
访问你的麦克风	wx.authorize({scope: 'scope.record'})、wx.startRecord、RecorderManager.start、<live-pusher>、wx.joinVoIPChat
访问你的摄像头	wx.authorize({scope: 'scope.camera'})、wx.createVKSession、<camera>、<live-pusher>、<voip-room>
访问你的蓝牙	wx.authorize({scope: 'scope.bluetooth'})、wx.openBluetoothAdapter、wx.createBLEPeripheralServer
使用你的相册（仅写入）权限	wx.authorize({scope: 'scope.writePhotosAlbum'})、wx.saveImageToPhotosAlbum、wx.saveVideoToPhotosAlbum
使用你的通讯录（仅写入）权限	wx.authorize({scope: 'scope.addPhoneContact'})、wx.addPhoneContact
使用你的日历（仅写入）权限	wx.authorize({scope: 'scope.addPhoneCalendar'})、wx.addPhoneRepeatCalendar、wx.addPhoneCalendar
调用你的加速传感器	wx.startAccelerometer
调用你的磁场传感器	wx.startCompass
调用你的方向传感器	wx.startDeviceMotionListening
调用你的陀螺仪传感器	wx.startGyroscope
读取你的剪切板	wx.setClipboardData、wx.getClipboardData

平台会对开发者处理信息的目的进行审核，请如实填写。

第三方插件信息
  为实现特定功能，开发者可能会接入由第三方提供的插件。第三方插件的个人信息处理规则，请以其公示的官方说明为准。XXX小程序接入的第三方插件信息如下：
  
  插件名称：客服助手
  插件提供方名称: 深圳市腾讯计算机系统有限公司
  - 开发者收集你选中的照片或视频信息，用于在客服会话中发送图片或视频类型的聊天内容。
  - 为了发送语音类型的聊天内容，开发者将在获取你的明示同意后，访问你的麦克风。


针对由引用了插件的小程序，将会在用户隐私保护指引中展示，展示内容包括插件名称、插件提供方名称与开发者处理的信息及目的。

第三方服务商信息
  小程序助手小程序由深圳市腾讯计算机系统有限公司代为开发，开发者保证深圳市腾讯计算机系统有限公司将在本指引规定范围内处理你的信息。


针对由代开发服务商进行开发的小程序，将会在用户隐私保护指引中进行展示。

用户权益
  1. 关于收集你的位置信息，你可以通过以下路径：小程序主页右上角“…”—“设置”—点击特定信息—点击“不允许”，撤回对开发者的授权。
  2. 关于收集你的手机号、收集你的发票信息，你可以通过以下路径：小程序主页右上角“...” — “设置” — “小程序已获取的信息” — 点击特定信息 — 点击“通知开发者删除”，开发者承诺收到通知后将删除信息。
  3. 关于你的个人信息，你可以通过以下方式与开发者联系，行使查阅、复制、更正、删除等法定权利。
  - 邮箱: miniprogram@tencent.com


微信会根据小程序版本隐私接口调用情况生成第1条与第2条描述，开发者需填写联系方式供用户联系开发者用于行使查阅、复制、更正、删除等法定权利。

若开发者在小程序内提供其他的用户可以行使查阅、复制、更正、删除等法定权利的入口，可以通过补充文档进行说明。

开发者对信息的存储

开发者需声明对信息的存储期限，如

  固定存储期限：180天

信息的使用规则
  1. 开发者将会在本指引所明示的用途内使用收集的信息。
  2. 如开发者使用你的信息超出本指引目的或合理范围，开发者必须在变更使用目的或范围前，再次以弹窗方式告知并征得你的明示同意。

信息对外提供
  1. 开发者承诺，不会主动共享或转让你的信息至任何第三方，如存在确需共享或转让时，开发者应当直接征得或确认第三方征得你

... (content truncated)

```text
  本指引是小程序示例小程序开发者”深圳市腾讯计算机系统有限公司“（以下简称“开发者”）为处理你的个人信息而制定。

```

```text
  根据法律规定，开发者仅处理实现小程序功能所必要的信息。
  - 开发者收集你选中的照片或视频信息，用于用户上传提交代码审核所需要的截图。

```

```text
  为实现特定功能，开发者可能会接入由第三方提供的插件。第三方插件的个人信息处理规则，请以其公示的官方说明为准。XXX小程序接入的第三方插件信息如下：
  
  插件名称：客服助手
  插件提供方名称: 深圳市腾讯计算机系统有限公司
  - 开发者收集你选中的照片或视频信息，用于在客服会话中发送图片或视频类型的聊天内容。
  - 为了发送语音类型的聊天内容，开发者将在获取你的明示同意后，访问你的麦克风。

```

---

## 9. 产品简介

**Source**: [https://developers.weixin.qq.com/miniprogram/dev/wxcloudservice/wxcloudrun/src/basic/intro.html](https://developers.weixin.qq.com/miniprogram/dev/wxcloudservice/wxcloudrun/src/basic/intro.html)

微信云托管
微信云托管是什么？

微信云托管 是微信团队提供的以云原生为基础的，免运维、高可用服务上云解决方案，无需服务器，1分钟即可部署小程序/公众号服务端。

微信云托管支持目前绝大多数语言/框架项目，开发者可以从服务器平滑迁移；并且微信云托管的自动运维和扩缩容特性，无需开发者关心服务的可用性，专注于业务，极大节省人力和服务资源成本。

同时，微信云托管还集成持续交付部署，DevOps自动化，安全鉴权等众多能力，致力于帮助没有深层运维经验的业务开发者和研发团队，用最低的成本，打造出稳定性高，安全性强的后端服务。

在微信云托管的助力下，项目服务可以达到和专业运维团队支撑一样的效果，同时又极大的节省人力和服务成本。

最重要的，微信云托管与微信生态深度融合，具有免鉴权，云调用，消息推送，微信支付等众多微信优势特性，开发者可以非常轻松和高效的完成互通，并且在安全、可靠性方面有微信团队的专业保障。

微信云托管能带来什么？与传统的服务器部署模式相比有什么优势？

微信云托管的高可用，免运维的基本特性，加上独家提供的微信生态核心能力，使得其在服务上云中有非常突出的优势。

1. 网络加速与网络安全

低网络延迟： 客户端请求从微信就近节点经过微信专线到达服务，服务端内网专线访问微信接口。
免费防DDoS攻击： 服务端接口可以禁止公网访问，只接受客户端请求通过专线访问，从根本上杜绝DDoS可能且无需支付额外费用。（专线安全性由微信团队支持，与微信客户端安全级别相同）
天然免鉴权：项目服务可以直接获取微信服务端接口令牌，由小程序或公众号端发送的请求，免鉴权直接获取用户信息。
开放接口服务：提供所有微信服务端接口的免密中转，集成「微信支付」，无需加解密处理。
消息推送服务：微信生态内各种消息，可配置多个服务和具体路径来接收，无需关心消息的加密和解密。

对APP和web网站的专线访问功能暂未上线，敬请期待。 必须禁止服务公网访问，才可获得DDoS防护能力。使用公网访问方式遭到攻击或损失不在微信云托管责任范围之内。

2. 初创业务、流量不稳定触发型业务大幅降低成本

自动扩缩容：服务可以根据流量多少和自身承载消耗动态的进行扩缩容，保证服务高可用、高稳定。
极速响应率：高并发场景下可在 10s-20s 自动快速扩容（增加实例副本数）并支持业务稳定运行，事前事中时候均无需人工操作。
无闲置成本：无业务流量时，实例副本数支持缩容到0，做到不用不花钱。
3. 免除服务器运维工作，业务发布又快又稳

自动流水线：提供流水线能力，可以实现从代码仓库到服务发布的全自动流程，无需反复登录控制台操作。
部署安全可控：提供灰度发布、定向开发测试、版本回滚等多样部署能力，业务更新迭代更稳更安全。
机器人提醒：提供企业微信机器人提醒，第一时间告知发布情况。
日志系统：对服务运行提供实时日志收集和查询能力，支持多种检索语法。
资源监控：实时反映环境各个服务和各种资源的使用消耗情况，以及服务内版本运行的具体情况。
资源告警：提供丰富的告警渠道，实时感知环境资源使用的各项指标运行情况，支持自定义规则。
集成SDK：小程序和公众号开发接入，可直接使用自带的SDK操作，无需自己封装。
4. 服务端所需资源一站式管理

MySql：提供「Serverless形态的Mysql」，根据业务使用需求自动扩缩容，不产生瓶颈；
对象存储：简单配置就可以在服务内和客户端使用，自带安全域名校验，CDN缓存加速和其他安全能力；
可延展性：可以结合其他云资源搭配使用，随心选择合适的云上资源，打造自己的服务体系。
从服务器迁移到云托管复杂吗？
低改造成本：传统服务几乎无需改造成本，可快速迁移存量业务；
支持微服务：支持东西向通信微服务和服务常驻，灵活设定，内网隔离；
自定义域名：服务可以解析到自有域名，支持开启HTTPS，还有更多网关相关能力；
如何使用微信云托管？
快速开始：建议你先阅读「快速开始」，先整体体验了解一下微信云托管的各项功能。
使用指南：在具体使用平台的时候，可以直接从控制台获得「使用指南」的具体链接，来学习如何操作。
开发指引：在开发业务代码时，对于云托管平台的操作，可以具体阅读「开发指引」。
模版部署：如果你无法开始你的项目，或者改造你过于传统的项目，可以在「一键部署模版」下选择与你最匹配的语言或框架，如果没有你想要的，可以联系我们提供帮助。
官方教程 · 快速上手微信云托管
微信云托管是为开发者提供的后端服务云原生解决方案，支持托管任意语言及框架的容器化应用，创建环境即可享受能自动扩缩容的容器资源，用户可面向代码/镜像等方式使用，免服务器、免运维。
关于腾讯 文档中心 辟谣中心 客服中心

Copyright © 2012-2026 Tencent. All Rights Reserved.

---

## 10. Skyline 渲染引擎 / 概览 / 介绍

**Source**: [https://developers.weixin.qq.com/miniprogram/dev/framework/runtime/skyline/introduction.html](https://developers.weixin.qq.com/miniprogram/dev/framework/runtime/skyline/introduction.html)

Skyline 渲染引擎 /概览 /介绍
简介

小程序一直以来采用的都是 AppService 和 WebView 的双线程模型，基于 WebView 和原生控件混合渲染的方式，小程序优化扩展了 Web 的基础能力，保证了在移动端上有良好的性能和用户体验。Web 技术至今已有 30 多年历史，作为一款强大的渲染引擎，它有着良好的兼容性和丰富的特性。 尽管各大厂商在不断优化 Web 性能，但由于其繁重的历史包袱和复杂的渲染流程，使得 Web 在移动端的表现与原生应用仍有一定差距。

为了进一步优化小程序性能，提供更为接近原生的用户体验，我们在 WebView 渲染之外新增了一个渲染引擎 Skyline，其使用更精简高效的渲染管线，并带来诸多增强特性，让 Skyline 拥有更接近原生渲染的性能体验。

架构

当小程序基于 WebView 环境下时，WebView 的 JS 逻辑、DOM 树创建、CSS 解析、样式计算、Layout、Paint (Composite) 都发生在同一线程，在 WebView 上执行过多的 JS 逻辑可能阻塞渲染，导致界面卡顿。以此为前提，小程序同时考虑了性能与安全，采用了目前称为「双线程模型」的架构。

在 Skyline 环境下，我们尝试改变这一情况：Skyline 创建了一条渲染线程来负责 Layout, Composite 和 Paint 等渲染任务，并在 AppService 中划出一个独立的上下文，来运行之前 WebView 承担的 JS 逻辑、DOM 树创建等逻辑。这种新的架构相比原有的 WebView 架构，有以下特点：

界面更不容易被逻辑阻塞，进一步减少卡顿
无需为每个页面新建一个 JS 引擎实例（WebView），减少了内存、时间开销
框架可以在页面之间共享更多的资源，进一步减少运行时内存、时间开销
框架的代码之间无需再通过 JSBridge 进行数据交换，减少了大量通信时间开销

而与此同时，这个新的架构能很好地保持和原有架构的兼容性，基于 WebView 环境的小程序代码基本上无需任何改动即可直接在新的架构下运行。WXS 由于被移到 AppService 中，虽然逻辑本身无需改动，但询问页面信息等接口会变为异步，效率也可能有所下降；为此，我们同时推出了新的 Worklet 机制，它比原有的 WXS 更靠近渲染流程，用以高性能地构建各种复杂的动画效果。

新的渲染流程如下图所示：

需要帮助

如果在使用过程中遇到任何问题，可以前往「Skyline 渲染引擎」专区查看说明。

关于腾讯 文档中心 辟谣中心 客服中心

Copyright © 2012-2026 Tencent. All Rights Reserved.

---

## 11. Skyline 渲染引擎 / 从 WebView 迁移 / 起步

**Source**: [https://developers.weixin.qq.com/miniprogram/dev/framework/runtime/skyline/migration/](https://developers.weixin.qq.com/miniprogram/dev/framework/runtime/skyline/migration/)

Skyline 渲染引擎 /从 WebView 迁移 /起步
环境准备

Skyline 具体支持版本如下：

微信安卓客户端 8.0.33 或以上版本（对应基础库为 2.30.4 或以上版本）
微信 iOS 客户端 8.0.34 或以上版本（对应基础库为 2.31.1 或以上版本）
开发者工具 Stable 1.06.2307260 或以上版本（建议使用 Nightly 最新版）

扫码快速确认环境是否正确

使用开发者工具调试

开发者工具提供了对齐移动端的 Skyline 渲染引擎，支持 WXML 调试、 WXSS 样式错误提示、新增的特性等

按以下步骤切换到 Skyline 模式：

在 app.json 或 page.json 中配上 renderer: skyline，并按下一节添加好配置项，或者按开发者工具的提示逐个加上配置项
确保右上角 > 详情 > 本地设置里的 开启 Skyline 渲染调试 选项被勾选上
使用 worklet 动画特性时，确保右上角 > 详情 > 本地设置里的 编译 worklet 代码 选项被勾选上 (代码包体积会少量增加)
调试基础库切到 3.0.0 或以上版本

若切换期间出现报错、白屏等问题，可尝试重启开发者工具解决

已知问题：热重载暂未支持

此时，在模拟器左上角能够看到当前的 renderer 为 skyline，见下图

开始迁移

迁移到 Skyline，无需大动干弋，我们保持了上层框架的语法、接口基本不变，只需要做局部的调整，主要是加强了 WXSS 样式、内置组件及部分特性的约束，基本流程如下：

在 app.json 加上如下必要配置项，若只想在某些页面开启，可将 renderer componentFramework 配置在页面 json 中
"lazyCodeLoading": "requiredComponents",
"renderer": "skyline",
"componentFramework": "glass-easel",
"rendererOptions": {
  "skyline": {
    "defaultDisplayBlock": true,
    "defaultContentBox": true,
    "tagNameStyleIsolation": "legacy",
    "enableScrollViewAutoSize": true,
    "keyframeStyleIsolation": "legacy"
  }
}

进行组件与 WXSS 适配，参考 Skyline 基础组件支持与差异、Skyline WXSS 样式支持与差异

参考代码模板

按照指引适配后，可以保证在微信低版本或 PC 端 fallback 到 WebView 渲染时，也能表现正确

更多详细指引参考 最佳实践 和 兼容建议

在真机上预览效果

由于 Skyline 默认接入 We 分析的 AB 实验，未配置的情况下，页面渲染仍为 WebView 引擎，可通过以下方式正确切到 Skyline 渲染

配置 We 分析 AB 实验，加上白名单，操作步骤详见下节
关闭 We 分析 AB 实验，默认启用 Skyline 渲染，配置方式详见此处第 2 点
通过快捷切换入口，强切到 Skyline 渲染，操作步骤详见下节
配置 We 分析 AB 实验

迁移完 Skyline 之后，为了让开发者能够针对 Skyline 逐步灰度放量，并且与 WebView 对比性能表现，我们在 We 分析 提供了 AB 实验机制。

因此，需要在 We 分析 配置之后，小程序用户才可以命中 Skyline 渲染，需要注意的是，小程序开发者也会受 AB 实验影响。操作步骤如下：

首先，进入 We 分析，在 AB 实验 > 实验看板，点击“新建实验”

接着，实验类型选择 小程序基础库实验，然后按需选择实验层级并分配流量，如果是小范围调试，可分配 0% 流量，并在 Skyline 渲染 的实验分组里填上测试微信号

最后，创建实验即可生效。后续经 AB 实验验证稳定后，需在 We 分析上先关闭实验再选择 Skyline 全量

点击查看更多 We 分析 AB 实验相关内容

快捷切换入口

考虑到本地调试时，配置 AB 实验会稍微繁琐一些，并且也会需要对比 WebView 的表现，我们提供了快捷切换渲染引擎的入口。

该入口只对开发版/体验版小程序生效，入口为：小程序菜单 > 开发调试 > Switch Render，会出现三个选项，说明如下：

Auto ：跟随 AB 实验，即对齐小程序正式用户的表现
WebView ：强制切为 WebView 渲染。强切后，开发版、体验版、正式版均为 WebView 渲染，需手动切到 Auto 才能恢复
Skyline ：若当前页面已迁移到 Skyline，则强制切为 Skyline 渲染。强切后，开发版、体验版、正式版均为 Skyline 渲染，需手动切到 Auto 才能恢复

如何识别当前页面是否使用 Skyline

通过客户端菜单：

打开开发版/体验版小程序，点击菜单即可查看当前页面是否使用 Skyline 渲染。 

通过 vConsole 按钮的右上角的红底文案识别

vConsole 的路由日志

路由日志中会包含页面路由的目标页面、路由类型和目标页面的渲染后端。

一个可能的日志形如：On app route: pages/index/index (navigateTo), renderer: skyline，代表通过 navigateTo 跳转到了 pages/index/index，渲染后端为 skyline

通过接口判断

页面和自定义组件示例上有属性 renderer，可以用于判断当前组件的实际渲染后端，如：

Page({
  onLoad() {
    console.log(this.renderer)
  }
})

关于腾讯 文档中心 辟谣中心 客服中心

Copyright © 2012-2026 Tencent. All Rights Reserved.

```json
"lazyCodeLoading": "requiredComponents",
"renderer": "skyline",
"componentFramework": "glass-easel",
"rendererOptions": {
  "skyline": {
    "defaultDisplayBlock": true,
    "defaultContentBox": true,
    "tagNameStyleIsolation": "legacy",
    "enableScrollViewAutoSize": true,
    "keyframeStyleIsolation": "legacy"
  }
}

```

```js
Page({
  onLoad() {
    console.log(this.renderer)
  }
})

```

---

