interface StatCardProps {
  label: string;
  value: string | number;
  icon: string;
}

export default function StatCard({ label, value, icon }: StatCardProps) {
  return (
    <div className="bg-zephyr-dark border border-zephyr-border rounded-xl p-4">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-lg">{icon}</span>
        <span className="text-xs text-zephyr-gray uppercase tracking-wider">{label}</span>
      </div>
      <p className="text-2xl font-bold text-zephyr-light">{value}</p>
    </div>
  );
}
