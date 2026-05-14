import { BrainCircuit, ShieldAlert } from "lucide-react";
import type { DigitalTwinState } from "../state/types";

export function IntelligenceRail({ state }: { state?: DigitalTwinState }) {
  const recommendations = state?.ai.material_recommendation ?? ["reinforced_carbon_carbon", "c_phenolic", "bio_ceramic_composite"];

  return (
    <aside className="intelligence-rail">
      <div>
        <p className="eyebrow">AI Systems</p>
        <h2>Predictive TPS Core</h2>
      </div>
      <section className="intel-panel">
        <BrainCircuit size={20} />
        <span>Model Stage</span>
        <strong>{state?.ai.model_stage ?? "demo-surrogate"}</strong>
      </section>
      <section className="intel-panel">
        <ShieldAlert size={20} />
        <span>Failure Probability</span>
        <strong>{Math.round((state?.ai.failure_probability ?? 0.18) * 100)}%</strong>
      </section>
      <section className="recommendations">
        <span>Material Ranking</span>
        {recommendations.map((item) => (
          <b key={item}>{item.replaceAll("_", " ")}</b>
        ))}
      </section>
      <section className={`alert-stack ${state?.risk.level ?? "nominal"}`}>
        <span>{state?.risk.level.toUpperCase() ?? "NOMINAL"}</span>
        <p>{state?.risk.recommended_action ?? "Maintain current TPS profile"}</p>
      </section>
    </aside>
  );
}

