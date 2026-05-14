from app.schemas.digital_twin import Alert, DigitalTwinState


class StructuralRiskModule:
    name = "structural_risk"

    def update(self, state: DigitalTwinState, dt_s: float) -> DigitalTwinState:
        thermal_risk = 1.0 - max(0.0, min(1.0, state.thermal.thermal_margin))
        pressure_risk = min(1.0, state.aerodynamic.dynamic_pressure_pa / 120_000.0)
        duration_risk = min(1.0, state.time_s / max(1, state.tps.thickness_mm * 8))
        risk_score = 0.58 * thermal_risk + 0.27 * pressure_risk + 0.15 * duration_risk

        state.alerts = []
        state.risk.score = round(risk_score, 3)
        state.risk.failure_warning = state.thermal.thermal_margin < 0.08

        if risk_score > 0.72 or state.risk.failure_warning:
            state.risk.level = "critical"
            state.risk.recommended_action = "Reduce Mach or increase coolant mass flow immediately"
            state.alerts.append(Alert(severity="critical", code="TPS_MARGIN_LOW", message="TPS thermal margin is below safe demo threshold"))
        elif risk_score > 0.42:
            state.risk.level = "guarded"
            state.risk.recommended_action = "Monitor leading-edge heating and raise cooling flow"
            state.alerts.append(Alert(severity="guarded", code="THERMAL_LOAD_RISING", message="Thermal load is trending upward"))
        else:
            state.risk.level = "nominal"
            state.risk.recommended_action = "Maintain current TPS profile"

        return state

