import './RouteListPanel.css';
import { type RefObject, useEffect, useRef, useState } from 'react';
import type { Route, RouteList } from '@/types/route';
import { JOURNEY_LABELS } from '@/constants/labels';
import type {
  JourneyAvailableFacets,
  JourneyDisplaySortMode,
  JourneyViewResult,
} from '@/services/routeService';
import { PanelCard, SectionHeader } from '@vistaflow/ui';
import { RouteCard } from './RouteCard';
import { SORT_OPTIONS } from './routeList.helpers';

const DISPLAY_SIZE_OPTIONS = [20, 50, 100] as const;
const COMMON_TRAIN_TYPE_ORDER = ['G', 'D', 'C', 'Z', 'T', 'K'] as const;

interface RouteListPanelProps {
  routes: RouteList;
  selectedRoute: Route | null;
  date: string;
  total: number;
  pageSize: number;
  sortMode: JourneyDisplaySortMode;
  appliedView: JourneyViewResult['appliedView'] | null;
  availableFacets: JourneyAvailableFacets;
  showOnlyAvailableTickets: boolean;
  onSelect: (route: Route) => void;
  onSortModeChange: (value: JourneyDisplaySortMode) => void;
  onPageSizeChange: (pageSize: number) => void;
  onTransferCountsChange: (transferCounts: number[]) => void;
  onDisplayTrainTypesChange: (trainTypes: string[]) => void;
  onShowOnlyAvailableTicketsChange: (value: boolean) => void;
  listRef: RefObject<HTMLDivElement | null>;
}

type ToolbarMenu = 'display-size' | null;

interface ToolbarButtonProps {
  active?: boolean;
  label: string;
  onClick: () => void;
}

function ToolbarButton({ active = false, label, onClick }: ToolbarButtonProps) {
  return (
    <button
      type="button"
      className={`route-toolbar-button${active ? ' route-toolbar-button--active' : ''}`}
      onClick={onClick}
    >
      {label}
    </button>
  );
}

function toggleSelection<T extends string | number>(values: T[], value: T): T[] {
  return values.includes(value)
    ? values.filter((item) => item !== value)
    : [...values, value];
}

export function RouteListPanel({
  routes,
  selectedRoute,
  date,
  total,
  pageSize,
  sortMode,
  appliedView,
  availableFacets,
  showOnlyAvailableTickets,
  onSelect,
  onSortModeChange,
  onPageSizeChange,
  onTransferCountsChange,
  onDisplayTrainTypesChange,
  onShowOnlyAvailableTicketsChange,
  listRef,
}: RouteListPanelProps) {
  const toolbarRef = useRef<HTMLDivElement | null>(null);
  const sizeMenuRef = useRef<HTMLDivElement | null>(null);
  const [openMenu, setOpenMenu] = useState<ToolbarMenu>(null);

  const activeTransferCounts = appliedView?.transferCounts ?? [];
  const activeTrainTypes = appliedView?.displayTrainTypes ?? [];
  const prioritizedTrainTypes = [
    ...COMMON_TRAIN_TYPE_ORDER.filter((trainType) =>
      availableFacets.trainTypes.includes(trainType),
    ),
    ...availableFacets.trainTypes.filter(
      (trainType) =>
        !COMMON_TRAIN_TYPE_ORDER.includes(
          trainType as (typeof COMMON_TRAIN_TYPE_ORDER)[number],
        ),
    ),
  ];

  useEffect(() => {
    if (openMenu === null) return;

    function handlePointerDown(event: MouseEvent) {
      const target = event.target as Node;
      const insideToolbar = toolbarRef.current?.contains(target);
      const insideSizeMenu = sizeMenuRef.current?.contains(target);

      if (!insideToolbar && !insideSizeMenu) {
        setOpenMenu(null);
      }
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setOpenMenu(null);
      }
    }

    document.addEventListener('mousedown', handlePointerDown);
    document.addEventListener('keydown', handleEscape);
    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [openMenu]);

  return (
    <PanelCard className="h-full overflow-hidden border-none bg-transparent p-0 shadow-none">
      <div
        className="sticky-header sticky-header--controls shrink-0 px-2 pt-2"
        style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}
      >
        <SectionHeader
          eyebrow={JOURNEY_LABELS.routeListEyebrow}
          title={JOURNEY_LABELS.routeListTitle(date)}
          subtitle={JOURNEY_LABELS.routeListSubtitle(total)}
          actions={
            <div ref={sizeMenuRef} className="route-toolbar-menu">
              <ToolbarButton
                active={openMenu === 'display-size'}
                label={`展示 ${pageSize} 条`}
                onClick={() =>
                  setOpenMenu((current) =>
                    current === 'display-size' ? null : 'display-size',
                  )
                }
              />
              {openMenu === 'display-size' ? (
                <div className="route-toolbar-popover">
                  <div className="route-toolbar-popover__options">
                    {DISPLAY_SIZE_OPTIONS.map((option) => (
                      <button
                        key={`page-size-${option}`}
                        type="button"
                        className={`route-toolbar-option${pageSize === option ? ' route-toolbar-option--active' : ''}`}
                        onClick={() => {
                          onPageSizeChange(option);
                          setOpenMenu(null);
                        }}
                      >
                        <span>{option} 条</span>
                      </button>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          }
        />

        <div ref={toolbarRef} className="route-toolbar">
          <div className="route-toolbar__scroll">
            <div className="route-toolbar__content">
              <div className="route-pill-group" role="tablist" aria-label="排序方式">
                {SORT_OPTIONS.map((option) => (
                  <ToolbarButton
                    key={option.value}
                    active={sortMode === option.value}
                    label={option.label}
                    onClick={() => onSortModeChange(option.value)}
                  />
                ))}
              </div>

              <div className="route-pill-group" role="group" aria-label="换乘次数">
                <ToolbarButton
                  active={activeTransferCounts.length === 0}
                  label="全部"
                  onClick={() => onTransferCountsChange([])}
                />
                {availableFacets.transferCounts.map((transferCount) => (
                  <ToolbarButton
                    key={`transfer-${transferCount}`}
                    active={activeTransferCounts.includes(transferCount)}
                    label={transferCount === 0 ? '直达' : `${transferCount}次`}
                    onClick={() =>
                      onTransferCountsChange(
                        toggleSelection(activeTransferCounts, transferCount).sort(
                          (a, b) => a - b,
                        ),
                      )
                    }
                  />
                ))}
              </div>

              <div className="route-pill-group" role="group" aria-label="车次类型">
                <ToolbarButton
                  active={activeTrainTypes.length === 0}
                  label="全部"
                  onClick={() => onDisplayTrainTypesChange([])}
                />
                {prioritizedTrainTypes.map((trainType) => (
                  <ToolbarButton
                    key={`train-type-${trainType}`}
                    active={activeTrainTypes.includes(trainType)}
                    label={trainType}
                    onClick={() =>
                      onDisplayTrainTypesChange(
                        toggleSelection(activeTrainTypes, trainType).sort(),
                      )
                    }
                  />
                ))}
              </div>

              <ToolbarButton
                active={showOnlyAvailableTickets}
                label={JOURNEY_LABELS.availableTicketsOnly}
                onClick={() => onShowOnlyAvailableTicketsChange(!showOnlyAvailableTickets)}
              />
            </div>
          </div>
        </div>
      </div>

      <div
        ref={listRef}
        className="flex-1 overflow-y-auto scroll-smooth pb-20 pr-4 pt-2"
        style={{ scrollbarWidth: 'none' }}
      >
        {routes.map((route) => (
          <RouteCard
            key={route.id}
            route={route}
            isActive={selectedRoute?.id === route.id}
            onClick={onSelect}
          />
        ))}
      </div>
    </PanelCard>
  );
}
