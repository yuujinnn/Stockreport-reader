import { useState, useEffect } from 'react';

export function useBlink(trigger: any, duration = 1000) {
  const [isBlinking, setIsBlinking] = useState(false);

  useEffect(() => {
    if (!trigger) return;

    setIsBlinking(true);
    const timer = setTimeout(() => {
      setIsBlinking(false);
    }, duration);

    return () => clearTimeout(timer);
  }, [trigger, duration]);

  return isBlinking;
} 