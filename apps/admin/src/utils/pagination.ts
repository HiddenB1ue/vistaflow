import { DATA_LABELS } from '@/constants/labels';
import type { PaginationFooterProps } from '@vistaflow/ui';

export const CHINESE_PAGINATION_LABELS: NonNullable<PaginationFooterProps['labels']> = {
  recordsCount: DATA_LABELS.recordsCount,
  pageSummary: DATA_LABELS.pageSummary,
  perPage: '每页',
  itemsUnit: '条',
  jumpTo: '跳转到',
  page: '页',
  jump: '跳转',
  firstPage: '首页',
  prevPage: DATA_LABELS.prevPage,
  nextPage: DATA_LABELS.nextPage,
  lastPage: '末页',
};

interface PaginatedResponse<T> {
  items: T[];
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
}

interface PaginationQuery {
  page: number;
  pageSize: number;
  [key: string]: any;
}

interface UsePaginationFooterOptions<Q extends PaginationQuery, D> {
  query: Q;
  data?: PaginatedResponse<D>;
  onQueryChange: (updater: (current: Q) => Q) => void;
}

export function usePaginationFooter<Q extends PaginationQuery, D>({
  query,
  data,
  onQueryChange,
}: UsePaginationFooterOptions<Q, D>): PaginationFooterProps {
  return {
    page: data?.page ?? query.page,
    pageSize: query.pageSize,
    totalPages: data?.totalPages ?? 0,
    total: data?.total ?? 0,
    onPageChange: (page: number) => {
      onQueryChange((current) => ({ ...current, page }));
    },
    onPageSizeChange: (pageSize: number) => {
      onQueryChange((current) => ({ ...current, pageSize, page: 1 }));
    },
    labels: CHINESE_PAGINATION_LABELS,
  };
}
