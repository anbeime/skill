#!/bin/zsh
# 从模板创建新项目：new_project.sh <目标目录> <slug>
set -e
HERE=$(cd "$(dirname "$0")/.." && pwd)
DEST=$1; SLUG=${2:-video}
[ -n "$DEST" ] || { echo "usage: new_project.sh <dest_dir> <slug>"; exit 1; }
# 本脚本必须留在 template/scripts/ 里：$HERE 是下面 rsync 的源，脚本被单独拷到别处时
# $HERE 会指向无关目录（最坏是 /），rsync 就会去复制那整棵目录树
[ -f "$HERE/src/config.ts" ] && [ -d "$HERE/src/common" ] || { echo "找不到模板（$HERE 不像 template/），请从 template/scripts/ 里运行本脚本"; exit 1; }
# slug 会进文件名、sed 表达式与渲染命令行，只允许安全字符
case "$SLUG" in
  ''|*[!A-Za-z0-9_-]*) echo "slug 只能用字母/数字/-/_，收到：$SLUG"; exit 1;;
esac
mkdir -p "$DEST"
rsync -a --exclude node_modules --exclude 'build*' --exclude renders --exclude fin_frames --exclude stills --exclude 'audio/cache' "$HERE/" "$DEST/"
# portable in-place edit: `-i.bak` + rm works on both BSD/macOS and GNU/Linux sed
# (BSD `sed -i ''` breaks on GNU sed, which reads '' as the script and config.ts as a file)
sed -i.bak "s/slug: 'demo'/slug: '$SLUG'/" "$DEST/src/config.ts" && rm -f "$DEST/src/config.ts.bak"
mkdir -p "$DEST/public/assets/$SLUG" "$DEST/script" "$DEST/research" "$DEST/qc" "$DEST/stills" "$DEST/renders"
cd "$DEST" && npm install --silent && npx tsc --noEmit && echo "project ready: $DEST (slug=$SLUG)"
