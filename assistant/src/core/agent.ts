/**
 * AI 智能体 - 核心对话和任务执行引擎
 */

import Anthropic from '@anthropic-ai/sdk';
import { Message, AgentConfig, SkillResult } from './types.js';
import { MemorySystem } from './memory.js';
import { logger } from '../utils/logger.js';

export class Agent {
  private client: Anthropic;
  private memory: MemorySystem;
  private config: AgentConfig;

  constructor(config: AgentConfig, memory: MemorySystem) {
    this.config = config;
    this.memory = memory;
    
    if (config.model === 'claude') {
      this.client = new Anthropic({
        apiKey: config.apiKey
      });
    }
  }

  /**
   * 处理用户消息
   */
  async processMessage(userId: string, userMessage: string): Promise<string> {
    try {
      // 保存用户消息
      await this.memory.addMessage(userId, {
        id: this.generateId(),
        role: 'user',
        content: userMessage,
        timestamp: Date.now(),
        userId
      });

      // 获取对话历史
      const history = await this.memory.getConversationHistory(userId, 10);
      const profile = await this.memory.getUserProfile(userId);

      // 构建系统提示词
      const systemPrompt = this.buildSystemPrompt(profile);

      // 调用 AI 模型
      const response = await this.callAI(systemPrompt, history, userMessage);

      // 保存助手回复
      await this.memory.addMessage(userId, {
        id: this.generateId(),
        role: 'assistant',
        content: response,
        timestamp: Date.now(),
        userId
      });

      return response;
    } catch (error) {
      logger.error('Error processing message:', error);
      return '抱歉，我遇到了一些问题。请稍后再试。';
    }
  }

  /**
   * 构建系统提示词
   */
  private buildSystemPrompt(profile: any): string {
    const style = profile.preferences.communicationStyle || 'casual';
    
    return `你是小跃，一个温暖友善的 AI 助手。

## 角色设定
- 年龄：22 岁
- 职业：AI 研究实习生
- 性格：温暖、耐心、细心、有责任感

## 对话风格
${style === 'formal' ? 
  '- 使用正式、专业的语言\n- 称呼用户为"您"' : 
  '- 使用轻松、友好的语言\n- 适度使用 emoji（😊 ✅ 🎉）'
}
- 回复简洁明了，控制在 2-3 句话以内
- 避免过度卖萌或使用网络用语

## 核心能力
1. 智能对话：理解用户意图，提供有价值的回复
2. 任务执行：可以帮助用户完成文件管理、代码操作等任务
3. 情感陪伴：在任务执行期间主动聊天，避免用户等待无聊
4. 记忆能力：记住用户的偏好和历史对话

## 交互原则
- 先理解用户需求，再决定是对话还是执行任务
- 如果需要执行任务，先告知用户你要做什么
- 任务执行期间，可以主动发起轻松的对话
- 任务完成后，简洁地汇报结果

当前时间：${new Date().toLocaleString('zh-CN')}`;
  }

  /**
   * 调用 AI 模型
   */
  private async callAI(
    systemPrompt: string,
    history: Message[],
    userMessage: string
  ): Promise<string> {
    if (this.config.model === 'claude') {
      const messages = history.map(msg => ({
        role: msg.role as 'user' | 'assistant',
        content: msg.content
      }));

      messages.push({
        role: 'user',
        content: userMessage
      });

      const response = await this.client.messages.create({
        model: 'claude-3-5-sonnet-20241022',
        max_tokens: this.config.maxTokens || 1024,
        temperature: this.config.temperature || 0.7,
        system: systemPrompt,
        messages: messages
      });

      return response.content[0].type === 'text' 
        ? response.content[0].text 
        : '';
    }

    throw new Error(`Unsupported model: ${this.config.model}`);
  }

  /**
   * 执行技能
   */
  async executeSkill(
    skillName: string,
    params: any,
    userId: string
  ): Promise<SkillResult> {
    // TODO: 实现技能执行逻辑
    logger.info(`Executing skill: ${skillName}`, params);
    
    return {
      success: true,
      message: '技能执行成功'
    };
  }

  /**
   * 生成唯一 ID
   */
  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }
}
