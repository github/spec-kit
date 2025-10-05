import * as React from 'react';
import { styled, keyframes } from 'goober';

import { Toast } from '../core/types';
import { ErrorIcon, ErrorTheme } from './error';
import { LoaderIcon, LoaderTheme } from './loader';
import { CheckmarkIcon, CheckmarkTheme } from './checkmark';

const StatusWrapper = styled('div')`
  position: absolute;
`;

const IndicatorWrapper = styled('div')`
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  min-width: 20px;
  min-height: 20px;
`;

const enter = keyframes`
from {
  transform: scale(0.6);
  opacity: 0.4;
}
to {
  transform: scale(1);
  opacity: 1;
}`;

export const AnimatedIconWrapper = styled('div')`
  position: relative;
  transform: scale(0.6);
  opacity: 0.4;
  min-width: 20px;
  animation: ${enter} 0.3s 0.12s cubic-bezier(0.175, 0.885, 0.32, 1.275)
    forwards;
`;

export type IconThemes = Partial<{
  success: CheckmarkTheme;
  error: ErrorTheme;
  loading: LoaderTheme;
}>;

export const ToastIcon: React.FC<{
  toast: Toast;
}> = ({ toast }) => {
  const { icon, type, iconTheme } = toast;
  if (icon !== undefined) {
    if (typeof icon === 'string') {
      return <AnimatedIconWrapper>{icon}</AnimatedIconWrapper>;
    } else {
      return icon;
    }
  }

  if (type === 'blank') {
    return null;
  }

  return (
    <IndicatorWrapper>
      <LoaderIcon {...iconTheme} />
      {type !== 'loading' && (
        <StatusWrapper>
          {type === 'error' ? (
            <ErrorIcon {...iconTheme} />
          ) : (
            <CheckmarkIcon {...iconTheme} />
          )}
        </StatusWrapper>
      )}
    </IndicatorWrapper>
  );
};
