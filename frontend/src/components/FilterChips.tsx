import React from 'react';

interface Chip {
  label: string;
  active: boolean;
  onClick: () => void;
}

const FilterChips: React.FC<{chips: Chip[]}> = ({ chips }) => (
  <div className="flex flex-wrap gap-2 mb-4">
    {chips.map((c, i) => (
      <button
        key={i}
        onClick={c.onClick}
        className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
          c.active
            ? 'bg-accent text-white'
            : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
        }`}
      >
        {c.label}
      </button>
    ))}
  </div>
);

export default FilterChips;
