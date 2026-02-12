/**
 * 伴侣服务 - 负责生成温暖的对话回应
 * 使用智谱 AI GLM 系列模型
 */

import { ZhipuAI } from 'zhipuai-sdk-nodejs-v4';
import { PERSONALITY_PROMPT, SCENE_TEMPLATES } from './prompts/personality';

interface CompanionContext {
  taskName?: string;
  progress?: number;
  userMessage?: string;
  scene?: {
    type: string;
    mood: string;
    needsPhoto: boolean;
  };
}

export class CompanionService {
  private client: ZhipuAI;
  private conversationHistory: Array<{ role: string; content: string }> = [];

  constructor(apiKey: string) {
    this.client = new ZhipuAI({ apiKey });
  }

  /**
   * 生成陪伴回应
   */
  async generateResponse(context: CompanionContext): Promise<string> {
    const { taskName, progress, userMessage, scene } = context;

    // 构建系统提示词
    const systemPrompt = this.buildSystemPrompt(context);

    // 构建用户消息
    const userPrompt = this.buildUserPrompt(context);

    try {
      const response = await this.client.createCompletions({
        model: 'glm-4-flash',  // 修正：全小写
        messages: [
          { role: 'system', content: systemPrompt },
          ...this.conversationHistory.slice(-6), // 保留最近3轮对话
          { role: 'user', content: userPrompt }
        ],
        temperature: 0.9, // 增加一点随机性，让回应更自然
        max_tokens: 200 // 控制回应长度
      });

      const reply = response.choices[0].message.content || '我在这里陪着你～';

      // 更新对话历史
      this.conversationHistory.push(
        { role: 'user', content: userPrompt },
        { role: 'assistant', content: reply }
      );

      return reply;
    } catch (error) {
      console.error('Failed to generate response:', error);
      return this.getFallbackResponse(context);
    }
  }

  /**
   * 纯对话模式
   */
  async chat(message: string): Promise<string> {
    try {
      const response = await this.client.createCompletions({
        model: 'glm-4-flash',  // 修正：全小写
        messages: [
          { role: 'system', content: PERSONALITY_PROMPT },
          ...this.conversationHistory.slice(-6),
          { role: 'user', content: message }
        ],
        temperature: 0.9,
        max_tokens: 300
      });

      const reply = response.choices[0].message.content || '我在听～';

      this.conversationHistory.push(
        { role: 'user', content: message },
        { role: 'assistant', content: reply }
      );

      return reply;
    } catch (error) {
      console.error('Chat error:', error);
      return '抱歉，我刚才走神了，能再说一遍吗？';
    }
  }

  /**
   * 分析图片内容（使用 glm-4v-flash 多模态模型）
   */
  async analyzeImage(imageUrl: string, question: string = '描述这张图片'): Promise<string> {
    try {
      const response = await this.client.createCompletions({
        model: 'glm-4v-flash',  // 修正：全小写
        messages: [
          {
            role: 'user',
            content: [
              {
                type: 'image_url',
                image_url: {
                  url: imageUrl
                }
              },
              {
                type: 'text',
                text: question
              }
            ]
          }
        ]
      });

      return response.choices[0].message.content || '无法分析图片';
    } catch (error) {
      console.error('Image analysis error:', error);
      return '抱歉，图片分析失败了';
    }
  }

  /**
   * 构建系统提示词
   */
  private buildSystemPrompt(context: CompanionContext): string {
    let prompt = PERSONALITY_PROMPT;

    if (context.scene) {
      const sceneTemplate = SCENE_TEMPLATES[context.scene.type];
      if (sceneTemplate) {
        prompt += `\n\n当前场景：${sceneTemplate.description}`;
        prompt += `\n回应风格：${sceneTemplate.style}`;
      }
    }

    return prompt;
  }

  /**
   * 构建用户消息
   */
  private buildUserPrompt(context: CompanionContext): string {
    const parts: string[] = [];

    if (context.taskName) {
      parts.push(`正在执行任务：${context.taskName}`);
    }

    if (context.progress !== undefined) {
      parts.push(`任务进度：${Math.round(context.progress * 100)}%`);
    }

    if (context.userMessage) {
      parts.push(`用户说：${context.userMessage}`);
    }

    if (context.scene?.needsPhoto) {
      parts.push('（你准备分享一张生活照片）');
    }

    return parts.join('\n') || '用户正在等待...';
  }

  /**
   * 降级回应（API 失败时使用）
   */
  private getFallbackResponse(context: CompanionContext): string {
    if (context.progress !== undefined) {
      if (context.progress < 0.3) {
        return '任务刚开始，我会陪着你的～';
      } else if (context.progress < 0.7) {
        return '进行得很顺利！再等一会儿就好～';
      } else {
        return '快完成了！马上就好～';
      }
    }

    if (context.userMessage) {
      if (context.userMessage.includes('累') || context.userMessage.includes('疲')) {
        return '辛苦啦！要不要休息一下？';
      }
      if (context.userMessage.includes('好') || context.userMessage.includes('顺利')) {
        return '太好了！继续加油～';
      }
    }

    return '我在这里陪着你～有什么需要帮忙的吗？';
  }

  /**
   * 清空对话历史
   */
  clearHistory(): void {
    this.conversationHistory = [];
  }
}
