import React from 'react';
import {RagStage} from '../../Main';
import {SHOTS_G0, SHOTS_G0_TOP, BG_G0} from '../G0';
import {SHOTS_G8, BG_G8} from './index';
// 组预览：本组镜头 + G0 覆盖层（章节卡/HUD/流程轨），无音频
export const PreviewG8: React.FC = () => <RagStage shots={[...SHOTS_G0, ...SHOTS_G8, ...SHOTS_G0_TOP]} bg={[...BG_G0, ...BG_G8]} />;
