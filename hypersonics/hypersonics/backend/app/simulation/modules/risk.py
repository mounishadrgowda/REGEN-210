from app.schemas.digital_twin import Alert, DigitalTwinState


class StructuralRiskModule:
    name = "structural_risk"

    def update(self, state: DigitalTwinState, dt_s: float) -> DigitalTwinState:
        thermal_risk = 1.0 - max(0.0, min(1.0, state.thermal.thermal_margin))
        pressure_risk = min(1.0, state.aerodynamic.dynamic_pressure_pa / 120_000.0)
        duration_risk = min(1.0, state.time_s / max(1, state.tps.thickness_mm * 8))
        stress_risk = min(1.0, state.structural.joint_stress_mpa / 700.0)
        fatigue_risk = min(1.0, state.structural.fatigue_damage * 4.0)
        risk_score = 0.44 * thermal_risk + 0.2 * pressure_risk + 0.12 * duration_risk + 0.16 * stress_risk + 0.08 * fatigue_risk

        state.alerts = []
        state.risk.score = round(risk_score, 3)
        state.risk.failure_warning = state.thermal.thermal_margin < 0.08 or state.structural.failure_probability > 0.72

        if risk_score > 0.72 or state.risk.failure_warning:
            state.risk.level = "critical"
            state.risk.recommended_action = f"Hold Mach below {state.aircraft.target_mach:.1f}, increase leading-edge cooling, and inspect {state.structural.limiting_location}"
            state.alerts.append(Alert(severity="critical", code="TPS_MARGIN_LOW", message="TPS or structural margin is below safe demo threshold"))
        elif risk_score > 0.42:
            state.risk.level = "guarded"
            state.risk.recommended_action = f"Monitor {state.structural.limiting_location} and raise zonal cooling flow"
            state.alerts.append(Alert(severity="guarded", code="THERMAL_LOAD_RISING", message="Thermal load is trending upward"))
        else:
            state.risk.level = "nominal"
            state.risk.recommended_action = "Maintain current TPS profile"

        return state
