import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { DigitalTwinState, SimulationStartRequest } from "../state/types";

interface TelemetryChartProps {
  history: DigitalTwinState[];
  mission: SimulationStartRequest;
}

interface PlotProps {
  color: string;
  data: TelemetryPoint[];
  domain?: [number, number] | ["auto", "auto"];
  label: string;
  series: keyof TelemetryPoint;
}

interface TelemetryPoint {
  drag: number;
  fuel: number;
  heat: number;
  temp: number;
  time: string;
}

function densityAtAltitude(altitudeM: number) {
  return 1.225 * Math.exp(-altitudeM / 8500);
}

function seedPoint(mission: SimulationStartRequest): TelemetryPoint {
  const velocity = mission.initial_conditions.mach * 295;
  const density = densityAtAltitude(mission.initial_conditions.altitude_m);
  const dynamicPressure = 0.5 * density * velocity ** 2;
  const dragN = dynamicPressure * mission.vehicle.reference_area_m2 * mission.vehicle.drag_coefficient;
  return {
    drag: Number((dragN / 1000).toFixed(2)),
    fuel: Number(((dragN * velocity) / (43_000_000 * 0.4)).toFixed(3)),
    heat: 1.05,
    temp: 300,
    time: "0.0",
  };
}

function MiniPlot({ color, data, domain = ["auto", "auto"], label, series }: PlotProps) {
  return (
    <section className="plot-panel">
      <span>{label}</span>
      <ResponsiveContainer width="100%" height={102}>
        <LineChart data={data}>
          <XAxis dataKey="time" hide />
          <YAxis domain={domain} hide />
          <Tooltip contentStyle={{ background: "#fffdf7", border: "1px solid #d7d1c6", color: "#2b2b28" }} />
          <Line type="monotone" dataKey={series} dot={false} stroke={color} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </section>
  );
}

export function TelemetryChart({ history, mission }: TelemetryChartProps) {
  const data =
    history.length > 0
      ? history.slice(-60).map((item) => {
          const dragN = item.aerodynamic.dynamic_pressure_pa * mission.vehicle.reference_area_m2 * mission.vehicle.drag_coefficient;
          const fuelFlowKgS = Math.max(0, (dragN * item.aircraft.velocity_m_s) / (43_000_000 * 0.4));
          return {
            drag: Number((dragN / 1000).toFixed(2)),
            fuel: Number(fuelFlowKgS.toFixed(3)),
            heat: Number((item.thermal.heat_flux_w_m2 / 1_000_000).toFixed(3)),
            temp: Math.round(item.thermal.max_surface_temp_k),
            time: item.time_s.toFixed(1),
          };
        })
      : [seedPoint(mission)];

  return (
    <section className="telemetry-deck">
      <MiniPlot color="#e05d6f" data={data} domain={[190, 220]} label="Surface Temperature [K]" series="temp" />
      <MiniPlot color="#e7922c" data={data} domain={[0.8, 1.25]} label="Heat Flux [MW/m2]" series="heat" />
      <MiniPlot color="#58bde2" data={data} label="Drag Force [kN]" series="drag" />
      <MiniPlot color="#29d583" data={data} label="Fuel Flow [kg/s]" series="fuel" />
    </section>
  );
}
