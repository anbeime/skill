# Animation Presets for Remotion

## Animation Types

### 1. Entrance Animations

| Name | Effect | Use Case |
|------|--------|----------|
| `fadeIn` | Opacity 0→1 | Simple text reveal |
| `slideInLeft` | TranslateX -100→0 | Cards from left |
| `slideInRight` | TranslateX 100→0 | Cards from right |
| `slideInUp` | TranslateY 50→0 | Cards from bottom |
| `scaleIn` | Scale 0.5→1 | Pop-in effect |
| `bounceIn` | Scale with spring | Attention grab |
| `typewriter` | Character by character | Text reveal |

### 2. Exit Animations

| Name | Effect | Use Case |
|------|--------|----------|
| `fadeOut` | Opacity 1→0 | Simple hide |
| `slideOutRight` | TranslateX 0→100 | Slide off screen |
| `scaleOut` | Scale 1→0 | Shrink away |

### 3. Transition Animations

| Name | Effect | Use Case |
|------|--------|----------|
| `crossFade` | Crossfade between slides | Default |
| `slideOver` | New slide slides over | Page turn |
| `zoomIn` | Zoom into next content | Focus effect |

---

## Spring Presets

```typescript
import { spring } from 'remotion';

const presets = {
  // Gentle (slow settle)
  gentle: { damping: 300, stiffness: 100 },
  
  // Default (balanced)
  default: { damping: 200, stiffness: 200 },
  
  // Bouncy (exaggerated)
  bouncy: { damping: 100, stiffness: 300 },
  
  // Snappy (quick)
  snappy: { damping: 150, stiffness: 400 },
};

// Usage
const progress = spring({
  fps,
  config: presets.bouncy
});
```

---

## Easing Functions

```typescript
import { interpolate, Easing } from 'remotion';

// Common easings
const easings = {
  linear: Easing.in(Easing.linear),
  easeIn: Easing.in(Easing.ease),
  easeOut: Easing.out(Easing.ease),
  easeInOut: Easing.inOut(Easing.ease),
  
  // Special easings
  easeInQuad: Easing.in(Easing.quad),
  easeOutQuad: Easing.out(Easing.quad),
  easeInOutQuad: Easing.inOut(Easing.quad),
  
  // Bounce
  bounceOut: Easing.out(Easing.bezier(0.33, 1, 0.68, 1)),
};

// Usage
const style = {
  transform: interpolate(progress, [0, 1], [0, 100], {
    easing: easings.easeOutQuad,
  }),
};
```

---

## Four-Color Card Animations

```typescript
import { spring, interpolate, useVideoConfig } from 'remotion';

const cardAnimations = {
  // 事实 (Blue) - Professional slide from left
  blue: {
    enter: (progress: number, style: any) => ({
      ...style,
      transform: `translateX(${interpolate(progress, [0, 1], [-80, 0])}px)`,
      opacity: interpolate(progress, [0, 0.3, 1], [0, 1, 1]),
    }),
    duration: 0.8,
  },
  
  // 解释 (Green) - Explanatory fade + scale
  green: {
    enter: (progress: number, style: any) => ({
      ...style,
      transform: `scale(${interpolate(progress, [0, 1], [0.8, 1])}px)`,
      opacity: interpolate(progress, [0, 1], [0, 1]),
    }),
    duration: 0.6,
  },
  
  // 风险 (Yellow) - Warning shake
  yellow: {
    enter: (progress: number, style: any) => {
      const shake = interpolate(progress, [0, 0.5, 0.7, 0.9, 1], [0, 5, -3, 1, 0]);
      return {
        ...style,
        transform: `translateX(${shake}px) scale(${interpolate(progress, [0, 1], [0.9, 1])})`,
        opacity: interpolate(progress, [0, 1], [0, 1]),
      };
    },
    duration: 1.0,
  },
  
  // 行动 (Red) - Urgent bounce
  red: {
    enter: (progress: number, style: any) => {
      const scale = interpolate(progress, [0, 0.5, 0.7, 1], [0.5, 1.1, 0.95, 1]);
      return {
        ...style,
        transform: `scale(${scale})`,
        opacity: interpolate(progress, [0, 1], [0, 1]),
      };
    },
    duration: 0.7,
  },
};
```

---

## Chart Animations

```typescript
// Bar chart grow animation
const animateBarChart = (progress: number, maxHeight: number) => {
  return {
    height: interpolate(progress, [0, 1], [0, maxHeight]),
  };
};

// Line chart draw animation
const animateLineChart = (progress: number, points: number[]) => {
  const pointCount = Math.floor(interpolate(progress, [0, 1], [0, points.length]));
  return points.slice(0, pointCount);
};

// Pie chart fill animation
const animatePieChart = (progress: number, slices: Slice[]) => {
  return slices.map((slice, i) => ({
    ...slice,
    endAngle: interpolate(progress, [0, 1], [slice.startAngle, slice.endAngle]),
  }));
};
```

---

## Text Animations

```typescript
// Typewriter effect
const typewriterStyle = (progress: number, text: string) => {
  const charCount = Math.floor(interpolate(progress, [0, 1], [0, text.length]));
  return text.slice(0, charCount);
};

// Staggered word reveal
const staggeredWordsStyle = (progress: number, words: string[], delay: number = 0.1) => {
  return words.map((word, i) => ({
    opacity: interpolate(progress, [i * delay, i * delay + 0.3], [0, 1]),
  }));
};

// Highlight pulse
const highlightPulse = (progress: number) => {
  return {
    boxShadow: `0 0 ${interpolate(progress, [0, 0.5, 1], [0, 20, 0])}px rgba(59, 130, 246, 0.5)`,
  };
};
```