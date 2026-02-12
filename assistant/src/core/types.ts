/**
 * 核心类型定义
 */

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  platform?: string;
  userId?: string;
}

export interface UserProfile {
  userId: string;
  name?: string;
  preferences: {
    workingHours?: string;
    favoriteTools?: string[];
    communicationStyle?: 'formal' | 'casual';
    language?: string;
  };
  conversationHistory: Message[];
  customSkills?: string[];
  createdAt: number;
  updatedAt: number;
}

export interface Skill {
  name: string;
  description: string;
  category: 'file' | 'code' | 'data' | 'system' | 'custom';
  execute: (params: SkillParams) => Promise<SkillResult>;
  requiresConfirmation?: boolean;
}

export interface SkillParams {
  action: string;
  args: Record<string, any>;
  userId: string;
  context?: string;
}

export interface SkillResult {
  success: boolean;
  data?: any;
  message?: string;
  error?: string;
}

export interface CompanionConfig {
  personality: string;
  emotionDetection: boolean;
  proactiveChat: boolean;
  imageGeneration: boolean;
}

export interface ImageGenerationParams {
  prompt: string;
  mode: 'direct' | 'mirror';
  referenceImage?: string;
  style?: string;
}

export interface PlatformMessage {
  platform: 'feishu' | 'dingtalk' | 'telegram' | 'wechat';
  messageId: string;
  userId: string;
  content: string;
  timestamp: number;
  chatType: 'private' | 'group';
}

export interface AgentConfig {
  model: 'claude' | 'gpt4' | 'qwen';
  apiKey: string;
  temperature?: number;
  maxTokens?: number;
}
