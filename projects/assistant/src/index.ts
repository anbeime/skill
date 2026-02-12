/**
 * 主入口文件
 */

import dotenv from 'dotenv';
import express from 'express';
import { Agent } from './core/agent.js';
import { MemorySystem } from './core/memory.js';
import { ImageGenerator } from './companion/image.js';
import { logger } from './utils/logger.js';

// 加载环境变量
dotenv.config();

const app = express();
app.use(express.json());

// 初始化核心组件
const memory = new MemorySystem(process.env.MEMORY_STORAGE_PATH);
const agent = new Agent(
  {
    model: 'claude',
    apiKey: process.env.ANTHROPIC_API_KEY || '',
    temperature: 0.7,
    maxTokens: 1024
  },
  memory
);

const imageGenerator = process.env.FAL_KEY 
  ? new ImageGenerator(process.env.FAL_KEY)
  : null;

/**
 * 健康检查接口
 */
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    memory: memory.getStats()
  });
});

/**
 * 消息处理接口
 */
app.post('/message', async (req, res) => {
  try {
    const { userId, message } = req.body;

    if (!userId || !message) {
      return res.status(400).json({
        error: 'Missing userId or message'
      });
    }

    logger.info(`Processing message from user ${userId}`);
    
    const response = await agent.processMessage(userId, message);
    
    res.json({
      success: true,
      response
    });
  } catch (error: any) {
    logger.error('Error handling message:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * 图片生成接口
 */
app.post('/generate-image', async (req, res) => {
  try {
    if (!imageGenerator) {
      return res.status(503).json({
        error: 'Image generation not configured'
      });
    }

    const { prompt, scene, referenceImage } = req.body;

    let imageUrl: string;
    
    if (scene) {
      imageUrl = await imageGenerator.generateSceneImage(
        scene,
        referenceImage || process.env.DEFAULT_REFERENCE_IMAGE || ''
      );
    } else {
      imageUrl = await imageGenerator.generateImage({
        prompt,
        mode: 'direct',
        referenceImage
      });
    }

    res.json({
      success: true,
      imageUrl
    });
  } catch (error: any) {
    logger.error('Error generating image:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * 用户偏好管理接口
 */
app.post('/preferences', async (req, res) => {
  try {
    const { userId, preferences } = req.body;

    await memory.updatePreferences(userId, preferences);

    res.json({
      success: true,
      message: 'Preferences updated'
    });
  } catch (error: any) {
    logger.error('Error updating preferences:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * 启动服务
 */
async function start() {
  try {
    // 初始化记忆系统
    await memory.initialize();
    logger.info('Memory system initialized');

    // 启动 HTTP 服务器
    const port = process.env.PORT || 3000;
    app.listen(port, () => {
      logger.info(`🚀 Xiaoyue Assistant is running on port ${port}`);
      logger.info(`Environment: ${process.env.NODE_ENV || 'development'}`);
      logger.info(`Health check: http://localhost:${port}/health`);
    });
  } catch (error) {
    logger.error('Failed to start application:', error);
    process.exit(1);
  }
}

// 优雅关闭
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  process.exit(0);
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully');
  process.exit(0);
});

// 启动应用
start();
