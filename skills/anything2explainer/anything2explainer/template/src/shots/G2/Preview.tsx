import React from 'react';
import {Stage} from '../../Main';
import {SHOTS_OVERLAY, SHOTS_OVERLAY_TOP, BG_OVERLAY} from '../../overlay';
import {SHOTS_G2, BG_G2, FOOTAGE_G2} from './index';
export const PreviewG2: React.FC = () => <Stage shots={[...SHOTS_OVERLAY, ...SHOTS_G2, ...SHOTS_OVERLAY_TOP]} bg={[...BG_OVERLAY, ...BG_G2]} footage={FOOTAGE_G2} />;
