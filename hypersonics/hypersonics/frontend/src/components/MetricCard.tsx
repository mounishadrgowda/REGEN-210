interface MetricCardProps {
  label: string;
  value: string;
  tone?: "nominal" | "guarded" | "critical";
}

export function MetricCard({ label, value, tone = "nominal" }: MetricCardProps) {
  return (
    <section className={`metric metric-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </section>
  );
}

