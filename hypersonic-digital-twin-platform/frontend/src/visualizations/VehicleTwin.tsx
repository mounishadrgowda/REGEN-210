import type { CSSProperties } from "react";
import type { DigitalTwinState } from "../state/types";

export function VehicleTwin({ state }: { state?: DigitalTwinState }) {
  const temp = state?.thermal.max_surface_temp_k ?? 980;
  const glow = Math.min(1, Math.max(0, (temp - 700) / 1800));

  return (
    <section className="vehicle-stage">
      <div className="shockwave" style={{ opacity: 0.25 + glow * 0.55 }} />
      <div className="vehicle-shell" style={{ "--heat": glow } as CSSProperties}>
        <div className="nose" />
        <div className="body" />
        <div className="fin fin-a" />
        <div className="fin fin-b" />
      </div>
      <div className="cooling-lines">
        <span />
        <span />
        <span />
      </div>
    </section>
  );
}
