# Rendering & Setup Guide

## Project Setup

### Initialize Remotion Project

```bash
mkdir remotion-project
cd remotion-project
npx create-video@latest
```

### Project Structure

```
remotion-project/
├── src/
│   ├── Root.tsx              # Main composition
│   ├── slides/
│   │   ├── Cover.tsx
│   │   ├── ContentSlide.tsx
│   │   ├── ChartSlide.tsx
│   │   ├── MindMapSlide.tsx
│   │   └── Summary.tsx
│   ├── components/
│   │   ├── AnimatedCard.tsx
│   │   ├── AnimatedChart.tsx
│   │   └── AnimatedText.tsx
│   └── theme/
│       └── index.ts
├── package.json
└── remotion.config.ts
```

---

## Remotion Config

```typescript
// remotion.config.ts
import { Config } from '@remotion/cli/config';

Config.setVideoImageFormat('jpeg');
Config.setVideoCrf(23);
Config.setVideoMaxConcurrency(2);
Config.setDelayRenderUntilReady(true);
```

---

## Render Commands

```bash
# Preview in browser (development)
npm start

# Render to MP4
npx remotion render out/video.mp4 --concurrency=2

# Render to WebM (smaller)
npx remotion render out/video.webm --output='image-sequence'

# Render specific composition
npx remotion render SlideSequence --composition-id=main

# Render with specific duration
npx remotion render out/video.mp4 --duration-in-frames=300
```

---

## Node.js Compilation Script

```javascript
// scripts/compile.js
const { bundle } = require('@remotion/bundler');
const { render } = require('@remotion/renderer');
const path = require('path');

async function compileToVideo(inputProps) {
  // 1. Bundle the project
  const bundled = await bundle({
    entryPoint: './src/Root.tsx',
    webpackOverride: (config) => config,
  });

  // 2. Render
  await render({
    bundlePath: bundled,
    composition: {
      id: 'main',
      durationInFrames: 300,
      fps: 30,
      width: 1920,
      height: 1080,
    },
    outputLocation: './out/presentation.mp4',
    inputProps,
  });

  console.log('Video rendered successfully!');
}

compileToVideo({ slides: [] }).catch(console.error);
```

---

## Knowledge Base Integration

### Input Schema

```typescript
interface KnowledgeInput {
  topic: string;
  cards: {
    id: string;
    type: 'blue' | 'green' | 'yellow' | 'red';
    title: string;
    content: string;
  }[];
  mindMap?: {
    root: string;
    nodes: { id: string; text: string; children: string[] }[];
  };
  charts?: {
    title: string;
    type: 'bar' | 'line' | 'pie';
    data: { name: string; value: number }[];
  }[];
}
```

### API Endpoint

```typescript
// Backend: routes/remotion_routes.ts
import { Router } from 'express';
import { compileToVideo } from '../services/remotion-compiler';

router.post('/api/remotion/generate', async (req, res) => {
  const { topic, cards, mindMap, charts } = req.body;
  
  // Generate Remotion source
  const source = await generateRemotionSource({ topic, cards, mindMap, charts });
  
  // Render video
  const outputPath = await compileToVideo({ ...req.body, source });
  
  res.json({ videoUrl: outputPath });
});
```

---

## Performance Optimization

### Lazy Loading

```typescript
// Only load heavy components when needed
const ChartSlide = React.lazy(() => import('./slides/ChartSlide'));
const MindMapSlide = React.lazy(() => import('./slides/MindMapSlide'));
```

### Frame Skipping

```typescript
// Skip frames for faster preview
Config.setFrameRange([0, 30]); // First second only
```

### Memory Management

```typescript
// Reduce concurrency to save memory
Config.setVideoMaxConcurrency(1);

// Use lower quality for preview
Config.setVideoCrf(28);
```

---

## Error Handling

```typescript
try {
  await render({
    bundlePath,
    composition,
    outputLocation,
  });
} catch (error) {
  console.error('Render failed:', error);
  // Fallback to static PPT
  await fallbackToPPT(req.body);
}
```

---

## Dependencies

```json
{
  "dependencies": {
    "remotion": "^4.0.0",
    "@remotion/cli": "^4.0.0",
    "@remotion/bundler": "^4.0.0",
    "@remotion/renderer": "^4.0.0",
    "recharts": "^2.10.0",
    "framer-motion": "^10.0.0"
  }
}
```