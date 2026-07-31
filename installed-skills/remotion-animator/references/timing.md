# Timing Reference for Remotion Animations

## Frame Calculations

```typescript
// FPS: 30 (default for Remotion)
const FPS = 30;

// Convert seconds to frames
const secondsToFrames = (seconds: number) => seconds * FPS;

// Common durations
const DURATIONS = {
  instant: 0.1,    // 3 frames
  fast: 0.3,       // 9 frames
  normal: 0.5,     // 15 frames
  slow: 1.0,       // 30 frames
  extraSlow: 2.0,  // 60 frames
};

// Total slide durations (in frames at 30fps)
const SLIDE_DURATIONS = {
  cover: 150,      // 5s
  content: 180,    // 6s
  chart: 240,      // 8s
  mindmap: 300,    // 10s
  summary: 120,    // 4s
};
```

---

## Standard Timeline Layout

### 3-Second Content Slide

| Phase | Frames | Time | Content |
|-------|--------|------|---------|
| Wait | 0-15 | 0-0.5s | Buffer before start |
| Title | 15-45 | 0.5-1.5s | Title appears |
| Content | 45-105 | 1.5-3.5s | Card content reveals |
| Hold | 105-150 | 3.5-5s | Hold for reading |
| Exit | 150-165 | 5-5.5s | Slide out |

### 5-Second Chart Slide

| Phase | Frames | Time | Content |
|-------|--------|------|---------|
| Wait | 0-15 | 0-0.5s | Buffer |
| Chart Intro | 15-45 | 0.5-1.5s | Chart container appears |
| Data Reveal | 45-105 | 1.5-3.5s | Bars/lines grow |
| Labels | 105-135 | 3.5-4.5s | Labels appear |
| Hold | 135-150 | 4.5-5s | Hold |
| Exit | 150-165 | 5-5.5s | Exit |

---

## Animation Staggering

```typescript
// Stagger children with delay
const staggerDelay = 15; // frames between each item

cards.map((card, i) => {
  const cardProgress = spring({
    fps,
    config: { damping: 200 },
    delayInFrames: i * staggerDelay,  // Stagger
  });
  
  return (
    <div
      style={{
        opacity: interpolate(cardProgress, [0, 1], [0, 1]),
        transform: `translateY(${interpolate(cardProgress, [0, 1], [30, 0])}px)`,
      }}
    >
      {card.content}
    </div>
  );
});
```

### Stagger Presets

| Item Count | Delay Between Items | Total Animation Time |
|------------|--------------------|-----------------------|
| 2 items | 20 frames (0.67s) | ~2.5s |
| 3 items | 15 frames (0.5s) | ~2.5s |
| 4 items | 12 frames (0.4s) | ~2.8s |
| 5+ items | 10 frames (0.33s) | ~3s |

---

## Easing Reference

```typescript
// Quick reference for spring configs
const SPRING_CONFIGS = {
  // Very bouncy (for attention)
  bouncy: { damping: 80, stiffness: 300, mass: 1 },
  
  // Default (good for most)
  default: { damping: 200, stiffness: 200, mass: 1 },
  
  // Gentle (for professional)
  gentle: { damping: 300, stiffness: 100, mass: 1 },
  
  // Snappy (for UI elements)
  snappy: { damping: 150, stiffness: 400, mass: 1 },
};

// Duration estimates at 30fps
// bouncy: ~0.5s
// default: ~0.7s
// gentle: ~1.2s
// snappy: ~0.4s
```

---

## Video Length Calculator

```typescript
// Calculate total video duration from slides
interface SlideConfig {
  type: 'cover' | 'content' | 'chart' | 'mindmap' | 'summary';
  cardCount?: number;  // For content slides
  dataPoints?: number;  // For chart slides
}

const calculateDuration = (slides: SlideConfig[], fps: number = 30): number => {
  let totalFrames = 0;
  
  for (const slide of slides) {
    switch (slide.type) {
      case 'cover':
        totalFrames += 150; // 5s
        break;
      case 'content':
        // Base 4s + 0.5s per card
        totalFrames += 120 + (slide.cardCount || 1) * 15;
        break;
      case 'chart':
        // Base 5s + 0.3s per data point
        totalFrames += 150 + (slide.dataPoints || 5) * 9;
        break;
      case 'mindmap':
        totalFrames += 240; // 8s
        break;
      case 'summary':
        totalFrames += 120; // 4s
        break;
    }
    // Add transition time
    totalFrames += 15; // 0.5s transition
  }
  
  return totalFrames / fps; // Return seconds
};

// Example
const slides = [
  { type: 'cover' },
  { type: 'content', cardCount: 4 },
  { type: 'chart', dataPoints: 6 },
  { type: 'summary' },
];

console.log(calculateDuration(slides)); // ~18 seconds
```