import React from 'react';
import {AbsoluteFill, OffthreadVideo, Sequence, staticFile, useCurrentFrame} from 'remotion';
import {W, H, keyframes, DirBlur} from './lib';

/**
 * 实拍/B-roll 层（可选）。素材只能来自 public/assets/<slug>/（免版权来源如 Mixkit，登记 MANIFEST.md：sha256 / 来源 URL / 许可 / 用途）。
 * spec.from/to 为成片帧号；zoom/pan/blur/opacity 关键帧 t 为成片帧号。
 */
export type FootageSpec = {
  from: number; to: number;
  src: string; // 相对 public/
  srcFrom: number; // 素材起始帧（30fps，0 起）
  zoomKf?: Array<[number, number]>; panKf?: Array<[number, number]>; panYKf?: Array<[number, number]>;
  blurKf?: Array<[number, number]>; focusKf?: Array<[number, number]>; opacityKf?: Array<[number, number]>;
  originX?: number; originY?: number; flipX?: boolean;
  grade?: 'dark' | 'none';
  filter?: string;
};
/** 低照暖调 + 暗角（让实拍融入黑底星空） */
export const DarkGrade: React.FC = () => (
  <>
    <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(40,30,20,0.25), rgba(10,8,6,0.35))', mixBlendMode: 'multiply', pointerEvents: 'none'}} />
    <AbsoluteFill style={{background: 'radial-gradient(ellipse 100% 95% at 50% 50%, rgba(0,0,0,0) 45%, rgba(0,0,0,0.6) 100%)', pointerEvents: 'none'}} />
  </>
);
export const FootageClip: React.FC<{spec: FootageSpec}> = ({spec}) => {
  const N = spec.from + useCurrentFrame();
  const scale = spec.zoomKf ? keyframes(N, spec.zoomKf) : 1;
  const pan = spec.panKf ? keyframes(N, spec.panKf) : 0;
  const panY = spec.panYKf ? keyframes(N, spec.panYKf) : 0;
  const blur = spec.blurKf ? keyframes(N, spec.blurKf) : 0;
  const focus = spec.focusKf ? keyframes(N, spec.focusKf) : 0;
  const opacity = spec.opacityKf ? keyframes(N, spec.opacityKf) : 1;
  return (
    <AbsoluteFill style={{overflow: 'hidden', opacity, background: '#0b0908'}}>
      <DirBlur bx={blur + focus} by={blur * 0.15 + focus}>
        <AbsoluteFill style={{transform: `translate(${pan}px, ${panY}px) scale(${scale})${spec.flipX ? ' scaleX(-1)' : ''}`, transformOrigin: `${spec.originX ?? 640}px ${spec.originY ?? 360}px`}}>
          <OffthreadVideo src={staticFile(spec.src)} trimBefore={spec.srcFrom} muted style={{width: W, height: H, objectFit: 'cover', filter: spec.filter ?? 'saturate(0.95) contrast(1.05) brightness(0.9)'}} />
        </AbsoluteFill>
      </DirBlur>
      {(spec.grade ?? 'dark') === 'dark' ? <DarkGrade /> : null}
    </AbsoluteFill>
  );
};
export const FootageTrack: React.FC<{specs: FootageSpec[]}> = ({specs}) => (
  <AbsoluteFill>
    {specs.map((spec) => (
      <Sequence key={`${spec.from}-${spec.src}`} from={spec.from - 1} durationInFrames={spec.to - spec.from + 1}>
        <FootageClip spec={spec} />
      </Sequence>
    ))}
  </AbsoluteFill>
);
