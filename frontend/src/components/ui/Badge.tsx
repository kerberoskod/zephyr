interface BadgeProps {
  variant: 'critical' | 'major' | 'minor' | 'pending' | 'processing' | 'completed' | 'failed';
  children: React.ReactNode;
}

const styles: Record<string, string> = {
  critical: 'bg-red-900/50 text-red-300 border-red-700',
  major: 'bg-yellow-900/50 text-yellow-300 border-yellow-700',
  minor: 'bg-blue-900/50 text-blue-300 border-blue-700',
  pending: 'bg-gray-800 text-gray-400 border-gray-600',
  processing: 'bg-zephyr-accent/20 text-zephyr-accent-light border-zephyr-accent',
  completed: 'bg-green-900/50 text-green-300 border-green-700',
  failed: 'bg-red-900/50 text-red-300 border-red-700',
};

export default function Badge({ variant, children }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 text-xs font-medium rounded border ${styles[variant] || styles.pending}`}
    >
      {children}
    </span>
  );
}
