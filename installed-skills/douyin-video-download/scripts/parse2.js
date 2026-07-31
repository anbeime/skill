#!/usr/bin/env node
/**
 * 抖音视频解析 - 通过页面抓取文案和封面
 */

const { chromium } = require('playwright-chromium');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const OUT = process.env.OUTPUT_DIR || '/tmp/douyin_output';
fs.mkdirSync(OUT, { recursive: true });

function curlDownload(url, filePath) {
  return new Promise((resolve, reject) => {
    const args = ['-L', '-A', 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_8 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1', '-s', '-g', url, '-o', filePath];
    const p = spawn('curl', args);
    let err = '';
    p.stderr.on('data', d => err += d.toString());
    p.on('close', code => {
      if (code === 0 && fs.existsSync(filePath) && fs.statSync(filePath).size > 1000) {
        resolve(filePath);
      } else {
        reject(new Error(err || `exit ${code}`));
      }
    });
    p.on('error', reject);
  });
}

async function run(videoUrl) {
  console.log('\n🔍 启动浏览器解析页面...');

  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_8 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1'
  });

  const page = await context.newPage();

  // 等待 API 响应，拿到 aweme_detail
  let awemeDetail = null;
  page.on('response', async (response) => {
    const url = response.url();
    if (url.includes('aweme') && url.includes('detail')) {
      try {
        const json = await response.json();
        awemeDetail = json.aweme_detail || json.data?.aweme_detail || null;
        if (awemeDetail) {
          fs.writeFileSync('/tmp/aweme_raw.json', JSON.stringify(awemeDetail, null, 2));
          console.log('  ✓ 捕获到视频详情数据');
        }
      } catch (e) {}
    }
  });

  await page.goto(videoUrl, { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(3000);

  // 从页面提取信息
  const pageData = await page.evaluate(() => {
    const metaDesc = document.querySelector('meta[name="description"]')?.content || '';
    const metaTitle = document.title || '';
    
    // 尝试从页面 JSON-LD 或内联脚本中提取数据
    let jsonData = null;
    const scripts = Array.from(document.querySelectorAll('script:not([src])'));
    for (const script of scripts) {
      const text = script.textContent || '';
      if (text.includes('aweme') || text.includes('desc') || text.includes('cover')) {
        try {
          // 尝试提取 JSON 数据
          const match = text.match(/(\{.*\})/s);
          if (match) {
            const parsed = JSON.parse(match[1]);
            if (parsed.desc || parsed.cover) {
              jsonData = parsed;
              break;
            }
          }
        } catch (e) {}
      }
    }
    
    return { metaDesc, metaTitle, jsonData };
  });

  await browser.close();

  console.log(`  ✓ 标题: ${pageData.metaTitle}`);
  console.log(`  ✓ Meta描述: ${pageData.metaDesc.substring(0, 50)}...`);

  // 优先使用 API 数据，兜底使用 meta 描述
  let videoDesc = '';
  let authorName = '';
  let coverUrl = '';
  let videoId = '';

  if (awemeDetail) {
    videoDesc = awemeDetail.desc || '';
    authorName = awemeDetail.author?.nickname || awemeDetail.author?.unique_id || '';
    const cover = awemeDetail.video?.cover || awemeDetail.video?.origin_cover;
    if (cover?.url_list?.length > 0) {
      coverUrl = cover.url_list[0];
    }
    videoId = awemeDetail.video?.play_addr?.uri || '';
    console.log(`  ✓ 文案长度: ${videoDesc.length} 字`);
    console.log(`  ✓ 作者: ${authorName}`);
    if (coverUrl) console.log(`  ✓ 封面: ${coverUrl.substring(0, 60)}...`);
  } else {
    videoDesc = pageData.metaDesc || pageData.metaTitle || '';
    console.log('  ⚠️  未捕获到API数据，使用页面描述兜底');
  }

  // 如果还是没有 videoId，从 URL 提取
  if (!videoId) {
    const m = videoUrl.match(/\/video\/(\d+)/);
    if (m) videoId = m[1];
  }
  if (!videoId) videoId = 'unknown_' + Date.now();

  console.log('\n📹 下载视频...');
  const videoPath = path.join(OUT, `${videoId}.mp4`);
  const downloadUrl = `https://aweme.snssdk.com/aweme/v1/play/?video_id=${videoId}&ratio=1080p&line=0`;
  
  try {
    await curlDownload(downloadUrl, videoPath);
    console.log(`  ✓ 视频已保存: ${videoPath}`);
  } catch (e) {
    console.log(`  ⚠️  视频下载失败: ${e.message}`);
  }

  // 保存文案
  if (videoDesc) {
    const descPath = path.join(OUT, `${videoId}_文案.txt`);
    fs.writeFileSync(descPath, `标题: ${pageData.metaTitle}\n作者: ${authorName}\n\n${videoDesc}`, 'utf8');
    console.log(`  ✓ 文案已保存: ${descPath}`);
  }

  // 下载封面
  if (coverUrl) {
    try {
      const ext = coverUrl.match(/\.(jpg|jpeg|png|webp)/i)?.[1] || 'jpeg';
      const coverPath = path.join(OUT, `${videoId}_封面.${ext}`);
      await curlDownload(coverUrl, coverPath);
      console.log(`  ✓ 封面已保存: ${coverPath}`);
    } catch (e) {
      console.log(`  ⚠️  封面下载失败: ${e.message}`);
    }
  }

  console.log('\n✅ 完成！\n');
}

async function main() {
  const videoUrl = process.argv[2];
  if (!videoUrl) {
    console.log('用法: node parse2.js <抖音链接>');
    process.exit(1);
  }
  try {
    await run(videoUrl);
  } catch (err) {
    console.error(`❌ 错误: ${err.message}`);
    process.exit(1);
  }
}

main();
