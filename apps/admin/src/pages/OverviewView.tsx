import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ContentSection } from '@vistaflow/ui';
import { fetchApiQuota, fetchSparklineData } from '@/services/overviewService';
import { OverviewInsightsSection, OverviewKpiGrid, OverviewTrendSection } from './overviewSections';

export default function OverviewView() {
  const [range, setRange] = useState<'7d' | '30d'>('7d');
  const { data: sparklineData } = useQuery({
    queryKey: ['admin', 'overview', 'sparkline'],
    queryFn: fetchSparklineData,
  });
  const { data: apiQuota } = useQuery({
    queryKey: ['admin', 'overview', 'quota'],
    queryFn: fetchApiQuota,
  });

  return (
    <div className="vf-page-stack">
      <ContentSection spacing="dense">
        <OverviewKpiGrid />
      </ContentSection>

      <ContentSection spacing="dense">
        <OverviewTrendSection
          range={range}
          onRangeChange={setRange}
          sparklineData={sparklineData}
          apiQuota={apiQuota}
        />
      </ContentSection>

      <ContentSection spacing="dense">
        <OverviewInsightsSection />
      </ContentSection>
    </div>
  );
}
