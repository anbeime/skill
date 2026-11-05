import React from 'react';
import {Stage} from '../../Main';
import {SHOTS_OVERLAY, SHOTS_OVERLAY_TOP, BG_OVERLAY} from '../../overlay';
import {SHOTS_G7, BG_G7, FOOTAGE_G7} from './index';
export const PreviewG7: React.FC = () => <Stage shots={[...SHOTS_OVERLAY, ...SHOTS_G7, ...SHOTS_OVERLAY_TOP]} bg={[...BG_OVERLAY, ...BG_G7]} footage={FOOTAGE_G7} />;
