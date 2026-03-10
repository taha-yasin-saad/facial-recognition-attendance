import React from 'react';

interface Column<T> {
  header: string;
  accessor: keyof T | ((row: T) => React.ReactNode);
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
}

function DataTable<T extends object>({ columns, data }: DataTableProps<T>) {
  const [sortKey, setSortKey] = React.useState<keyof T | null>(null);
  const [ascending, setAscending] = React.useState(true);

  const sortedData = React.useMemo(() => {
    if (!sortKey) return data;
    return [...data].sort((a, b) => {
      const va = (a as any)[sortKey];
      const vb = (b as any)[sortKey];
      if (va === vb) return 0;
      if (va == null) return 1;
      if (vb == null) return -1;
      if (va < vb) return ascending ? -1 : 1;
      return ascending ? 1 : -1;
    });
  }, [data, sortKey, ascending]);

  const handleHeaderClick = (col: Column<T>) => {
    if (typeof col.accessor === 'string') {
      if (sortKey === col.accessor) {
        setAscending(!ascending);
      } else {
        setSortKey(col.accessor as keyof T);
        setAscending(true);
      }
    }
  };

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {columns.map((col, idx) => (
              <th
                key={idx}
                onClick={() => handleHeaderClick(col)}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer select-none"
              >
                {col.header}
                {typeof col.accessor === 'string' && sortKey === col.accessor && (
                  <span className="ml-1">
                    {ascending ? '▲' : '▼'}
                  </span>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {sortedData.map((row, i) => (
            <tr key={i} className={i % 2 === 0 ? '' : 'bg-gray-50'}>
              {columns.map((col, j) => {
                const value =
                  typeof col.accessor === 'function'
                    ? col.accessor(row)
                    : (row as any)[col.accessor];
                return (
                  <td key={j} className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                    {value}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default DataTable;
