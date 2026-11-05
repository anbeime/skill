import React from 'react';
import {Stage} from '../../Main';
import {SHOTS_OVERLAY, SHOTS_OVERLAY_TOP, BG_OVERLAY} from '../../overlay';
import {SHOTS_G6, BG_G6, FOOTAGE_G6} from './index';
export const PreviewG6: React.FC = () => <Stage shots={[...SHOTS_OVERLAY, ...SHOTS_G6, ...SHOTS_OVERLAY_TOP]} bg={[...BG_OVERLAY, ...BG_G6]} footage={FOOTAGE_G6} />;
