
import { useMemo } from 'react';
import { SEARCH_LABELS } from '@/constants/labels';

export function useTimeGreeting(): string {
  return useMemo(() => {
    const hour = new Date().getHours();
    if (hour >= 5 && hour < 12) return SEARCH_LABELS.greetingMorning;
    if (hour >= 12 && hour < 14) return SEARCH_LABELS.greetingNoon;
    if (hour >= 14 && hour < 18) return SEARCH_LABELS.greetingAfternoon;
    return SEARCH_LABELS.greetingEvening;
  }, []);
}
