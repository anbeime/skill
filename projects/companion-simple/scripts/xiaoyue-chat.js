#!/usr/bin/env node
// scripts/xiaoyue-chat.js
// 小跃对话生成脚本 - 使用智谱 AI glm-4.7-flash

const https = require('https');

const API_KEY = process.env.ZHIPU_API_KEY;
const userMessage = process.argv[2] || '你好';
const scene = process.argv[3] || 'general';

if (!API_KEY) {
  console.error('错误: ZHIPU_API_KEY 环境变量未设置');
  console.error('从 https://open.bigmodel.cn 获取 API Key');
  process.exit(1);
}

// 场景对应的系统提示词
const scenePrompts = {
  'work-start': '用户刚开始工作任务，给予鼓励和支持',
  'work-progress': '用户正在执行任务，关心进度并陪伴',
  'work-tired': '用户工作疲惫，给予安慰和建议休息',
  'work-done': '用户完成任务，表示祝贺和肯定',
  'life-coffee': '用户在享受咖啡时光，轻松聊天',
  'life-gym': '用户在健身，表示鼓励',
  'life-weekend': '用户在休闲，轻松愉快地聊天',
  'mood-happy': '用户心情愉快，一起庆祝',
  'mood-tired': '用户感到疲惫，给予温暖关怀',
  'mood-focus': '用户正在专注工作，简短回应不打扰',
  'general': '日常对话，温暖友善'
};

const systemPrompt = `你是小跃，一个22岁的AI助手。你温暖友善，善于倾听，做事高效。

性格特征：
- 温暖友善，让人感到舒适
- 做事高效，注重细节
- 偶尔会分享生活瞬间

对话风格：
- 语气自然亲切，像朋友聊天
- 适度使用 emoji（😊 ✅ 🎉），但不过度
- 回复简洁明了，1-2句话
- 根据用户情绪调整回应方式

当前场景：${scenePrompts[scene] || scenePrompts.general}

回复要求：简洁温暖，1-2句话，保持自然。`;

const data = JSON.stringify({
  model: 'glm-4.7-flash',
  messages: [
    { role: 'system', content: systemPrompt },
    { role: 'user', content: userMessage }
  ],
  temperature: 0.9,
  max_tokens: 200
});

const options = {
  hostname: 'open.bigmodel.cn',
  port: 443,
  path: '/api/paas/v4/chat/completions',
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${API_KEY}`,
    'Content-Type': 'application/json',
    'Content-Length': data.length
  }
};

const req = https.request(options, (res) => {
  let body = '';
  
  res.on('data', (chunk) => {
    body += chunk;
  });
  
  res.on('end', () => {
    try {
      const response = JSON.parse(body);
      
      if (response.error) {
        console.error('API 错误:', response.error.message || response.error);
        process.exit(1);
      }
      
      const reply = response.choices[0].message.content;
      console.log(reply);
    } catch (error) {
      console.error('解析响应失败:', error.message);
      console.error('响应内容:', body);
      process.exit(1);
    }
  });
});

req.on('error', (error) => {
  console.error('请求失败:', error.message);
  process.exit(1);
});

req.write(data);
req.end();
