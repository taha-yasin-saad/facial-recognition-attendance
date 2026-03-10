import React from 'react';

interface Props {
  name: string;
  size?: number;
}

const AvatarPlaceholder: React.FC<Props> = ({ name, size = 40 }) => {
  const initials = name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase();
  return (
    <div
      style={{ width: size, height: size }}
      className="rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center text-gray-700 dark:text-gray-200 font-semibold"
    >
      {initials}
    </div>
  );
};

export default AvatarPlaceholder;
