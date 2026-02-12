/**
 * 小跃虚拟伴侣 Skill - 主入口
 * 为 OpenClaw 提供虚拟伴侣能力
 */

import { CompanionService } from './companion';
import { ImageGenerator } from './image-generator';
import { SceneDetector } from './scene-detector';

interface SkillInput {
  action: 'accompany' | 'generate-photo' | 'chat';
  context?: {
    taskName?: string;
    progress?: number;
    userMessage?: string;
  };
  scene?: string;
  mood?: string;
  message?: string;
}

interface SkillOutput {
  success: boolean;
  message?: string;
  imageUrl?: string;
  error?: string;
}

export async function execute(input: SkillInput): Promise<SkillOutput> {
  try {
    const apiKey = process.env.ZHIPU_API_KEY;
    if (!apiKey) {
      throw new Error('ZHIPU_API_KEY not configured');
    }

    const companion = new CompanionService(apiKey);
    const imageGenerator = new ImageGenerator(apiKey);
    const sceneDetector = new SceneDetector();

    switch (input.action) {
      case 'accompany': {
        // 任务陪伴模式
        const { taskName, progress, userMessage } = input.context || {};
        
        // 检测场景
        const scene = sceneDetector.detectScene(userMessage || '', progress || 0);
        
        // 生成回应
        const response = await companion.generateResponse({
          taskName,
          progress,
          userMessage,
          scene
        });

        // 如果需要图片，生成图片
        let imageUrl: string | undefined;
        if (scene.needsPhoto) {
          imageUrl = await imageGenerator.generate({
            scene: scene.type,
            mood: scene.mood
          });
        }

        return {
          success: true,
          message: response,
          imageUrl
        };
      }

      case 'generate-photo': {
        // 纯图片生成
        const imageUrl = await imageGenerator.generate({
          scene: input.scene || 'work',
          mood: input.mood || 'neutral'
        });

        return {
          success: true,
          imageUrl
        };
      }

      case 'chat': {
        // 纯对话模式
        const response = await companion.chat(input.message || '');
        
        return {
          success: true,
          message: response
        };
      }

      default:
        throw new Error(`Unknown action: ${input.action}`);
    }
  } catch (error) {
    console.error('Skill execution error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}

// 导出类型供外部使用
export type { SkillInput, SkillOutput };
