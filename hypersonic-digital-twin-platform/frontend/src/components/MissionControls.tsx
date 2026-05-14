import { Pause, Play, RotateCcw } from "lucide-react";
import type { SimulationStartRequest } from "../state/types";

interface MissionControlsProps {
  mission: SimulationStartRequest;
  running: boolean;
  onStart: () => void;
}

export function MissionControls({ mission, running, onStart }: MissionControlsProps) {
  return (
    <aside className="control-rail">
      <div>
        <p className="eyebrow">Mission Controls</p>
        <h2>{mission.vehicle.name}</h2>
      </div>

      <label>
        Mach
        <input type="range" min="4" max="10" step="0.1" value={mission.initial_conditions.mach} readOnly />
      </label>
      <label>
        Altitude
        <input type="range" min="18000" max="45000" step="500" value={mission.initial_conditions.altitude_m} readOnly />
      </label>
      <label>
        Coolant Flow
        <input type="range" min="0" max="2" step="0.1" value={mission.cooling.mass_flow_kg_s} readOnly />
      </label>

      <button className="primary-action" onClick={onStart}>
        {running ? <Pause size={18} /> : <Play size={18} />}
        {running ? "Streaming Mission" : "Run Digital Twin Mission"}
      </button>
      <button className="secondary-action">
        <RotateCcw size={18} />
        Reset Scenario
      </button>
    </aside>
  );
}

