import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { DigitalTwinState } from "../state/types";

interface TelemetryChartProps {
  history: DigitalTwinState[];
}

export function TelemetryChart({ history }: TelemetryChartProps) {
  const data = history.slice(-40).map((item) => ({
    time: item.time_s.toFixed(1),
    temp: Math.round(item.thermal.max_surface_temp_k),
    risk: Math.round(item.risk.score * 100),
  }));

  return (
    <section className="telemetry-deck">
      <ResponsiveContainer width="100%" height={190}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="temp" x1="0" x2="0" y1="0" y2="1">
              <stop offset="5%" stopColor="#ffb000" stopOpacity={0.7} />
              <stop offset="95%" stopColor="#ff4d4d" stopOpacity={0.05} />
            </linearGradient>
          </defs>
          <XAxis dataKey="time" stroke="#74849a" />
          <YAxis stroke="#74849a" />
          <Tooltip contentStyle={{ background: "#101820", border: "1px solid #2b3c4e" }} />
          <Area type="monotone" dataKey="temp" stroke="#ffb000" fill="url(#temp)" />
          <Area type="monotone" dataKey="risk" stroke="#5eead4" fill="transparent" />
        </AreaChart>
      </ResponsiveContainer>
    </section>
  );
}

