import React from 'react';

export const SIMULATION_CHUNK_SIZE = 1024 * 1024; // 1 MB
export const SIMULATION_INTERVAL = 50; // ms

// FIX: Replaced JSX with React.createElement to be compatible with .ts files.
export const FileIcon = () => (
    React.createElement('svg', {
        xmlns: "http://www.w3.org/2000/svg",
        className: "h-6 w-6 flex-shrink-0 text-gray-400",
        fill: "none",
        viewBox: "0 0 24 24",
        stroke: "currentColor"
    }, React.createElement('path', {
        strokeLineCap: "round",
        strokeLineJoin: "round",
        strokeWidth: 2,
        d: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2-2z"
    }))
);

// FIX: Replaced JSX with React.createElement to be compatible with .ts files.
export const HomeIcon = () => (
    React.createElement('svg', {
        xmlns: "http://www.w3.org/2000/svg",
        className: "h-5 w-5",
        fill: "none",
        viewBox: "0 0 24 24",
        stroke: "currentColor"
    }, React.createElement('path', {
        strokeLineCap: "round",
        strokeLineJoin: "round",
        strokeWidth: 2,
        d: "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
    }))
);

// FIX: Replaced JSX with React.createElement to be compatible with .ts files.
export const UploadIcon = () => (
    React.createElement('svg', {
        xmlns: "http://www.w3.org/2000/svg",
        className: "h-6 w-6",
        fill: "none",
        viewBox: "0 0 24 24",
        stroke: "currentColor"
    }, React.createElement('path', {
        strokeLineCap: "round",
        strokeLineJoin: "round",
        strokeWidth: 2,
        d: "M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
    }))
);

// FIX: Replaced JSX with React.createElement to be compatible with .ts files.
export const DownloadIcon = () => (
     React.createElement('svg', {
        xmlns: "http://www.w3.org/2000/svg",
        className: "h-6 w-6",
        fill: "none",
        viewBox: "0 0 24 24",
        stroke: "currentColor"
    }, React.createElement('path', {
        strokeLineCap: "round",
        strokeLineJoin: "round",
        strokeWidth: 2,
        d: "M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
    }))
);

// FIX: Replaced JSX with React.createElement to be compatible with .ts files.
export const InfoIcon = () => (
    React.createElement('svg', {
        xmlns: "http://www.w3.org/2000/svg",
        className: "h-5 w-5 text-blue-400 flex-shrink-0",
        fill: "none",
        viewBox: "0 0 24 24",
        stroke: "currentColor"
    }, React.createElement('path', {
        strokeLineCap: "round",
        strokeLineJoin: "round",
        strokeWidth: "2",
        d: "M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
    }))
);

// FIX: Replaced JSX with React.createElement to be compatible with .ts files.
export const SuccessIcon = () => (
    React.createElement('svg', {
        xmlns: "http://www.w3.org/2000/svg",
        className: "h-5 w-5 text-green-400 flex-shrink-0",
        fill: "none",
        viewBox: "0 0 24 24",
        stroke: "currentColor"
    }, React.createElement('path', {
        strokeLineCap: "round",
        strokeLineJoin: "round",
        strokeWidth: "2",
        d: "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
    }))
);

// FIX: Replaced JSX with React.createElement to be compatible with .ts files.
export const ErrorIcon = () => (
    React.createElement('svg', {
        xmlns: "http://www.w3.org/2000/svg",
        className: "h-5 w-5 text-red-400 flex-shrink-0",
        fill: "none",
        viewBox: "0 0 24 24",
        stroke: "currentColor"
    }, React.createElement('path', {
        strokeLineCap: "round",
        strokeLineJoin: "round",
        strokeWidth: "2",
        d: "M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
    }))
);
