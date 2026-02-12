/**
 * 图片生成器 - 集成智谱 AI CogView-3-Flash
 * 支持两种模式：
 * 1. AI 生成模式：使用 cogview-3-flash 动态生成场景图片
 * 2. 静态模式：使用预制图片库（降级方案）
 */

import * as path from 'path';
import * as fs from 'fs';
import axios from 'axios';

interface ImageGenerateOptions {
  scene: string;
  mood: string;
  customPrompt?: string;
}

interface CogViewResponse {
  created: number;
  data: Array<{
    url: string;
  }>;
}

export class ImageGenerator {
  private apiKey: string;
  private mode: 'static' | 'ai';
  private staticImagePath: string;
  private apiEndpoint = 'https://open.bigmodel.cn/api/paas/v4/images/generations';
  
  // 小跃的基础人设描述（用于保持生成图片的一致性）
  private characterDescription = `一个22岁的年轻人，短发，休闲装扮，友好的表情，现代都市风格`;

  constructor(apiKey: string) {
    this.apiKey = apiKey;
    this.mode = (process.env.XIAOYUE_PHOTO_MODE as 'static' | 'ai') || 'static';
    this.staticImagePath = path.join(__dirname, '../assets/reference');
    
    // 确保静态图片目录存在
    if (!fs.existsSync(this.staticImagePath)) {
      fs.mkdirSync(this.staticImagePath, { recursive: true });
    }
  }

  /**
   * 生成图片（主入口）
   */
  async generate(options: ImageGenerateOptions): Promise<string> {
    if (this.mode === 'ai') {
      try {
        return await this.generateAIImage(options);
      } catch (error) {
        console.error('AI image generation failed, falling back to static:', error);
        return this.getStaticImage(options);
      }
    } else {
      return this.getStaticImage(options);
    }
  }

  /**
   * 使用 cogview-3-flash 生成图片
   */
  private async generateAIImage(options: ImageGenerateOptions): Promise<string> {
    const { scene, mood, customPrompt } = options;

    // 构建提示词
    const prompt = customPrompt || this.buildPrompt(scene, mood);

    console.log(`Generating image with cogview-3-flash: ${prompt}`);

    try {
      const response = await axios.post<CogViewResponse>(
        this.apiEndpoint,
        {
          model: 'cogview-3-flash',  // 修正：全小写
          prompt: prompt,
          size: '1280x1280' // 可选: 1024x1024, 1280x720, 720x1280
        },
        {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`,
            'Content-Type': 'application/json'
          },
          timeout: 60000 // 60秒超时
        }
      );

      if (response.data.data && response.data.data.length > 0) {
        const imageUrl = response.data.data[0].url;
        
        // 可选：下载图片到本地缓存
        await this.cacheImage(imageUrl, scene, mood);
        
        return imageUrl;
      } else {
        throw new Error('No image generated');
      }
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.error('CogView API Error:', {
          status: error.response?.status,
          data: error.response?.data,
          message: error.message
        });
      }
      throw error;
    }
  }

  /**
   * 构建图片生成提示词
   */
  private buildPrompt(scene: string, mood: string): string {
    const scenePrompts: Record<string, string> = {
      'work-coffee': `${this.characterDescription}，在温馨的咖啡馆里用笔记本电脑工作，桌上有一杯咖啡，温暖的灯光，专注的表情，现代咖啡馆背景，自然光线`,
      
      'work-office': `${this.characterDescription}，在现代办公室环境中写代码，多个显示器，整洁的桌面，专业的工作氛围，侧面角度`,
      
      'work-debug': `${this.characterDescription}，专注调试代码的场景，屏幕上显示代码编辑器，认真思考的表情，办公室环境`,
      
      'life-gym': `${this.characterDescription}，在健身房自拍，运动装，充满活力的表情，健身器材背景，明亮的灯光`,
      
      'life-coffee': `${this.characterDescription}，手持咖啡杯的特写，咖啡馆背景虚化，温馨的氛围，自然光线`,
      
      'life-weekend': `${this.characterDescription}，周末休闲场景，轻松愉快的氛围，户外或咖啡馆，阳光明媚`,
      
      'mood-happy': `${this.characterDescription}，开心庆祝的场景，笑容灿烂，举起手机或咖啡杯，明亮的背景`,
      
      'mood-tired': `${this.characterDescription}，疲惫但满足的表情，靠在椅子上休息，温暖的灯光，办公室或家中`,
      
      'mood-focus': `${this.characterDescription}，专注工作的侧面照，深度思考的表情，屏幕光线照亮脸部，安静的环境`
    };

    const key = `${scene}-${mood}`;
    let basePrompt = scenePrompts[key] || scenePrompts[scene] || `${this.characterDescription}，日常生活场景`;

    // 添加质量增强词
    basePrompt += `，高质量，自然光线，真实感，细节丰富，专业摄影`;

    return basePrompt;
  }

  /**
   * 缓存生成的图片到本地
   */
  private async cacheImage(imageUrl: string, scene: string, mood: string): Promise<void> {
    try {
      const response = await axios.get(imageUrl, {
        responseType: 'arraybuffer',
        timeout: 30000
      });

      const filename = `${scene}-${mood}-${Date.now()}.jpg`;
      const filepath = path.join(this.staticImagePath, filename);

      fs.writeFileSync(filepath, response.data);
      console.log(`Image cached: ${filepath}`);
    } catch (error) {
      console.error('Failed to cache image:', error);
      // 不抛出错误，缓存失败不影响主流程
    }
  }

  /**
   * 从静态图片库获取图片
   */
  private getStaticImage(options: ImageGenerateOptions): string {
    const { scene, mood } = options;

    // 图片映射表
    const imageMap: Record<string, string> = {
      'work-coffee': 'coffee-shop-work.jpg',
      'work-office': 'office-coding.jpg',
      'work-debug': 'debugging.jpg',
      'life-gym': 'gym-selfie.jpg',
      'life-coffee': 'coffee-break.jpg',
      'life-weekend': 'weekend-relax.jpg',
      'mood-happy': 'celebration.jpg',
      'mood-tired': 'tired-rest.jpg',
      'mood-focus': 'deep-focus.jpg'
    };

    // 组合场景和情绪
    const key = `${scene}-${mood}`;
    const filename = imageMap[key] || imageMap[scene] || 'default.jpg';
    const imagePath = path.join(this.staticImagePath, filename);

    // 检查文件是否存在
    if (fs.existsSync(imagePath)) {
      return imagePath;
    }

    // 如果没有找到，返回默认图片路径（即使不存在，也返回路径）
    console.warn(`Image not found: ${imagePath}, returning default path`);
    return path.join(this.staticImagePath, 'default.jpg');
  }

  /**
   * 批量生成场景图片（用于初始化图片库）
   */
  async generateImageLibrary(): Promise<void> {
    console.log('Generating image library with cogview-3-flash...');

    const scenes = [
      { scene: 'work', mood: 'coffee' },
      { scene: 'work', mood: 'office' },
      { scene: 'work', mood: 'debug' },
      { scene: 'life', mood: 'gym' },
      { scene: 'life', mood: 'coffee' },
      { scene: 'life', mood: 'weekend' },
      { scene: 'mood', mood: 'happy' },
      { scene: 'mood', mood: 'tired' },
      { scene: 'mood', mood: 'focus' }
    ];

    for (const { scene, mood } of scenes) {
      try {
        console.log(`Generating: ${scene}-${mood}`);
        const imageUrl = await this.generateAIImage({ scene, mood });
        console.log(`✓ Generated: ${imageUrl}`);
        
        // 等待1秒，避免API限流
        await new Promise(resolve => setTimeout(resolve, 1000));
      } catch (error) {
        console.error(`✗ Failed to generate ${scene}-${mood}:`, error);
      }
    }

    console.log('Image library generation completed!');
  }

  /**
   * 设置人物描述（用于自定义小跃的外观）
   */
  setCharacterDescription(description: string): void {
    this.characterDescription = description;
  }

  /**
   * 获取当前人物描述
   */
  getCharacterDescription(): string {
    return this.characterDescription;
  }
}
