import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useBlink } from './useBlink';

describe('useBlink', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should not blink when trigger is falsy', () => {
    const { result } = renderHook(() => useBlink(null, 1000));
    expect(result.current).toBe(false);
  });

  it('should start blinking when trigger changes', () => {
    const { result, rerender } = renderHook(
      ({ trigger }) => useBlink(trigger, 1000),
      { initialProps: { trigger: null as any } }
    );

    expect(result.current).toBe(false);

    // Update trigger
    rerender({ trigger: 'something' });
    expect(result.current).toBe(true);
  });

  it('should stop blinking after duration', () => {
    const { result } = renderHook(() => useBlink('trigger', 1000));

    expect(result.current).toBe(true);

    act(() => {
      vi.advanceTimersByTime(1000);
    });

    expect(result.current).toBe(false);
  });

  it('should use custom duration', () => {
    const { result } = renderHook(() => useBlink('trigger', 500));

    expect(result.current).toBe(true);

    act(() => {
      vi.advanceTimersByTime(499);
    });
    expect(result.current).toBe(true);

    act(() => {
      vi.advanceTimersByTime(1);
    });
    expect(result.current).toBe(false);
  });
}); 