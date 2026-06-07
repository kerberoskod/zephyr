import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getReviews, Review } from '../api/client';
import StatCard from '../components/ui/StatCard';
import Badge from '../components/ui/Badge';

const statusIcon: Record<string, string> = {
  pending: '⏳',
  processing: '🔄',
  completed: '✅',
  failed: '❌',
};

const severityOrder = ['critical', 'major', 'minor'];

function severityIcon(s: string) {
  switch (s) {
    case 'critical': return '🔴';
    case 'major': return '🟡';
    case 'minor': return '🔵';
    default: return '⚪';
  }
}

function formatDate(d: string | null) {
  if (!d) return '-';
  return new Date(d).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

export default function Dashboard() {
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<Review | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['reviews', page],
    queryFn: () => getReviews(page, 20),
    refetchInterval: 10000,
  });

  const reviews = data?.reviews || [];
  const total = data?.total || 0;

  const totalCritical = reviews.filter(
    (r) => r.findings?.some((f) => f.severity === 'critical')
  ).length;
  const totalCompleted = reviews.filter((r) => r.status === 'completed').length;

  return (
    <div className="min-h-screen bg-zephyr-night">
      <header className="border-b border-zephyr-border bg-zephyr-dark/50">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center gap-3">
          <span className="text-2xl">🌪️</span>
          <div>
            <h1 className="text-lg font-bold text-zephyr-light">Zephyr</h1>
            <p className="text-xs text-zephyr-gray">Code Review</p>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          <StatCard label="Total Reviews" value={total} icon="📋" />
          <StatCard label="Completed" value={totalCompleted} icon="✅" />
          <StatCard label="Critical Issues" value={totalCritical} icon="🔴" />
        </div>

        <div className="bg-zephyr-dark border border-zephyr-border rounded-xl overflow-hidden">
          <div className="p-4 border-b border-zephyr-border">
            <h2 className="text-sm font-semibold text-zephyr-light">Review History</h2>
          </div>

          {isLoading ? (
            <div className="p-8 text-center text-zephyr-gray text-sm">Loading...</div>
          ) : reviews.length === 0 ? (
            <div className="p-8 text-center text-zephyr-gray text-sm">
              No reviews yet. Install the GitHub App and open a PR to get started.
            </div>
          ) : (
            <div className="divide-y divide-zephyr-border">
              {reviews.map((review) => (
                <button
                  key={review.id}
                  onClick={() => setSelected(selected?.id === review.id ? null : review)}
                  className="w-full text-left px-4 py-3 hover:bg-zephyr-mid/50 transition-colors"
                >
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2 min-w-0">
                      <span>{statusIcon[review.status] || '⏳'}</span>
                      <span className="text-sm font-medium text-zephyr-light truncate">
                        {review.repo_full_name}
                      </span>
                      <span className="text-xs text-zephyr-gray">#{review.pr_number}</span>
                    </div>
                    <Badge variant={review.status as any}>{review.status}</Badge>
                  </div>
                  {review.pr_title && (
                    <p className="text-xs text-zephyr-gray truncate pl-7">{review.pr_title}</p>
                  )}
                  <div className="flex items-center gap-3 mt-1 pl-7">
                    <span className="text-xs text-zephyr-gray">{formatDate(review.created_at)}</span>
                    {review.total_comments > 0 && (
                      <span className="text-xs text-zephyr-gray">
                        {review.total_comments} finding{review.total_comments !== 1 ? 's' : ''}
                      </span>
                    )}
                  </div>

                  {selected?.id === review.id && review.findings && (
                    <div className="mt-3 pl-7 border-t border-zephyr-border pt-3 space-y-2">
                      {review.diff_summary && (
                        <p className="text-xs text-zephyr-gray mb-2">{review.diff_summary}</p>
                      )}
                      {[...review.findings]
                        .sort((a, b) => severityOrder.indexOf(a.severity) - severityOrder.indexOf(b.severity))
                        .slice(0, 20)
                        .map((f, i) => (
                          <div key={i} className="bg-zephyr-night/50 rounded-lg p-3 text-xs">
                            <div className="flex items-center gap-2 mb-1">
                              <span>{severityIcon(f.severity)}</span>
                              <Badge variant={f.severity as any}>{f.severity}</Badge>
                              <span className="text-zephyr-gray">{f.category}</span>
                              <span className="text-zephyr-gray ml-auto font-mono">
                                {f.file}:{f.line}
                              </span>
                            </div>
                            <p className="text-zephyr-light mb-1">{f.message}</p>
                            {f.suggestion && (
                              <p className="text-zephyr-accent-light">💡 {f.suggestion}</p>
                            )}
                          </div>
                        ))}
                    </div>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
