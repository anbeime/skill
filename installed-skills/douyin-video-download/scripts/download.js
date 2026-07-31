#!/usr/bin/env node

/**
 * 抖音视频下载器 - 主入口
 */

require('dotenv').config();

const parser = require('../lib/parser');
const downloader = require('../lib/downloader');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const DEFAULT_OUTPUT_DIR = process.env.OUTPUT_DIR || path.join(__dirname, '../temp/downloads');

/**
 * 打印欢迎信息
 */
function printBanner() {
  console.log('');
  console.log('╔════════════════════════════════════════════╗');
  console.log('║    📹 抖音视频下载器 v1.0.3                ║');
  console.log('║    Douyin Video Downloader                 ║');
  console.log('╚════════════════════════════════════════════╝');
  console.log('');
}

/**
 * 打印帮助信息
 */
function printHelp() {
  console.log('用法: node scripts/download.js <链接> [选项]');
  console.log('');
  console.log('参数:');
  console.log('  <链接>                 抖音视频链接或链接文件路径');
  console.log('');
  console.log('选项:');
  console.log('  --output <dir>         输出目录 (默认: ./temp/downloads)');
  console.log('  --filename <name>      自定义文件名 (不含扩展名)');
  console.log('  --batch                批量模式（从文件读取链接）');
  console.log('  --concurrent <num>     并发下载数量 (默认: 1)');
  console.log('  --timeout <ms>         下载超时时间 (默认: 120000)');
  console.log('');
  console.log('示例:');
  console.log('  # 单视频下载');
  console.log('  node scripts/download.js "https://v.douyin.com/xxxxx"');
  console.log('');
  console.log('  # 批量下载');
  console.log('  node scripts/download.js --batch links.txt');
  console.log('');
  console.log('  # 指定输出目录');
  console.log('  node scripts/download.js "https://v.douyin.com/xxxxx" --output ./videos');
  console.log('');
}

/**
 * 解析命令行参数
 */
function parseArgs() {
  const args = process.argv.slice(2);
  const result = {
    input: null,
    output: DEFAULT_OUTPUT_DIR,
    filename: null,
    batch: false,
    concurrent: 1,
    timeout: 120000
  };
  
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--output' && i + 1 < args.length) {
      result.output = args[++i];
    } else if (arg === '--filename' && i + 1 < args.length) {
      result.filename = args[++i];
    } else if (arg === '--batch') {
      result.batch = true;
    } else if (arg === '--concurrent' && i + 1 < args.length) {
      result.concurrent = parseInt(args[++i]);
    } else if (arg === '--timeout' && i + 1 < args.length) {
      result.timeout = parseInt(args[++i]);
    } else if (!arg.startsWith('--')) {
      result.input = arg;
    }
  }
  
  return result;
}

/**
 * 下载封面图
 */
function downloadCover(coverUrl, outputPath) {
  return new Promise((resolve, reject) => {
    const args = ['-L', '-A', 'Mozilla/5.0', '-s', '-g', coverUrl, '-o', outputPath];
    const proc = spawn('curl', args);
    proc.on('close', (code) => {
      if (code === 0 && fs.existsSync(outputPath) && fs.statSync(outputPath).size > 1000) {
        resolve(outputPath);
      } else {
        reject(new Error('封面图下载失败'));
      }
    });
    proc.on('error', reject);
  });
}

/**
 * 下载单个视频
 */
async function downloadSingle(url, options) {
  try {
    console.log(`📹 目标: ${url}`);
    console.log('');
    
    // 解析 URL
    console.log('ℹ️  步骤 1/2: 解析视频信息...');
    const parseResult = await parser.parseDouyinUrl(url);
    console.log(`  ✓ 视频 ID: ${parseResult.videoId}`);
    if (parseResult.info?.title) {
      console.log(`  ✓ 标题: ${parseResult.info.title}`);
    }
    console.log('');
    
    // 下载视频
    console.log('ℹ️  步骤 2/2: 下载视频...');
    const downloadResult = await downloader.downloadVideo(
      parseResult.targetUrl,
      options.output,
      parseResult.videoId,
      {
        filename: options.filename,
        timeout: options.timeout
      }
    );
    
    if (downloadResult.success) {
      console.log('');
      console.log('✅ 下载成功！');
      console.log(`📁 文件路径: ${downloadResult.filePath}`);
      console.log(`📊 文件大小: ${downloader.formatBytes(downloadResult.size)}`);
      return true;
    } else {
      console.error('');
      console.error(`❌ 下载失败: ${downloadResult.error}`);
      return false;
    }
  } catch (error) {
    console.error('');
    console.error(`❌ 错误: ${error.message}`);
    return false;
  }
}

/**
 * 批量下载
 */
async function downloadBatch(filePath, options) {
  try {
    // 读取链接列表
    const content = fs.readFileSync(filePath, 'utf8');
    const urls = content
      .split('\n')
      .map(line => line.trim())
      .filter(line => line && !line.startsWith('#'));
    
    if (urls.length === 0) {
      console.error('❌ 错误: 文件中没有找到有效的链接');
      return false;
    }
    
    console.log(`📋 找到 ${urls.length} 个链接`);
    console.log('');
    
    let successCount = 0;
    let failCount = 0;
    
    for (let i = 0; i < urls.length; i++) {
      const url = urls[i];
      console.log(`[${i + 1}/${urls.length}] ${url}`);
      
      const success = await downloadSingle(url, options);
      if (success) {
        successCount++;
      } else {
        failCount++;
      }
      
      console.log('');
      console.log('─'.repeat(50));
      console.log('');
    }
    
    console.log('📊 批量下载完成');
    console.log(`✅ 成功: ${successCount}`);
    console.log(`❌ 失败: ${failCount}`);
    
    return failCount === 0;
  } catch (error) {
    console.error(`❌ 错误: ${error.message}`);
    return false;
  }
}

/**
 * 主函数
 */
async function main() {
  const args = parseArgs();
  
  if (!args.input) {
    return printHelp();
  }
  
  printBanner();
  
  try {
    if (args.batch) {
      // 批量模式
      if (!fs.existsSync(args.input)) {
        console.error(`❌ 错误: 文件不存在: ${args.input}`);
        return;
      }
      await downloadBatch(args.input, args);
    } else {
      // 单视频模式
      await downloadSingle(args.input, args);
    }
  } catch (error) {
    console.error('');
    console.error('❌ 发生错误:', error.message);
    console.error('');
    console.error(error.stack);
  }
}

// 运行主函数
main();
