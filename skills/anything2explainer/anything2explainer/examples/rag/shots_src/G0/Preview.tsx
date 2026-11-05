import React from 'react';
import {RagStage} from '../../Main';
import {SHOTS_G0, SHOTS_G0_TOP, BG_G0} from './index';
export const PreviewG0: React.FC = () => <RagStage shots={[...SHOTS_G0, ...SHOTS_G0_TOP]} bg={BG_G0} />;
