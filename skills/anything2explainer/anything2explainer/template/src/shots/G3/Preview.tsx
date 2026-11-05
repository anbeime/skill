import React from 'react';
import {Stage} from '../../Main';
import {SHOTS_OVERLAY, SHOTS_OVERLAY_TOP, BG_OVERLAY} from '../../overlay';
import {SHOTS_G3, BG_G3, FOOTAGE_G3} from './index';
export const PreviewG3: React.FC = () => <Stage shots={[...SHOTS_OVERLAY, ...SHOTS_G3, ...SHOTS_OVERLAY_TOP]} bg={[...BG_OVERLAY, ...BG_G3]} footage={FOOTAGE_G3} />;
