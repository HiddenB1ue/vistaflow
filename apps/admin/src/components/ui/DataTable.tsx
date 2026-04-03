import type { ReactNode } from 'react';

interface DataTableColumn<T> {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  columns: DataTableColumn<T>[];
  data: T[];
  selectable?: boolean;
  selectedIds?: Set<string>;
  onSelectionChange?: (ids: Set<string>) => void;
  getId: (row: T) => string;
  rowClassName?: (row: T) => string;
}

export function DataTable<T>({
  columns,
  data,
  selectable = false,
  selectedIds,
  onSelectionChange,
  getId,
  rowClassName,
}: DataTableProps<T>) {
  const allSelected = data.length > 0 && data.every(row => selectedIds?.has(getId(row)));

  const toggleAll = () => {
    if (!onSelectionChange) return;
    if (allSelected) {
      onSelectionChange(new Set());
    } else {
      onSelectionChange(new Set(data.map(getId)));
    }
  };

  const toggleRow = (id: string) => {
    if (!onSelectionChange || !selectedIds) return;
    const next = new Set(selectedIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    onSelectionChange(next);
  };

  return (
    <table className="data-table">
      <thead>
        <tr>
          {selectable && (
            <th className="w-12 text-center">
              <input
                type="checkbox"
                checked={allSelected}
                onChange={toggleAll}
                className="accent-[#8B5CF6] cursor-pointer"
              />
            </th>
          )}
          {columns.map((col) => (
            <th key={col.key} className={col.className}>{col.header}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {data.map((row) => {
          const id = getId(row);
          return (
            <tr key={id} className={rowClassName?.(row) ?? ''}>
              {selectable && (
                <td className="text-center">
                  <input
                    type="checkbox"
                    checked={selectedIds?.has(id) ?? false}
                    onChange={() => toggleRow(id)}
                    className="accent-[#8B5CF6] cursor-pointer"
                  />
                </td>
              )}
              {columns.map((col) => (
                <td key={col.key} className={col.className}>{col.render(row)}</td>
              ))}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
