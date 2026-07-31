/**
 * 视频下载模块 (v2.7 - 安全加固版)
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

/**
 * 确保目录存在
 */
function ensureDir(dirPath) {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
}

/**
 * 格式化字节大小
 */
function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

/**
 * 安全执行外部命令 (使用 spawn 代替 exec，防止命令注入)
 */
function runCommand(command, args, timeout = 60000) {
  return new Promise((resolve, reject) => {
    const proc = spawn(command, args);
    let errorOutput = '';

    const timer = setTimeout(() => {
      proc.kill();
      reject(new Error(`${command} 执行超时 (${timeout}ms)`));
    }, timeout);

    proc.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });

    proc.on('close', (code) => {
      clearTimeout(timer);
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`${command} 退出码 ${code}: ${errorOutput}`));
      }
    });

    proc.on('error', (err) => {
      clearTimeout(timer);
      reject(err);
    });
  });
}

/**
 * 使用系统 curl 下载 (安全重构)
 */
async function downloadWithCurl(url, filePath) {
  const ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_8 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1';
  
  // 使用 spawn 参数数组，自动处理转义，彻底杜绝注入隐患
  const args = [
    '-L',                // 跟踪重定向
    '-A', ua,            // 设置 UA
    '-s',                // 静默
    '-g',                // 禁用 URL 通配符
    url,                 // 目标 URL
    '-o', filePath       // 输出路径
  ];

  try {
    await runCommand('curl', args);
    
    if (fs.existsSync(filePath)) {
      const stats = fs.statSync(filePath);
      if (stats.size < 10000) { // 检查文件头
          const fd = fs.openSync(filePath, 'r');
          const buffer = Buffer.alloc(10);
          fs.readSync(fd, buffer, 0, 10, 0);
          const firstBytes = buffer.toString('utf8');
          fs.closeSync(fd);
          
          if (firstBytes.includes('<html') || firstBytes.includes('<!DOC')) {
            fs.unlinkSync(filePath);
            throw new Error('抓取到了网页内容（可能是反爬虫拦截）');
          }
      }
      return { success: true, size: stats.size };
    }
    throw new Error('下载未生成文件');
  } catch (error) {
    if (fs.existsSync(filePath)) try { fs.unlinkSync(filePath); } catch(e) {}
    throw error;
  }
}

/**
 * 主下载入口
 */
async function downloadVideo(videoUrl, outputDir, videoId, options = {}) {
  ensureDir(outputDir);
  const filename = options.filename || `${videoId}.mp4`;
  const filePath = path.join(outputDir, filename);
  
  console.log(`  🚀 正在尝试无水印解析下载...`);
  
  // 核心去水印链接构造 (严格白名单过滤)
  let downloadUrl = videoUrl;
  if (videoId && !videoUrl.includes('video_id=')) {
      // 仅允许字母、数字和下划线的 video_id，防止非法构造
      if (/^[a-z0-9A-Z_]+$/.test(videoId)) {
          downloadUrl = `https://aweme.snssdk.com/aweme/v1/play/?video_id=${videoId}&ratio=1080p&line=0`;
      }
  }
  
  // 确保是 play 而不是 playwm
  downloadUrl = downloadUrl.replace('playwm', 'play');

  try {
    const result = await downloadWithCurl(downloadUrl, filePath);
    if (result.success) {
      console.log(`  ✅ 下载完成: ${filename} (${formatBytes(result.size)})`);
      return { success: true, filePath, size: result.size };
    }
  } catch (err) {
    console.log(`  ⚠️ Curl 下载失败: ${err.message}`);
    
    // 备选方案: 安全运行 yt-dlp
    try {
      console.log(`  🔄 尝试 yt-dlp 备选通道...`);
      const ytArgs = ['-o', filePath, '--user-agent', 'Mozilla/5.0', downloadUrl];
      await runCommand('yt-dlp', ytArgs);
      
      if (fs.existsSync(filePath) && fs.statSync(filePath).size > 50000) {
        return { success: true, filePath, size: fs.statSync(filePath).size };
      }
    } catch (ytErr) {
      console.log(`  ❌ yt-dlp 也失败了`);
    }
  }

  throw new Error('下载失败：所有路径均无法获取有效的视频流');
}

module.exports = {
  downloadVideo,
  ensureDir,
  formatBytes
};
