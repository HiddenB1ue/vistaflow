import { useEffect } from 'react';
import { startPriceStream } from '@/services/priceStreamService';
import { usePriceStore } from '@/stores/priceStore';
import { useRouteStore } from '@/stores/routeStore';

export function useJourneyPriceStream(searchId: string | null) {
  const isPriceStreaming = usePriceStore((s) => s.isStreaming);
  const priceFetchedLegs = usePriceStore((s) => s.fetchedLegs);
  const priceTotalLegs = usePriceStore((s) => s.totalLegs);

  useEffect(() => {
    if (!searchId) return;

    const { reset, startStream, mergePrices, endStream } = usePriceStore.getState();
    reset();

    const abort = startPriceStream(searchId, {
      onStarted: (totalLegs) => {
        startStream(totalLegs);
      },
      onPriceBatch: (prices) => {
        mergePrices(prices);
        useRouteStore.getState().updateRoutesPrices(
          usePriceStore.getState().priceMap,
        );
      },
      onLegFetched: (completed) => {
        usePriceStore.setState({ fetchedLegs: completed });
      },
      onComplete: () => {
        endStream();
        useRouteStore.getState().updateRoutesPrices(
          usePriceStore.getState().priceMap,
        );
      },
      onError: (msg) => {
        console.error('Price stream error:', msg);
        endStream();
      },
    });

    return () => {
      abort();
      reset();
    };
  }, [searchId]);

  return {
    isPriceStreaming,
    priceFetchedLegs,
    priceTotalLegs,
  };
}
