import React from 'react';
import {Stage} from '../../Main';
import {SHOTS_OVERLAY, SHOTS_OVERLAY_TOP, BG_OVERLAY} from '../../overlay';
import {SHOTS_G8, BG_G8, FOOTAGE_G8} from './index';
export const PreviewG8: React.FC = () => <Stage shots={[...SHOTS_OVERLAY, ...SHOTS_G8, ...SHOTS_OVERLAY_TOP]} bg={[...BG_OVERLAY, ...BG_G8]} footage={FOOTAGE_G8} />;
