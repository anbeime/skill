# Remix Dependency Graph — 2.24.21

“只改一个变量”不是整组重抽。冻结未受影响变量，只重算目标及必要下游。

| Target | Always invalidate | Conditional invalidate |
|---|---|---|
| location | scene, props, pose_shot, share_card, render | hairstyle, makeup, wardrobe when climate/environment materially changes them |
| era / worldview | wardrobe, hairstyle, makeup, scene, props, pose_shot, share_card, render | — |
| wardrobe | hairstyle, makeup, pose_shot, share_card, render | props when owned/worn props change |
| hairstyle | makeup, pose_shot, render | share_card when hair is a visual hook |
| makeup | pose_shot, render | share_card when makeup is a visual hook |
| relationship | pose_emotion, pose_shot, share_card, render | wardrobe only if role/formality changes |
| color | wardrobe_palette, hairstyle, makeup, lighting, pose_shot, share_card, render | — |
| photography_style | lighting, composition, pose_shot, share_card, render | makeup when finish conflicts with new style |

方向阶段妆发是正式锁；只有本图判定失效时才重跑。换服装、换年代、换世界观默认都会重跑妆发。
