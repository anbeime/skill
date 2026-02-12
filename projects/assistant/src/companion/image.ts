/**
 * 图片生成模块 - 基于 fal.ai
 */

import fetch from 'node-fetch';
import { ImageGenerationParams } from '../core/types.js';
import { logger } from '../utils/logger.js';

export class ImageGenerator {
  private apiKey: string;
  private baseUrl = 'https://fal.run/fal-ai/grok-imagine';

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  /**
   * 生成场景图片
   */
  async generateImage(params: ImageGenerationParams): Promise<string> {
    try {
      const response = await fetch(this.baseUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Key ${this.apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          prompt: this.enhancePrompt(params.prompt, params.style),
          image_url: params.referenceImage,
          mode: params.mode || 'direct',
          num_images: 1
        })
      });

      if (!response.ok) {
        throw new Error(`API request failed: ${response.statusText}`);
      }

      const result: any = await response.json();
      
      if (result.images && result.images.length > 0) {
        logger.info('Image generated successfully');
        return result.images[0].url;
      }

      throw new Error('No image generated');
    } catch (error) {
      logger.error('Failed to generate image:', error);
      throw error;
    }
  }

  /**
   * 增强提示词
   */
  private enhancePrompt(basePrompt: string, style?: string): string {
    const enhancements = [
      'consistent character',
      'natural lighting',
      'high quality',
      'detailed'
    ];

    if (style) {
      enhancements.push(style);
    }

    return `${basePrompt}, ${enhancements.join(', ')}`;
  }

  /**
   * 预设场景生成
   */
  async generateSceneImage(
    scene: 'work' | 'coffee' | 'gym' | 'office',
    referenceImage: string
  ): Promise<string> {
    const scenePrompts = {
      work: 'working on laptop at a cozy coffee shop, focused expression',
      coffee: 'holding a coffee cup, smiling, casual outfit',
      gym: 'at the gym, workout clothes, energetic pose',
      office: 'in modern office, professional attire, working at desk'
    };

    return this.generateImage({
      prompt: scenePrompts[scene],
      mode: 'direct',
      referenceImage,
      style: 'photorealistic'
    });
  }
}
