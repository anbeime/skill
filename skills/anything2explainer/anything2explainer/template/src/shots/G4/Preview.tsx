import React from 'react';
import {Stage} from '../../Main';
import {SHOTS_OVERLAY, SHOTS_OVERLAY_TOP, BG_OVERLAY} from '../../overlay';
import {SHOTS_G4, BG_G4, FOOTAGE_G4} from './index';
export const PreviewG4: React.FC = () => <Stage shots={[...SHOTS_OVERLAY, ...SHOTS_G4, ...SHOTS_OVERLAY_TOP]} bg={[...BG_OVERLAY, ...BG_G4]} footage={FOOTAGE_G4} />;
