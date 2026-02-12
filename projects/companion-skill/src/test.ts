/**
 * 测试脚本 - 验证虚拟伴侣功能
 * 
 * 运行方式：
 * 1. 确保已配置 .env 文件
 * 2. npm run build
 * 3. node dist/test.js
 */

import * as dotenv from 'dotenv';
import { CompanionService } from './companion';
import { ImageGenerator } from './image-generator';
import { SceneDetector } from './scene-detector';
import * as path from 'path';
import * as fs from 'fs';

// 加载环境变量
dotenv.config();

async function testCompanionService() {
  console.log('\n=== 测试对话生成 (glm-4-flash) ===\n');

  const apiKey = process.env.ZHIPU_API_KEY;
  if (!apiKey) {
    console.error('❌ ZHIPU_API_KEY not found in .env file');
    return;
  }

  const companion = new CompanionService(apiKey);

  // 测试场景1：任务开始
  console.log('场景1：任务开始');
  const response1 = await companion.generateResponse({
    taskName: '文件整理',
    progress: 0.1,
    userMessage: '',
    scene: {
      type: 'work',
      mood: 'neutral',
      needsPhoto: false,
      description: '任务开始'
    }
  });
  console.log('小跃:', response1);

  // 测试场景2：用户说累了
  console.log('\n场景2：用户说累了');
  const response2 = await companion.generateResponse({
    taskName: '文件整理',
    progress: 0.5,
    userMessage: '有点累',
    scene: {
      type: 'work',
      mood: 'tired',
      needsPhoto: true,
      description: '疲惫休息'
    }
  });
  console.log('小跃:', response2);

  // 测试场景3：任务完成
  console.log('\n场景3：任务完成');
  const response3 = await companion.generateResponse({
    taskName: '文件整理',
    progress: 1.0,
    userMessage: '终于完成了',
    scene: {
      type: 'mood',
      mood: 'happy',
      needsPhoto: true,
      description: '开心庆祝'
    }
  });
  console.log('小跃:', response3);
}

async function testMultimodalVision() {
  console.log('\n=== 测试多模态视觉理解 (glm-4v-flash) ===\n');

  const apiKey = process.env.ZHIPU_API_KEY;
  if (!apiKey) {
    console.error('❌ ZHIPU_API_KEY not found in .env file');
    return;
  }

  const companion = new CompanionService(apiKey);

  // 测试参考图片
  const referenceImagePath = 'D:\\tool\\StepFun\\resources\\chat.png';
  
  if (fs.existsSync(referenceImagePath)) {
    console.log('测试图片:', referenceImagePath);
    
    // 将图片转换为 base64（glm-4v-flash 支持 base64）
    const imageBuffer = fs.readFileSync(referenceImagePath);
    const base64Image = imageBuffer.toString('base64');
    const dataUrl = `data:image/png;base64,${base64Image}`;
    
    try {
      const analysis = await companion.analyzeImage(
        dataUrl,
        '请描述这张图片的内容，包括人物、场景和氛围'
      );
      console.log('图片分析结果:', analysis);
    } catch (error) {
      console.error('图片分析失败:', error);
    }
  } else {
    console.log('⚠️  测试图片不存在，跳过多模态测试');
  }
}

async function testSceneDetector() {
  console.log('\n=== 测试场景识别 ===\n');

  const detector = new SceneDetector();

  const testCases = [
    { message: '帮我整理文件', progress: 0.1 },
    { message: '有点累了', progress: 0.5 },
    { message: '我在咖啡馆工作', progress: 0.3 },
    { message: '刚健身完', progress: 0 },
    { message: '终于完成了！', progress: 1.0 }
  ];

  for (const testCase of testCases) {
    const scene = detector.detectScene(testCase.message, testCase.progress);
    console.log(`消息: "${testCase.message}"`);
    console.log(`识别结果:`, scene);
    console.log('---');
  }
}

async function testImageGenerator() {
  console.log('\n=== 测试图片生成 (cogview-3-flash) ===\n');

  const apiKey = process.env.ZHIPU_API_KEY;
  if (!apiKey) {
    console.error('❌ ZHIPU_API_KEY not found in .env file');
    return;
  }

  const generator = new ImageGenerator(apiKey);

  // 测试静态模式
  console.log('测试静态模式...');
  const staticImage = generator['getStaticImage']({
    scene: 'work',
    mood: 'coffee'
  });
  console.log('静态图片路径:', staticImage);

  // 测试 AI 生成模式（如果启用）
  if (process.env.XIAOYUE_PHOTO_MODE === 'ai') {
    console.log('\n测试 AI 生成模式 (cogview-3-flash)...');
    try {
      const aiImage = await generator.generate({
        scene: 'work',
        mood: 'coffee'
      });
      console.log('✓ AI 生成成功:', aiImage);
    } catch (error) {
      console.error('✗ AI 生成失败:', error);
    }
  } else {
    console.log('\n跳过 AI 生成测试（当前模式: static）');
    console.log('提示：在 .env 中设置 XIAOYUE_PHOTO_MODE=ai 来启用 AI 生成');
  }
}

async function testImageLibraryGeneration() {
  console.log('\n=== 批量生成图片库 (cogview-3-flash) ===\n');

  const apiKey = process.env.ZHIPU_API_KEY;
  if (!apiKey) {
    console.error('❌ ZHIPU_API_KEY not found in .env file');
    return;
  }

  const confirm = process.argv.includes('--generate-library');
  if (!confirm) {
    console.log('⚠️  此操作将调用 9 次 CogView API，可能产生费用');
    console.log('如需执行，请运行: node dist/test.js --generate-library');
    return;
  }

  const generator = new ImageGenerator(apiKey);
  await generator.generateImageLibrary();
}

async function testReferenceImage() {
  console.log('\n=== 测试参考图片 ===\n');

  const referenceImagePath = 'D:\\tool\\StepFun\\resources\\chat.png';
  
  if (fs.existsSync(referenceImagePath)) {
    console.log('✓ 参考图片存在:', referenceImagePath);
    
    // 复制到 assets 目录
    const targetPath = path.join(__dirname, '../assets/reference/reference.png');
    const targetDir = path.dirname(targetPath);
    
    if (!fs.existsSync(targetDir)) {
      fs.mkdirSync(targetDir, { recursive: true });
    }
    
    fs.copyFileSync(referenceImagePath, targetPath);
    console.log('✓ 已复制到:', targetPath);
    console.log('\n提示：你可以基于这张图片生成一致风格的场景图片');
  } else {
    console.log('✗ 参考图片不存在:', referenceImagePath);
  }
}

async function main() {
  console.log('🚀 小跃虚拟伴侣 Skill - 功能测试\n');
  console.log('API Key:', process.env.ZHIPU_API_KEY ? '已配置 ✓' : '未配置 ✗');
  console.log('图片模式:', process.env.XIAOYUE_PHOTO_MODE || 'static');
  console.log('='.repeat(50));

  try {
    // 测试参考图片
    await testReferenceImage();

    // 测试场景识别
    await testSceneDetector();

    // 测试对话生成 (glm-4-flash)
    await testCompanionService();

    // 测试多模态视觉 (glm-4v-flash)
    await testMultimodalVision();

    // 测试图片生成 (cogview-3-flash)
    await testImageGenerator();

    // 批量生成图片库（可选）
    await testImageLibraryGeneration();

    console.log('\n✅ 所有测试完成！');
  } catch (error) {
    console.error('\n❌ 测试失败:', error);
    process.exit(1);
  }
}

// 运行测试
main();
