import { useState } from 'react';
import { Button } from './Button';
import { CustomSelect } from './CustomSelect';
import { InputBox } from './InputBox';

export interface PaginationFooterProps {
  page: number;
  pageSize: number;
  totalPages: number;
  total: number;
  pageSizeOptions?: number[];
  onPageChange: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
  labels?: {
    recordsCount?: (total: number) => string;
    pageSummary?: (page: number, totalPages: number) => string;
    perPage?: string;
    itemsUnit?: string;
    jumpTo?: string;
    page?: string;
    jump?: string;
    firstPage?: string;
    prevPage?: string;
    nextPage?: string;
    lastPage?: string;
  };
}

const defaultLabels = {
  recordsCount: (total: number) => `Total ${total} records`,
  pageSummary: (page: number, totalPages: number) => `Page ${page} / ${Math.max(totalPages, 1)}`,
  perPage: 'Per page',
  itemsUnit: 'items',
  jumpTo: 'Jump to',
  page: 'page',
  jump: 'Go',
  firstPage: 'First',
  prevPage: 'Previous',
  nextPage: 'Next',
  lastPage: 'Last',
};

export function PaginationFooter({
  page,
  pageSize,
  totalPages,
  total,
  pageSizeOptions = [20, 50, 100, 200],
  onPageChange,
  onPageSizeChange,
  labels = {},
}: PaginationFooterProps) {
  const [jumpToPage, setJumpToPage] = useState('');
  const mergedLabels = { ...defaultLabels, ...labels };

  const handleJumpToPage = () => {
    const pageNum = parseInt(jumpToPage, 10);
    if (!isNaN(pageNum) && pageNum >= 1 && pageNum <= totalPages) {
      onPageChange(pageNum);
      setJumpToPage('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleJumpToPage();
    }
  };

  return (
    <div className="flex flex-col gap-3 border-t border-white/5 px-5 py-4 text-xs text-muted sm:flex-row sm:items-center sm:justify-between">
      <div className="flex flex-wrap items-center gap-4">
        <span>{mergedLabels.recordsCount(total)}</span>
        <span>{mergedLabels.pageSummary(page, totalPages)}</span>
        {onPageSizeChange && (
          <div className="flex items-center gap-2">
            <span>{mergedLabels.perPage}</span>
            <CustomSelect
              options={pageSizeOptions.map((size) => ({
                value: String(size),
                label: `${size} ${mergedLabels.itemsUnit}`,
              }))}
              value={String(pageSize)}
              onChange={(value) => onPageSizeChange(Number(value))}
              className="w-[100px]"
            />
          </div>
        )}
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <Button variant="outline" size="sm" onClick={() => onPageChange(1)} disabled={page <= 1}>
          {mergedLabels.firstPage}
        </Button>
        <Button variant="outline" size="sm" onClick={() => onPageChange(page - 1)} disabled={page <= 1}>
          {mergedLabels.prevPage}
        </Button>
        <div className="flex items-center gap-2">
          <span>{mergedLabels.jumpTo}</span>
          <InputBox
            type="text"
            inputMode="numeric"
            pattern="[0-9]*"
            value={jumpToPage}
            onChange={(e) => setJumpToPage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={String(page)}
            className="w-[60px] text-center"
          />
          <span>{mergedLabels.page}</span>
          <Button variant="outline" size="sm" onClick={handleJumpToPage} disabled={!jumpToPage || totalPages === 0}>
            {mergedLabels.jump}
          </Button>
        </div>
        <Button variant="outline" size="sm" onClick={() => onPageChange(page + 1)} disabled={totalPages === 0 || page >= totalPages}>
          {mergedLabels.nextPage}
        </Button>
        <Button variant="outline" size="sm" onClick={() => onPageChange(totalPages)} disabled={totalPages === 0 || page >= totalPages}>
          {mergedLabels.lastPage}
        </Button>
      </div>
    </div>
  );
}
