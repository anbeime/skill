#!/bin/bash
# xiaoyue-companion.sh
# 小跃虚拟伴侣 - 生成对话并发送到 OpenClaw

set -euo pipefail

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查环境变量
if [ -z "${ZHIPU_API_KEY:-}" ]; then
  log_error "ZHIPU_API_KEY 环境变量未设置"
  echo "从 https://open.bigmodel.cn 获取 API Key"
  exit 1
fi

# 解析参数
USER_MESSAGE="${1:-}"
SCENE="${2:-general}"
CHANNEL="${3:-}"

if [ -z "$USER_MESSAGE" ]; then
  echo "用法: $0 <用户消息> [场景] [频道]"
  echo ""
  echo "场景选项:"
  echo "  work-start, work-progress, work-tired, work-done"
  echo "  life-coffee, life-gym, life-weekend"
  echo "  mood-happy, mood-tired, mood-focus"
  echo "  general (默认)"
  echo ""
  echo "示例:"
  echo "  $0 \"有点累了\" work-tired"
  echo "  $0 \"终于完成了\" work-done \"#general\""
  exit 1
fi

log_info "场景: $SCENE"
log_info "用户消息: $USER_MESSAGE"

# 生成回应
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESPONSE=$(node "$SCRIPT_DIR/xiaoyue-chat.js" "$USER_MESSAGE" "$SCENE")

if [ $? -ne 0 ]; then
  log_error "对话生成失败"
  exit 1
fi

echo ""
log_info "小跃: $RESPONSE"

# 如果指定了频道，发送消息
if [ -n "$CHANNEL" ]; then
  log_info "发送到频道: $CHANNEL"
  
  openclaw message send \
    --action send \
    --channel "$CHANNEL" \
    --message "$RESPONSE"
  
  # 根据场景发送图片
  ASSETS_DIR="$(dirname "$SCRIPT_DIR")/assets"
  IMAGE_PATH=""
  
  case "$SCENE" in
    work-tired|mood-tired)
      IMAGE_PATH="$ASSETS_DIR/tired-rest.jpg"
      ;;
    mood-happy|work-done)
      IMAGE_PATH="$ASSETS_DIR/celebration.jpg"
      ;;
    life-coffee)
      IMAGE_PATH="$ASSETS_DIR/coffee-break.jpg"
      ;;
    life-gym)
      IMAGE_PATH="$ASSETS_DIR/gym-selfie.jpg"
      ;;
  esac
  
  if [ -n "$IMAGE_PATH" ] && [ -f "$IMAGE_PATH" ]; then
    log_info "发送图片: $(basename "$IMAGE_PATH")"
    openclaw message send \
      --action send \
      --channel "$CHANNEL" \
      --media "file://$IMAGE_PATH"
  fi
  
  log_info "完成!"
fi
