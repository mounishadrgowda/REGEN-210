from app.schemas.digital_twin import DigitalTwinState
from app.simulation.materials import get_material


class SustainabilityModule:
    name = "sustainability"

    def update(self, state: DigitalTwinState, dt_s: float) -> DigitalTwinState:
        material = get_material(state.tps.material_id)
        coolant_penalty = 0.04 if state.cooling.coolant == "liquid_hydrogen" else 0.12
        cooling_power_penalty = min(0.25, state.cooling.mass_flow_kg_s * 0.05)
        risk_penalty = state.risk.score * 0.22
        score = material["sustainability"] - coolant_penalty - cooling_power_penalty - risk_penalty + 0.18

        state.sustainability.score = round(max(0.0, min(1.0, score)), 3)
        state.sustainability.material_reuse_potential = material["sustainability"]
        state.sustainability.coolant_penalty = coolant_penalty + cooling_power_penalty
        return state

