/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: 'class',
    content: [
        './index.html',
        './src/**/*.{js,ts,jsx,tsx}',
    ],
    theme: {
        extend: {
            colors: {
                accent: '#4F46E5',
                success: '#10B981',
                error: '#EF4444',
            },
            backdropBlur: {
                xs: '2px',
            },
        },
    },
    plugins: [],
};