import type { CSSProperties } from "react";
import { Pause, Play, RotateCcw } from "lucide-react";
import type { DigitalTwinState, SimulationStartRequest } from "../state/types";

type NumericVehicleField = "nose_radius_m" | "reference_area_m2" | "drag_coefficient";

interface MissionControlsProps {
  mission: SimulationStartRequest;
  running: boolean;
  state?: DigitalTwinState;
  onStart: () => void;
  onMissionChange: (mission: SimulationStartRequest) => void;
  onReset: () => void;
}

interface FlightGaugeProps {
  accent: string;
  label: string;
  max: number;
  min: number;
  rangeLabel: string;
  screenLabel: string;
  step: number;
  unit: string;
  value: number;
  valueLabel: string;
  onChange: (value: number) => void;
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function FlightGauge({ accent, label, max, min, rangeLabel, screenLabel, step, unit, value, valueLabel, onChange }: FlightGaugeProps) {
  const progress = clamp((value - min) / (max - min), 0, 1);
  const dialStyle = {
    "--accent": accent,
    "--dial": `${Math.round(progress * 100)}%`,
    "--needle": `${-128 + progress * 256}deg`,
  } as CSSProperties;

  return (
    <section className="flight-card" style={dialStyle}>
      <div className="dial" aria-hidden="true">
        <span className="needle" />
        <span className="pin" />
      </div>

      <div className="readout">
        <span>{screenLabel}</span>
        <strong>
          {valueLabel}
          <small>{unit}</small>
        </strong>
        <div className="readout-range">
          <b>REC: {Math.round((min + max) / 2)}</b>
          <b>MIN: {min}</b>
          <b>MAX: {max}</b>
        </div>
      </div>

      <label className="instrument-control">
        <span>{rangeLabel}</span>
        <input type="range" min={min} max={max} step={step} value={value} onChange={(event) => onChange(event.currentTarget.valueAsNumber)} />
      </label>
      <p>{label}</p>
    </section>
  );
}

export function MissionControls({ mission, running, state, onStart, onMissionChange, onReset }: MissionControlsProps) {
  const mach = mission.initial_conditions.mach;
  const altitudeKm = mission.initial_conditions.altitude_m / 1000;
  const velocityMps = state?.aircraft.velocity_m_s ?? mach * 295;

  function updateInitialCondition(field: keyof SimulationStartRequest["initial_conditions"], value: number) {
    onMissionChange({
      ...mission,
      initial_conditions: {
        ...mission.initial_conditions,
        [field]: value,
      },
    });
  }

  function updateVehicle(field: NumericVehicleField, value: number) {
    onMissionChange({
      ...mission,
      vehicle: {
        ...mission.vehicle,
        [field]: value,
      },
    });
  }

  function updateCoolingMassFlow(value: number) {
    onMissionChange({
      ...mission,
      cooling: {
        ...mission.cooling,
        mass_flow_kg_s: value,
      },
    });
  }

  function updateMagneticField(value: number) {
    onMissionChange({
      ...mission,
      plasma_control: {
        ...mission.plasma_control,
        magnetic_field_t: value,
      },
    });
  }

  return (
    <aside className="control-rail">
      <div className="section-title">
        <span />
        <div>
          <p>Flight Parameters</p>
          <h2>{mission.vehicle.name}</h2>
        </div>
      </div>

      <FlightGauge
        accent="#25b9d7"
        label="Altitude"
        max={45}
        min={18}
        rangeLabel="Altitude"
        screenLabel="ALTITUDE"
        step={0.5}
        unit="km"
        value={altitudeKm}
        valueLabel={altitudeKm.toFixed(1)}
        onChange={(value) => updateInitialCondition("altitude_m", value * 1000)}
      />

      <FlightGauge
        accent="#ff9f0a"
        label="Velocity"
        max={8.8}
        min={4}
        rangeLabel="Mach / Velocity"
        screenLabel="VELOCITY"
        step={0.1}
        unit="m/s"
        value={mach}
        valueLabel={Math.round(velocityMps).toLocaleString()}
        onChange={(value) => updateInitialCondition("mach", value)}
      />

      <FlightGauge
        accent="#b75cff"
        label="Nose Radius R-"
        max={1}
        min={0.1}
        rangeLabel="Nose Radius"
        screenLabel="NOSE RAD"
        step={0.01}
        unit="m"
        value={mission.vehicle.nose_radius_m}
        valueLabel={mission.vehicle.nose_radius_m.toFixed(2)}
        onChange={(value) => updateVehicle("nose_radius_m", value)}
      />

      <FlightGauge
        accent="#16e785"
        label="Drag Coeff CD"
        max={1.2}
        min={0.1}
        rangeLabel="Drag Coeff CD"
        screenLabel="DRAG COE"
        step={0.01}
        unit=""
        value={mission.vehicle.drag_coefficient}
        valueLabel={mission.vehicle.drag_coefficient.toFixed(2)}
        onChange={(value) => updateVehicle("drag_coefficient", value)}
      />

      <FlightGauge
        accent="#ff4d98"
        label="Ref Area"
        max={40}
        min={5}
        rangeLabel="Ref Area"
        screenLabel="REF AREA"
        step={0.5}
        unit="m2"
        value={mission.vehicle.reference_area_m2}
        valueLabel={mission.vehicle.reference_area_m2.toFixed(1)}
        onChange={(value) => updateVehicle("reference_area_m2", value)}
      />

      <label className="coolant-control">
        <span>Regen Cooling Flow {mission.cooling.mass_flow_kg_s.toFixed(1)} kg/s</span>
        <input
          type="range"
          min="0"
          max="2"
          step="0.1"
          value={mission.cooling.mass_flow_kg_s}
          onChange={(event) => updateCoolingMassFlow(event.currentTarget.valueAsNumber)}
        />
      </label>

      <label className="coolant-control magnetic-control">
        <span>Magnetic Field {mission.plasma_control.magnetic_field_t.toFixed(1)} T</span>
        <input
          type="range"
          min="0"
          max="5"
          step="0.1"
          value={mission.plasma_control.magnetic_field_t}
          onChange={(event) => updateMagneticField(event.currentTarget.valueAsNumber)}
        />
      </label>

      <div className="control-actions">
        <button className="primary-action" onClick={onStart}>
          {running ? <Pause size={18} /> : <Play size={18} />}
          {running ? "Streaming REGEN-TWIN" : "Run REGEN-TWIN Mission"}
        </button>
        <button className="secondary-action" onClick={onReset}>
          <RotateCcw size={18} />
          Reset Scenario
        </button>
      </div>
    </aside>
  );
}
