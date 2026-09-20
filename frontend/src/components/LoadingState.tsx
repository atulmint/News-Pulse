'use client';

export default function LoadingState() {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6 shadow-sm space-y-6">
      <div className="flex justify-between items-center">
        <div className="space-y-2">
          <div className="h-6 w-48 bg-gray-200 dark:bg-gray-800 rounded animate-pulse" />
          <div className="h-4 w-72 bg-gray-100 dark:bg-gray-800/60 rounded animate-pulse" />
        </div>
        <div className="h-8 w-24 bg-gray-200 dark:bg-gray-800 rounded-full animate-pulse" />
      </div>

      {/* Axis Skeleton */}
      <div className="h-6 w-full bg-gray-100 dark:bg-gray-800/40 rounded animate-pulse" />

      {/* Track Skeletons */}
      <div className="space-y-4 py-4">
        {[
          { left: '5%', width: '35%' },
          { left: '45%', width: '40%' },
          { left: '20%', width: '50%' },
          { left: '10%', width: '30%' },
        ].map((item, idx) => (
          <div key={idx} className="h-16 relative w-full bg-gray-50 dark:bg-gray-950/30 rounded-xl overflow-hidden">
            <div
              style={{ left: item.left, width: item.width }}
              className="absolute top-0 bottom-0 bg-gray-200 dark:bg-gray-800 rounded-xl animate-pulse"
            />
          </div>
        ))}
      </div>

      {/* Axis Skeleton */}
      <div className="h-6 w-full bg-gray-100 dark:bg-gray-800/40 rounded animate-pulse" />
    </div>
  );
}
