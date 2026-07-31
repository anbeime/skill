/**
 * 抖音链接解析模块
 * 使用 Playwright 绕过反爬，获取视频下载链接
 */

const { chromium } = require('playwright-chromium');
const { URL } = require('url');
const fs = require('fs');

/**
 * 解析短链接
 */
async function resolveShortUrl(shortUrl) {
  console.log(`  🔍 解析短链接: ${shortUrl}`);
  
  let browser;
  try {
    browser = await chromium.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
  } catch (error) {
    if (error.message.includes('executable doesn\'t exist')) {
      throw new Error('Playwright 浏览器未安装。请运行: npx playwright install chromium');
    }
    throw error;
  }
  
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'
  });
  
  const page = await context.newPage();
  
  try {
    await page.goto(shortUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(3000);
    
    const finalUrl = page.url();
    console.log(`  ✓ 解析完成: ${finalUrl}`);
    
    await browser.close();
    return finalUrl;
  } catch (error) {
    await browser.close();
    throw error;
  }
}

/**
 * 从完整 URL 中提取视频 ID
 */
function extractVideoId(url) {
  const match = url.match(/\/video\/(\d+)/);
  if (match) return match[1];
  
  const paths = url.split('/');
  for (const path of paths) {
    if (/^\d{10,}$/.test(path)) {
      return path;
    }
  }
  return Date.now().toString();
}

/**
 * 解析视频信息（播放器页面数据提取）
 */
async function fetchVideoInfo(url) {
  console.log(`  🌐 启动浏览器获取视频信息...`);
  
  let browser;
  try {
    browser = await chromium.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
  } catch (error) {
    return { success: false, error: error.message };
  }
  
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_8 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1'
  });
  
  const page = await context.newPage();
  
  try {
    let videoId = null;
    let awemeDetail = null;

    // 使用 waitForResponse 可靠地拦截 API 响应
    console.log('  🔍 等待 API 响应...');
    const responsePromise = page.waitForResponse(
      res => {
        const match = res.url().includes('aweme/v1/web/aweme/detail');
        return match;
      },
      { timeout: 20000 }
    );

    await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });

    let apiResponse = null;
    try {
      apiResponse = await responsePromise;
      console.log(`  ✓ 捕获 API 响应: ${apiResponse.url().substring(0, 80)}`);
    } catch (e) {
      console.log(`  ⚠️  API 响应超时: ${e.message}`);
    }

    if (apiResponse) {
      try {
        const json = await apiResponse.json();
        fs.writeFileSync('/tmp/aweme_debug.json', JSON.stringify(json, null, 2));
        console.log('  ✓ API 数据已保存到 /tmp/aweme_debug.json');
        awemeDetail = json?.aweme_detail || json?.data?.aweme_detail || json || null;
        if (awemeDetail?.video?.play_addr?.uri) {
          videoId = awemeDetail.video.play_addr.uri;
        }
      } catch (e) { console.log(`  ⚠️  API 解析失败: ${e.message}`); }
    }

    // 兜底：从页面内容提取 video_id
    if (!videoId) {
      const content = await page.content();
      const vidMatch = content.match(/\"vid\":\"([a-z0-9_]+)\"/i) ||
                       content.match(/video_id=([a-z0-9_]+)/i) ||
                       content.match(/\"uri\":\"([a-z0-9_]+)\"/i);
      if (vidMatch) videoId = vidMatch[1];
    }
    if (!videoId) {
      const urlMatch = url.match(/\/video\/(\d+)/);
      if (urlMatch) videoId = urlMatch[1];
    }

    // 统一构造无水印 1080P 下载链接
    let finalDownloadUrl = videoId ? `https://aweme.snssdk.com/aweme/v1/play/?video_id=${videoId}&ratio=1080p&line=0` : null;
    
        const videoInfo = await page.evaluate(() => {
      return {
        title: document.title,
        description: document.querySelector('meta[name="description"]')?.content
      };
    });
    
    // 从 awemeDetail 提取更多信息
    let coverUrl = null;
    let videoDesc = null;
    let authorName = null;
    if (awemeDetail) {
      videoDesc = awemeDetail.desc || null;
      authorName = awemeDetail.author?.nickname || awemeDetail.author?.unique_id || null;
      const cover = awemeDetail.video?.cover || awemeDetail.video?.origin_cover;
      if (cover?.url_list?.length > 0) {
        coverUrl = cover.url_list[0];
      }
    }
    
    await browser.close();
    
    return {
      success: !!finalDownloadUrl,
      downloadUrl: finalDownloadUrl,
      videoId,
      info: videoInfo,
      videoDesc,
      authorName,
      coverUrl
    };
  } catch (error) {
    await browser.close();
    return { success: false, error: error.message };
  }
}

/**
 * 主解析函数
 */
async function parseDouyinUrl(inputUrl) {
  try {
    let targetUrl = inputUrl;
    if (inputUrl.includes('v.douyin.com')) {
      targetUrl = await resolveShortUrl(inputUrl);
    }
    
    const result = await fetchVideoInfo(targetUrl);
    
    // 最终兜底：强制转换任何链接为无水印版
    if (result.downloadUrl) {
      result.downloadUrl = result.downloadUrl.replace('playwm', 'play');
    }

    return {
      videoId: result.videoId || extractVideoId(targetUrl),
      originalUrl: inputUrl,
      targetUrl,
      ...result
    };
  } catch (error) {
    throw new Error(`解析失败: ${error.message}`);
  }
}

module.exports = {
  parseDouyinUrl,
  resolveShortUrl,
  extractVideoId,
  fetchVideoInfo
};
