/**
 * 示例：如何使用小跃助手
 */

import { Agent } from './core/agent.js';
import { MemorySystem } from './core/memory.js';
import { ImageGenerator } from './companion/image.js';

// 初始化组件
const memory = new MemorySystem('./data/memory.json');
await memory.initialize();

const agent = new Agent(
  {
    model: 'claude',
    apiKey: process.env.ANTHROPIC_API_KEY || '',
    temperature: 0.7
  },
  memory
);

const imageGen = new ImageGenerator(process.env.FAL_KEY || '');

// 示例 1: 基础对话
async function example1() {
  console.log('=== 示例 1: 基础对话 ===\n');
  
  const userId = 'demo-user-001';
  
  const response1 = await agent.processMessage(userId, '你好小跃');
  console.log('小跃:', response1);
  
  const response2 = await agent.processMessage(userId, '你能帮我做什么？');
  console.log('小跃:', response2);
}

// 示例 2: 记忆功能
async function example2() {
  console.log('\n=== 示例 2: 记忆功能 ===\n');
  
  const userId = 'demo-user-002';
  
  // 设置用户偏好
  await memory.updatePreferences(userId, {
    communicationStyle: 'casual',
    favoriteTools: ['VS Code', 'Git'],
    workingHours: '9:00-18:00'
  });
  
  const response = await agent.processMessage(
    userId,
    '我喜欢用什么工具？'
  );
  console.log('小跃:', response);
}

// 示例 3: 图片生成
async function example3() {
  console.log('\n=== 示例 3: 图片生成 ===\n');
  
  try {
    const imageUrl = await imageGen.generateSceneImage(
      'coffee',
      'https://cdn.example.com/reference.png'
    );
    console.log('生成的图片:', imageUrl);
  } catch (error) {
    console.log('图片生成需要配置 FAL_KEY');
  }
}

// 示例 4: 对话历史
async function example4() {
  console.log('\n=== 示例 4: 对话历史 ===\n');
  
  const userId = 'demo-user-003';
  
  await agent.processMessage(userId, '今天天气真好');
  await agent.processMessage(userId, '我想去公园散步');
  
  const history = await memory.getConversationHistory(userId);
  console.log('对话历史:', JSON.stringify(history, null, 2));
}

// 运行所有示例
async function runExamples() {
  try {
    await example1();
    await example2();
    await example3();
    await example4();
    
    console.log('\n=== 统计信息 ===');
    console.log(memory.getStats());
  } catch (error) {
    console.error('Error:', error);
  }
}

// 如果直接运行此文件
if (import.meta.url === `file://${process.argv[1]}`) {
  runExamples();
}
