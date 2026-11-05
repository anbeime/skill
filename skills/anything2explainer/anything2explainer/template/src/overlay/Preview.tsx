import React from 'react';
import {Stage} from '../Main';
import {SHOTS_OVERLAY, SHOTS_OVERLAY_TOP, BG_OVERLAY} from './index';
export const PreviewOverlay: React.FC = () => <Stage shots={[...SHOTS_OVERLAY, ...SHOTS_OVERLAY_TOP]} bg={BG_OVERLAY} />;
