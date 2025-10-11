import { styled, keyframes } from 'goober';

const circleAnimation = keyframes`
from {
  transform: scale(0) rotate(45deg);
	opacity: 0;
}
to {
 transform: scale(1) rotate(45deg);
  opacity: 1;
}`;

const firstLineAnimation = keyframes`
from {
  transform: scale(0);
  opacity: 0;
}
to {
  transform: scale(1);
  opacity: 1;
}`;

const secondLineAnimation = keyframes`
from {
  transform: scale(0) rotate(90deg);
	opacity: 0;
}
to {
  transform: scale(1) rotate(90deg);
	opacity: 1;
}`;

export interface ErrorTheme {
  primary?: string;
  secondary?: string;
}

export const ErrorIcon = styled('div')<ErrorTheme>`
  width: 20px;
  opacity: 0;
  height: 20px;
  border-radius: 10px;
  background: ${(p) => p.primary || '#ff4b4b'};
  position: relative;
  transform: rotate(45deg);

  animation: ${circleAnimation} 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)
    forwards;
  animation-delay: 100ms;

  &:after,
  &:before {
    content: '';
    animation: ${firstLineAnimation} 0.15s ease-out forwards;
    animation-delay: 150ms;
    position: absolute;
    border-radius: 3px;
    opacity: 0;
    background: ${(p) => p.secondary || '#fff'};
    bottom: 9px;
    left: 4px;
    height: 2px;
    width: 12px;
  }

  &:before {
    animation: ${secondLineAnimation} 0.15s ease-out forwards;
    animation-delay: 180ms;
    transform: rotate(90deg);
  }
`;
