import React from 'react';
import {Stage} from '../../Main';
import {SHOTS_OVERLAY, SHOTS_OVERLAY_TOP, BG_OVERLAY} from '../../overlay';
import {SHOTS_G5, BG_G5, FOOTAGE_G5} from './index';
export const PreviewG5: React.FC = () => <Stage shots={[...SHOTS_OVERLAY, ...SHOTS_G5, ...SHOTS_OVERLAY_TOP]} bg={[...BG_OVERLAY, ...BG_G5]} footage={FOOTAGE_G5} />;
