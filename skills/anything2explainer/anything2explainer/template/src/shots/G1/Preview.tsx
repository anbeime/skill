import React from 'react';
import {Stage} from '../../Main';
import {SHOTS_OVERLAY, SHOTS_OVERLAY_TOP, BG_OVERLAY} from '../../overlay';
import {SHOTS_G1, BG_G1, FOOTAGE_G1} from './index';
export const PreviewG1: React.FC = () => <Stage shots={[...SHOTS_OVERLAY, ...SHOTS_G1, ...SHOTS_OVERLAY_TOP]} bg={[...BG_OVERLAY, ...BG_G1]} footage={FOOTAGE_G1} />;
