# Components

*1 pages in this category*

## Table of Contents

1. [视图容器](#1-视图容器)

---

## 1. 视图容器

**Source**: [https://developers.weixin.qq.com/miniprogram/dev/component/](https://developers.weixin.qq.com/miniprogram/dev/component/)

以下服务端接口可免 access_token 调用的场景：使用微信云托管通过微信令牌/开放接口服务调用；使用微信云开发通过云函数免服务器发起云调用。  

视图容器

	名称	功能
	cover-image	覆盖在原生组件之上的图片视图
	cover-view	覆盖在原生组件之上的文本视图
	match-media	media query 匹配检测节点
	movable-area	movable-view的可移动区域
	movable-view	可移动的视图容器，在页面中可以拖拽滑动
	page-container	页面容器
	root-portal	使整个子树从页面中脱离出来，类似于在 CSS 中使用 fixed position 的效果
	scroll-view	可滚动视图区域
	swiper	滑块视图容器
	swiper-item	仅可放置在swiper组件中，宽高自动设置为100%
	view	视图容器

	名称	功能
	cover-image	覆盖在原生组件之上的图片视图
	cover-view	覆盖在原生组件之上的文本视图
	match-media	media query 匹配检测节点
	movable-area	movable-view的可移动区域
	movable-view	可移动的视图容器，在页面中可以拖拽滑动
	page-container	页面容器
	root-portal	使整个子树从页面中脱离出来，类似于在 CSS 中使用 fixed position 的效果
	scroll-view	可滚动视图区域
	swiper	滑块视图容器
	swiper-item	仅可放置在swiper组件中，宽高自动设置为100%
	view	视图容器

基础内容

基础内容

	名称	功能
	icon	图标组件
	progress	进度条
	rich-text	富文本
	selection	局部文本选区
	text	文本

表单组件

	名称	功能
	button	按钮
	checkbox	多选项目
	checkbox-group	多项选择器，内部由多个checkbox组成
	editor	富文本编辑器，可以对图片、文字进行编辑
	editor-portal	渲染 editor 组件的自定义区块
	form	表单
	input	输入框
	keyboard-accessory	设置 input / textarea 聚焦时键盘上方 cover-view / cover-image 工具栏视图
	label	用来改进表单组件的可用性
	picker	从底部弹起的滚动选择器
	picker-view	嵌入页面的滚动选择器
	picker-view-column	滚动选择器子项
	radio	单选项目
	radio-group	单项选择器，内部由多个 radio 组成
	slider	滑动选择器
	switch	开关选择器
	textarea	多行输入框

Skyline

	名称	功能
	手势系统	
	
	名称	功能
	double-tap-gesture-handler	双击时触发手势
	force-press-gesture-handler	iPhone 设备重按时触发手势
	horizontal-drag-gesture-handler	横向滑动时触发手势
	long-press-gesture-handler	长按时触发手势
	pan-gesture-handler	拖动（横向/纵向）时触发手势
	scale-gesture-handler	多指缩放时触发手势
	tap-gesture-handler	点击时触发手势
	vertical-drag-gesture-handler	纵向滑动时触发手势

	draggable-sheet	半屏可拖拽组件
	grid-builder	网格构造器，仅支持作为 <scroll-view type="custom"> 模式的直接子节点
	grid-view	Skyline 下网格布局容器 和 瀑布流布局容器
	list-builder	列表构造器，仅支持作为 <scroll-view type="custom"> 模式的直接子节点
	list-view	列表布局容器，仅支持作为 <scroll-view type="custom"> 模式的直接子节点或 sticky-section 组件直接子节点
	nested-scroll-body	嵌套 scroll-view 场景中属于里层 scroll-view 的节点，仅支持作为 <scroll-view type="nested"> 模式的直接子节点
	nested-scroll-header	嵌套 scroll-view 场景中属于外层 scroll-view 的节点，仅支持作为 <scroll-view type="nested"> 模式的直接子节点
	open-container	容器转场动画组件
	open-data-item	展示微信开放数据，需配合 open-data-list 组件使用
	open-data-list	展示微信开放数据
	share-element	共享元素
	snapshot	截图组件
	span	用于支持内联文本和 image / navigator 的混排
	sticky-header	吸顶布局容器，仅支持作为 <scroll-view type="custom"> 模式的直接子节点或 sticky-section 组件直接子节点
	sticky-section	吸顶布局容器，仅支持作为 <scroll-view type="custom"> 模式的直接子节点

导航

	名称	功能
	functional-page-navigator	仅在插件中有效，用于跳转到插件功能页
	navigator	页面链接

媒体组件

	名称	功能
	audio	音频
	camera	系统相机
	channel-live	小程序内嵌视频号直播组件，展示视频号直播状态和封面，并无弹窗跳转至视频号
	channel-video	小程序内嵌视频号视频组件，支持在小程序中播放视频号视频，并无弹窗跳转至视频号
	image	图片
	live-player	实时音视频播放（v2.9.1 起支持同层渲染）
	live-pusher	实时音视频录制（v2.9.1 起支持同层渲染）
	video	视频（v2.4.0 起支持同层渲染）
	voip-room	多人音视频对话

地图

	名称	功能
	map	地图 v2.7.0 起支持同层渲染

画布

	名称	功能
	canvas	画布

开放能力

	名称	功能
	web-view	承载网页的容器
	ad	Banner 广告
	ad-custom	原生模板 广告
	official-account	公众号关注组件
	official-account-publish	公众号图文组件
	open-data	用于展示微信开放的数据
	store-coupon	小程序内嵌微信小店优惠券，展示小店优惠券，并进行跳转交易
	store-gift	小程序送礼

... (content truncated)

---

