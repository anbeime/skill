/**
 * 记忆系统 - 管理用户偏好和对话历史
 */

import fs from 'fs/promises';
import path from 'path';
import { UserProfile, Message } from './types.js';
import { logger } from '../utils/logger.js';

export class MemorySystem {
  private memoryPath: string;
  private cache: Map<string, UserProfile>;

  constructor(storagePath: string = './data/memory.json') {
    this.memoryPath = storagePath;
    this.cache = new Map();
  }

  /**
   * 初始化记忆系统
   */
  async initialize(): Promise<void> {
    try {
      const dir = path.dirname(this.memoryPath);
      await fs.mkdir(dir, { recursive: true });

      try {
        const data = await fs.readFile(this.memoryPath, 'utf-8');
        const profiles: UserProfile[] = JSON.parse(data);
        profiles.forEach(profile => {
          this.cache.set(profile.userId, profile);
        });
        logger.info(`Loaded ${profiles.length} user profiles from memory`);
      } catch (error) {
        // 文件不存在，创建空文件
        await this.save();
        logger.info('Initialized new memory storage');
      }
    } catch (error) {
      logger.error('Failed to initialize memory system:', error);
      throw error;
    }
  }

  /**
   * 获取用户档案
   */
  async getUserProfile(userId: string): Promise<UserProfile> {
    if (this.cache.has(userId)) {
      return this.cache.get(userId)!;
    }

    // 创建新用户档案
    const newProfile: UserProfile = {
      userId,
      preferences: {
        communicationStyle: 'casual',
        language: 'zh-CN'
      },
      conversationHistory: [],
      createdAt: Date.now(),
      updatedAt: Date.now()
    };

    this.cache.set(userId, newProfile);
    await this.save();
    return newProfile;
  }

  /**
   * 添加对话消息
   */
  async addMessage(userId: string, message: Message): Promise<void> {
    const profile = await this.getUserProfile(userId);
    
    // 保留最近 50 条消息
    profile.conversationHistory.push(message);
    if (profile.conversationHistory.length > 50) {
      profile.conversationHistory = profile.conversationHistory.slice(-50);
    }

    profile.updatedAt = Date.now();
    await this.save();
  }

  /**
   * 获取对话历史
   */
  async getConversationHistory(userId: string, limit: number = 10): Promise<Message[]> {
    const profile = await this.getUserProfile(userId);
    return profile.conversationHistory.slice(-limit);
  }

  /**
   * 更新用户偏好
   */
  async updatePreferences(
    userId: string,
    preferences: Partial<UserProfile['preferences']>
  ): Promise<void> {
    const profile = await this.getUserProfile(userId);
    profile.preferences = { ...profile.preferences, ...preferences };
    profile.updatedAt = Date.now();
    await this.save();
    logger.info(`Updated preferences for user ${userId}`);
  }

  /**
   * 清除用户历史
   */
  async clearHistory(userId: string): Promise<void> {
    const profile = await this.getUserProfile(userId);
    profile.conversationHistory = [];
    profile.updatedAt = Date.now();
    await this.save();
    logger.info(`Cleared history for user ${userId}`);
  }

  /**
   * 保存到磁盘
   */
  private async save(): Promise<void> {
    try {
      const profiles = Array.from(this.cache.values());
      await fs.writeFile(
        this.memoryPath,
        JSON.stringify(profiles, null, 2),
        'utf-8'
      );
    } catch (error) {
      logger.error('Failed to save memory:', error);
    }
  }

  /**
   * 获取统计信息
   */
  getStats() {
    return {
      totalUsers: this.cache.size,
      totalMessages: Array.from(this.cache.values()).reduce(
        (sum, profile) => sum + profile.conversationHistory.length,
        0
      )
    };
  }
}
