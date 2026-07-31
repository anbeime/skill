# Slide Types for Remotion Animations

## Slide Type Reference

| Type | Duration | Use Case |
|------|----------|----------|
| `cover` | 3-5s | Title + background animation |
| `content` | 4-6s | Text + visual content |
| `chart` | 5-8s | Data visualization |
| `mindmap` | 6-10s | Mind map expansion |
| `summary` | 3-4s | Key takeaways |

---

## Cover Slide

```tsx
import { AbsoluteFill, useVideoConfig, interpolate, spring } from 'remotion';

export const CoverSlide: React.FC<{ title: string; subtitle?: string }> = ({
  title,
  subtitle
}) => {
  const { fps } = useVideoConfig();
  
  const titleProgress = spring({ fps, config: { damping: 200 } });
  const titleStyle = {
    opacity: interpolate(titleProgress, [0, 1], [0, 1]),
    transform: interpolate(titleProgress, [0, 1], [50, 0]),
  };
  
  return (
    <AbsoluteFill style={{ background: '#1a1a2e' }}>
      <div style={{ ...titleStyle, fontSize: 72, color: 'white', textAlign: 'center' }}>
        {title}
      </div>
      {subtitle && (
        <div style={{ opacity: interpolate(titleProgress, [0.5, 1], [0, 1]), fontSize: 32 }}>
          {subtitle}
        </div>
      )}
    </AbsoluteFill>
  );
};
```

---

## Content Slide (Four-Color Cards)

```tsx
import { AbsoluteFill, useVideoConfig, interpolate, spring } from 'remotion';

interface CardProps {
  title: string;
  content: string;
  cardType: 'blue' | 'green' | 'yellow' | 'red';
  delay?: number;
}

const cardColors = {
  blue: '#3b82f6',
  green: '#22c55e',
  yellow: '#eab308',
  red: '#ef4444',
};

export const ContentSlide: React.FC<{ cards: CardProps[] }> = ({ cards }) => {
  const { fps, durationInFrames } = useVideoConfig();
  
  return (
    <AbsoluteFill style={{ background: '#f8fafc', padding: 40 }}>
      {cards.map((card, i) => (
        <AnimatedCard key={i} {...card} delay={i * 30} />
      ))}
    </AbsoluteFill>
  );
};

const AnimatedCard: React.FC<CardProps> = ({ title, content, cardType, delay = 0 }) => {
  const progress = spring({ fps, config: { damping: 200 }, delayInFrames: delay });
  
  const cardStyle = {
    opacity: interpolate(progress, [0, 0.3], [0, 1]),
    transform: `translateX(${interpolate(progress, [0, 1], [-100, 0])}px)`,
    backgroundColor: cardColors[cardType],
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
  };
  
  return (
    <div style={cardStyle}>
      <div style={{ fontSize: 24, fontWeight: 'bold', color: 'white' }}>{title}</div>
      <div style={{ fontSize: 18, color: 'rgba(255,255,255,0.9)', marginTop: 8 }}>{content}</div>
    </div>
  );
};
```

---

## Chart Slide

```tsx
import { AbsoluteFill, useVideoConfig, interpolate, spring } from 'remotion';
import { BarChart, Bar, XAxis, YAxis, Cell } from 'recharts';

export const ChartSlide: React.FC<{
  title: string;
  data: { name: string; value: number }[];
}> = ({ title, data }) => {
  const { fps } = useVideoConfig();
  const progress = spring({ fps, config: { damping: 150 } });
  
  return (
    <AbsoluteFill style={{ background: 'white', padding: 40 }}>
      <div style={{ fontSize: 36, fontWeight: 'bold', marginBottom: 20 }}>{title}</div>
      <BarChart
        width={900}
        height={400}
        data={data}
        style={{
          opacity: interpolate(progress, [0, 0.5], [0, 1]),
        }}
      >
        <XAxis dataKey="name" />
        <YAxis />
        <Bar dataKey="value" fill="#3b82f6">
          {data.map((_, i) => (
            <Cell key={i} fill={['#3b82f6', '#22c55e', '#eab308', '#ef4444'][i % 4]} />
          ))}
        </Bar>
      </BarChart>
    </AbsoluteFill>
  );
};
```

---

## Summary Slide

```tsx
import { AbsoluteFill, useVideoConfig, interpolate, spring } from 'remotion';

export const SummarySlide: React.FC<{ points: string[] }> = ({ points }) => {
  const progress = spring({ fps, config: { damping: 200 } });
  
  return (
    <AbsoluteFill style={{ background: '#0f172a', justifyContent: 'center', alignItems: 'center' }}>
      <div style={{ fontSize: 48, color: 'white', marginBottom: 40 }}>总结</div>
      {points.map((point, i) => (
        <div
          key={i}
          style={{
            fontSize: 24,
            color: 'white',
            marginBottom: 16,
            opacity: interpolate(progress, [i * 0.2, 1], [0, 1]),
            transform: `translateY(${interpolate(progress, [i * 0.2, 1], [20, 0])}px)`,
          }}
        >
          {i + 1}. {point}
        </div>
      ))}
    </AbsoluteFill>
  );
};
```

---

## Animation Duration Guidelines

| Element Type | Min Duration | Max Duration | Recommended |
|--------------|--------------|--------------|-------------|
| Title | 1.5s | 3s | 2s |
| Single card | 2s | 4s | 3s |
| Chart reveal | 3s | 6s | 4s |
| Mind map | 4s | 10s | 6s |
| Slide transition | 0.3s | 0.8s | 0.5s |