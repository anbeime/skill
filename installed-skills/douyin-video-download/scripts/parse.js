#!/usr/bin/env node

const parser = require('../lib/parser');
const downloader = require('../lib/downloader');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const OUT = process.env.OUTPUT_DIR || path.join(__dirname, '../temp/downloads');

function curlDownload(url, filePath) {
  return new Promise((resolve, reject) => {
    const args = ['-L', '-A', 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_8 like Mac OS X)', '-s', '-g', url, '-o', filePath];
    const p = spawn('curl', args);
    let err = '';
    p.stderr.on('data', d => err += d.toString());
    p.on('close', code => {
      if (code === 0 && fs.existsSync(filePath) && fs.statSync(filePath).size > 1000) {
        resolve(filePath);
      } else {
        reject(new Error(err || 'curl failed'));
      }
    });
    p.on('error', reject);
  });
}

async function run(videoUrl, outputDir) {
  fs.mkdirSync(outputDir, { recursive: true });

  console.log('\n🔍 解析视频信息...');
  const r = await parser.parseDouyinUrl(videoUrl);

  const videoId = r.videoId || 'unknown';
  const title = (r.info && r.info.title) || '';
  const desc = r.videoDesc || '';
  const author = r.authorName || '';
  const coverUrl = r.coverUrl || '';

  console.log(`  ✓ 视频ID: ${videoId}`);
  console.log(`  ✓ 标题: ${title}`);
  if (author) console.log(`  ✓ 作者: ${author}`);
  if (desc) console.log(`  ✓ 文案: ${desc.length}字`);
  if (coverUrl) console.log(`  ✓ 封面: ${coverUrl.slice(0, 60)}...`);
  console.log('');

  // 下载视频
  console.log('📹 下载视频...');
  const videoPath = path.join(outputDir, `${videoId}.mp4`);
  await downloader.downloadVideo(r.targetUrl, outputDir, videoId, { filename: videoId, timeout: 120000 });
  console.log('');

  const result = { success: true, videoId, title, author, desc, videoPath, coverPath: null, descPath: null };

  // 保存文案
  if (desc) {
    const descPath = path.join(outputDir, `${videoId}_文案.txt`);
    fs.writeFileSync(descPath, `标题: ${title}\n作者: ${author}\n\n${desc}`, 'utf8');
    result.descPath = descPath;
    console.log(`📝 文案已保存: ${descPath}`);
  }

  // 下载封面
  if (coverUrl) {
    try {
      const ext = coverUrl.match(/\.(jpe?g|png|webp)/)?.[1] || 'jpeg';
      const coverPath = path.join(outputDir, `${videoId}_封面.${ext}`);
      await curlDownload(coverUrl, coverPath);
      result.coverPath = coverPath;
      console.log(`🖼️  封面已保存: ${coverPath}`);
    } catch (e) {
      console.log(`⚠️  封面下载失败: ${e.message}`);
    }
  }

  // 保存元数据
  const metaPath = path.join(outputDir, `${videoId}_元数据.json`);
  fs.writeFileSync(metaPath, JSON.stringify(result, null, 2), 'utf8');
  console.log(`📋 元数据已保存: ${metaPath}`);
  console.log('\n✅ 完成！\n');
  console.log(JSON.stringify(result, null, 2));
}

async function main() {
  const args = process.argv.slice(2);
  const videoUrl = args.find(a => !a.startsWith('--'));
  const outputDir = args.includes('--output') ? args[args.indexOf('--output') + 1] : OUT;

  if (!videoUrl) {
    console.log('用法: node parse.js <抖音链接> [--output <目录>]');
    process.exit(1);
  }

  console.log('╔═══════════════════════════════════════╗');
  console.log('║  🎬 抖音视频完整解析器 v1.0         ║');
  console.log('╚═══════════════════════════════════════╝');

  try {
    await run(videoUrl, outputDir);
  } catch (err) {
    console.error(`\n❌ 错误: ${err.message}`);
    process.exit(1);
  }
}

main();
