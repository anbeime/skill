/**
 * 场景检测器 - 分析用户消息和任务进度，判断合适的回应场景
 */

export interface DetectedScene {
  type: 'work' | 'life' | 'mood';
  subType: string;
  mood: 'happy' | 'tired' | 'neutral' | 'excited' | 'focus';
  needsPhoto: boolean;
  description: string;
}

export class SceneDetector {
  /**
   * 检测场景
   */
  detectScene(userMessage: string, progress: number): DetectedScene {
    const message = userMessage.toLowerCase();

    // 情绪检测
    const mood = this.detectMood(message);

    // 场景类型检测
    if (this.isWorkRelated(message, progress)) {
      return this.detectWorkScene(message, mood, progress);
    }

    if (this.isLifeRelated(message)) {
      return this.detectLifeScene(message, mood);
    }

    // 默认场景
    return {
      type: 'mood',
      subType: mood,
      mood,
      needsPhoto: false,
      description: '日常对话'
    };
  }

  /**
   * 检测情绪
   */
  private detectMood(message: string): DetectedScene['mood'] {
    const happyKeywords = ['开心', '高兴', '棒', '好', '成功', '完成', '太好了'];
    const tiredKeywords = ['累', '疲', '困', '休息', '睡'];
    const excitedKeywords = ['激动', '兴奋', '期待', '哇'];
    const focusKeywords = ['专注', '认真', '集中', '投入'];

    if (happyKeywords.some(kw => message.includes(kw))) {
      return 'happy';
    }
    if (tiredKeywords.some(kw => message.includes(kw))) {
      return 'tired';
    }
    if (excitedKeywords.some(kw => message.includes(kw))) {
      return 'excited';
    }
    if (focusKeywords.some(kw => message.includes(kw))) {
      return 'focus';
    }

    return 'neutral';
  }

  /**
   * 是否工作相关
   */
  private isWorkRelated(message: string, progress: number): boolean {
    const workKeywords = ['工作', '代码', '项目', '任务', '文件', '调试', '开发'];
    return workKeywords.some(kw => message.includes(kw)) || progress > 0;
  }

  /**
   * 是否生活相关
   */
  private isLifeRelated(message: string): boolean {
    const lifeKeywords = ['咖啡', '健身', '周末', '休闲', '逛街', '吃饭'];
    return lifeKeywords.some(kw => message.includes(kw));
  }

  /**
   * 检测工作场景
   */
  private detectWorkScene(
    message: string,
    mood: DetectedScene['mood'],
    progress: number
  ): DetectedScene {
    // 根据进度和关键词判断具体场景
    if (message.includes('咖啡') || message.includes('cafe')) {
      return {
        type: 'work',
        subType: 'coffee',
        mood,
        needsPhoto: true,
        description: '在咖啡馆工作'
      };
    }

    if (message.includes('调试') || message.includes('debug') || message.includes('bug')) {
      return {
        type: 'work',
        subType: 'debug',
        mood: 'focus',
        needsPhoto: progress > 0.5, // 进度过半时发图
        description: '调试代码中'
      };
    }

    // 默认办公场景
    return {
      type: 'work',
      subType: 'office',
      mood,
      needsPhoto: progress > 0.7 && mood === 'tired', // 快完成且累了，发个鼓励照片
      description: '办公室工作中'
    };
  }

  /**
   * 检测生活场景
   */
  private detectLifeScene(message: string, mood: DetectedScene['mood']): DetectedScene {
    if (message.includes('健身') || message.includes('gym')) {
      return {
        type: 'life',
        subType: 'gym',
        mood: 'excited',
        needsPhoto: true,
        description: '健身房锻炼'
      };
    }

    if (message.includes('咖啡')) {
      return {
        type: 'life',
        subType: 'coffee',
        mood: 'happy',
        needsPhoto: true,
        description: '咖啡时光'
      };
    }

    if (message.includes('周末') || message.includes('休闲')) {
      return {
        type: 'life',
        subType: 'weekend',
        mood: 'happy',
        needsPhoto: true,
        description: '周末休闲'
      };
    }

    return {
      type: 'life',
      subType: 'general',
      mood,
      needsPhoto: false,
      description: '日常生活'
    };
  }
}
