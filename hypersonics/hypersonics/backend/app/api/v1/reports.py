from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from fastapi import APIRouter, HTTPException

from app.schemas.digital_twin import DigitalTwinState
from app.services.simulation_service import simulation_service

router = APIRouter()


def _round(value: float, digits: int = 2) -> float:
    return round(float(value), digits)


def _percent(value: float) -> float:
    return _round(max(0.0, min(1.0, value)) * 100.0, 1)


def _mw_m2(value: float) -> float:
    return _round(value / 1_000_000.0, 3)


def _kw_m2(value: float) -> float:
    return _round(value / 1_000.0, 2)


def _stats(values: list[float]) -> dict[str, float]:
    if not values:
        return {"min": 0, "max": 0, "avg": 0}
    return {"min": _round(min(values), 2), "max": _round(max(values), 2), "avg": _round(mean(values), 2)}


def _heatmap_stats(grid: list[list[float]]) -> dict[str, float | str]:
    values = [value for row in grid for value in row]
    if not values:
        return {"min_k": 0, "max_k": 0, "avg_k": 0, "hotspot": "not available"}

    max_value = max(values)
    hotspot = "nose / leading edge"
    for y, row in enumerate(grid):
        for x, value in enumerate(row):
            if value == max_value:
                if x > len(row) * 0.62:
                    hotspot = "scramjet / aft-body"
                elif y in {0, len(grid) - 1}:
                    hotspot = "outer leading edge"
                break

    return {
        "min_k": _round(min(values), 1),
        "max_k": _round(max_value, 1),
        "avg_k": _round(mean(values), 1),
        "hotspot": hotspot,
    }


def _assessment(state: DigitalTwinState, min_margin: float) -> str:
    if state.risk.level == "critical":
        return "Critical TPS condition: reduce Mach, increase coolant flow, or abort the current profile."
    if state.risk.level == "guarded":
        return "Guarded TPS condition: continue monitoring leading-edge heat and prepare extra cooling margin."
    if min_margin < 0.2:
        return "Nominal risk with narrowing thermal margin: keep the profile under active review."
    return "Mission profile is nominal within the current demo surrogate model."


def _recommendations(state: DigitalTwinState, min_margin: float, avg_cooling_efficiency: float, peak_dynamic_pressure: float) -> list[str]:
    items = [state.risk.recommended_action]

    if min_margin < 0.15:
        items.append("Increase TPS thickness or switch to a higher temperature material for the next run.")
    elif min_margin < 0.3:
        items.append("Keep a 10-15% TPS thickness reserve before extending mission duration.")

    if state.cooling.enabled and avg_cooling_efficiency < 0.25:
        items.append("Raise coolant mass flow or choose a higher heat-capacity coolant.")
    elif not state.cooling.enabled:
        items.append("Enable regenerative cooling before high-Mach thermal envelope expansion.")

    if peak_dynamic_pressure > 90_000:
        items.append("Lower angle of attack or climb earlier to reduce peak dynamic pressure.")

    for material in state.ai.material_recommendation[:3]:
        items.append(f"Evaluate {material.replace('_', ' ')} in the TPS material trade study.")

    deduped: list[str] = []
    for item in items:
        if item not in deduped:
            deduped.append(item)
    return deduped


def _build_markdown(report: dict[str, Any]) -> str:
    mission = report["mission"]
    thermal = report["thermal"]
    aero = report["aerodynamic"]
    cooling = report["cooling"]
    zonal = report["zonal_cooling"]
    plasma = report["plasma_shielding"]
    rpic = report["rpic"]
    structural = report["structural"]
    intelligence = report["intelligence"]
    risk = report["risk"]
    data_products = report["data_products"]

    alert_lines = report["alerts"] or [{"severity": "nominal", "code": "NO_ALERTS", "message": "No active alerts"}]
    recommendations = "\n".join(f"- {item}" for item in report["recommendations"])
    alerts = "\n".join(f"- {item['severity'].upper()} `{item['code']}`: {item['message']}" for item in alert_lines)
    judge_highlights = "\n".join(f"- {item}" for item in report["judge_highlights"])
    model_notes = "\n".join(f"- {item}" for item in intelligence["surrogate_notes"]) or "- No surrogate notes recorded."
    zone_rows = "\n".join(
        f"| {zone['name']} | {zone['surface_temp_k']} K | {zone['thermal_margin_pct']}% | {zone['efficiency_pct']}% | {zone['status']} |"
        for zone in zonal["zones"]
    ) or "| No active zones | - | - | - | - |"
    material_rows = "\n".join(f"| {idx + 1} | {item} |" for idx, item in enumerate(intelligence["material_recommendation"])) or "| - | No recommendation |"
    forecast = ", ".join(f"{value} K" for value in intelligence["heat_forecast_k"]) or "not available"

    return f"""# REGEN-TWIN Mission Report

Generated: `{report["generated_at"]}`
Report ID: `{report["report_id"]}`

## Executive Summary

- Mission generated: `yes`
- Mission ID: `{mission["mission_id"]}`
- Simulation ID: `{mission["simulation_id"]}`
- Vehicle: `{mission["vehicle_name"]}`
- Risk level: `{report["executive_summary"]["risk_level"]}`
- Assessment: {report["executive_summary"]["assessment"]}
- Recommended action: {report["executive_summary"]["recommended_action"]}
- Judge scorecard: `{report["scorecard"]["overall"]}/100`

## Judge Highlights

{judge_highlights}

## Mission Profile

- Initial Mach: `{mission["initial_mach"]}`
- Final Mach: `{mission["final_mach"]}`
- Target Mach cap: `{mission["target_mach"]}`
- Flight phase: `{mission["flight_phase"]}`
- Initial altitude: `{mission["initial_altitude_m"]} m`
- Final altitude: `{mission["final_altitude_m"]} m`
- Cruise altitude target: `{mission["cruise_altitude_m"]} m`
- Final velocity: `{mission["final_velocity_m_s"]} m/s`
- Angle of attack: `{mission["angle_of_attack_deg"]} deg`
- Planned duration: `{mission["planned_duration_s"]} s`
- Simulated duration: `{mission["covered_duration_s"]} s`
- Profile coverage: `{mission["progress_pct"]}%`
- Samples retained: `{mission["samples"]}`

## Thermal Protection

- TPS material: `{thermal["material_id"]}`
- TPS thickness: `{thermal["thickness_mm"]} mm`
- Surface area: `{thermal["surface_area_m2"]} m2`
- Peak heat flux: `{thermal["peak_heat_flux_mw_m2"]} MW/m2`
- Average heat flux: `{thermal["avg_heat_flux_mw_m2"]} MW/m2`
- Peak net heat flux after controls: `{thermal["peak_net_heat_flux_mw_m2"]} MW/m2`
- Peak surface temperature: `{thermal["peak_surface_temp_k"]} K`
- Average surface temperature: `{thermal["avg_surface_temp_k"]} K`
- Final surface temperature: `{thermal["final_surface_temp_k"]} K`
- Minimum thermal margin: `{thermal["minimum_thermal_margin"]}`
- Thermal margin reserve: `{thermal["minimum_thermal_margin_pct"]}%`
- Final thermal load: `{thermal["thermal_load_mj_m2"]} MJ/m2`
- Peak ML heatmap hotspot: `{intelligence["heatmap"]["hotspot"]}` at `{intelligence["heatmap"]["max_k"]} K`

## Aerodynamic Loads

- Peak dynamic pressure: `{aero["peak_dynamic_pressure_pa"]} Pa`
- Peak dynamic pressure: `{aero["peak_dynamic_pressure_kpa"]} kPa`
- Average dynamic pressure: `{aero["avg_dynamic_pressure_kpa"]} kPa`
- Final shock cone angle: `{aero["shock_cone_angle_deg"]} deg`
- Final stagnation temperature: `{aero["stagnation_temperature_k"]} K`

## Active Thermal Controls

- Enabled: `{cooling["enabled"]}`
- Coolant: `{cooling["coolant"]}`
- Mass flow: `{cooling["mass_flow_kg_s"]} kg/s`
- Average efficiency: `{cooling["average_efficiency_pct"]}%`
- Peak heat removed: `{cooling["peak_heat_removed_kw_m2"]} kW/m2`
- Final heat removed: `{cooling["final_heat_removed_kw_m2"]} kW/m2`
- Zonal balance quality: `{zonal["balance_quality_pct"]}%`
- Active hottest zone: `{zonal["active_zone"]}`
- Plasma shielding peak reduction: `{plasma["peak_reduction_pct"]}%`
- RPIC peak reduction: `{rpic["peak_heat_flux_reduction_pct"]}%`
- RPIC peak power draw: `{rpic["peak_power_draw_kw"]} kW`

| Zone | Surface Temp | Margin | Efficiency | Status |
| --- | ---: | ---: | ---: | --- |
{zone_rows}

## Structural Mechanics And Maintenance

- Peak thermal stress: `{structural["peak_thermal_stress_mpa"]} MPa`
- Peak joint stress: `{structural["peak_joint_stress_mpa"]} MPa`
- Final fatigue damage: `{structural["fatigue_damage_pct"]}%`
- Ablation depth: `{structural["ablation_depth_mm"]} mm`
- Estimated cycles consumed: `{structural["cycles"]}`
- Remaining useful life: `{structural["remaining_life_cycles"]} cycles`
- Limiting location: `{structural["limiting_location"]}`
- Structural failure probability: `{structural["failure_probability_pct"]}%`

## Risk And Intelligence

- Maximum risk score: `{risk["maximum_score"]}`
- Failure warning: `{risk["failure_warning"]}`
- Failure probability: `{risk["failure_probability_pct"]}%`
- Anomaly score: `{risk["anomaly_score"]}`
- Sustainability score: `{risk["sustainability_score_pct"]}%`
- ML model stage: `{intelligence["model_stage"]}`
- Model confidence: `{intelligence["model_confidence_pct"]}%`
- Temperature forecast: {forecast}
- Heatmap min/avg/max: `{intelligence["heatmap"]["min_k"]} K / {intelligence["heatmap"]["avg_k"]} K / {intelligence["heatmap"]["max_k"]} K`

### Material Recommendation Ranking

| Rank | Material |
| ---: | --- |
{material_rows}

### Surrogate Model Notes

{model_notes}

## Data Products

- Replay dataset: `{data_products["telemetry_jsonl"]}`
- Markdown report: `{data_products["report_markdown"]}`
- Heatmap grid: `{intelligence["heatmap"]["rows"]} x {intelligence["heatmap"]["cols"]}`

## Alerts

{alerts}

## Recommendations

{recommendations}

## Notes

This report uses surrogate calculations for early design exploration and judging demos. It is not a flight qualification artifact, but it now contains a traceable telemetry replay, spatial thermal map, structural fatigue estimate, and active-control performance summary.
"""


@router.post("/generate")
async def generate_report(payload: dict) -> dict:
    simulation_id = payload.get("simulation_id")
    state = simulation_service.latest(simulation_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Simulation not found")

    mission = simulation_service.mission(simulation_id)
    samples = simulation_service.history(simulation_id) or [state]
    generated_at = datetime.now(timezone.utc).isoformat()
    report_id = f"report_{state.simulation_id}"

    peak_heat_flux = max(item.thermal.heat_flux_w_m2 for item in samples)
    peak_net_heat_flux = max(item.thermal.net_heat_flux_w_m2 for item in samples)
    peak_surface_temp = max(item.thermal.max_surface_temp_k for item in samples)
    min_margin = min(item.thermal.thermal_margin for item in samples)
    peak_dynamic_pressure = max(item.aerodynamic.dynamic_pressure_pa for item in samples)
    max_risk_score = max(item.risk.score for item in samples)
    avg_cooling_efficiency = mean(item.cooling.efficiency for item in samples)
    avg_heat_flux = mean(item.thermal.heat_flux_w_m2 for item in samples)
    avg_surface_temp = mean(item.thermal.max_surface_temp_k for item in samples)
    avg_dynamic_pressure = mean(item.aerodynamic.dynamic_pressure_pa for item in samples)
    peak_heat_removed = max(item.cooling.heat_removed_w_m2 for item in samples)
    peak_thermal_stress = max(item.structural.thermal_stress_mpa for item in samples)
    peak_joint_stress = max(item.structural.joint_stress_mpa for item in samples)
    max_failure_probability = max(item.structural.failure_probability for item in samples)
    peak_plasma_reduction = max(item.plasma_shielding.reduction_factor for item in samples)
    peak_rpic_reduction = max(item.rpic.heat_flux_reduction for item in samples)
    peak_rpic_power = max(item.rpic.power_draw_kw for item in samples)
    heatmap = _heatmap_stats(state.ai.spatial_heatmap_k)
    heatmap["rows"] = len(state.ai.spatial_heatmap_k)
    heatmap["cols"] = len(state.ai.spatial_heatmap_k[0]) if state.ai.spatial_heatmap_k else 0

    planned_duration = mission.initial_conditions.duration_s if mission else max(state.time_s, 1)
    initial_conditions = mission.initial_conditions if mission else None
    progress_pct = _percent(state.time_s / max(planned_duration, 1))

    alerts_by_code = {alert.code: alert for sample in samples for alert in sample.alerts}
    recommendations = _recommendations(state, min_margin, avg_cooling_efficiency, peak_dynamic_pressure)
    reports_dir = Path(__file__).resolve().parents[4] / "reports" / "generated"
    report_path = reports_dir / f"{report_id}.md"
    dataset_path = Path(__file__).resolve().parents[4] / "datasets" / "generated" / f"{state.simulation_id}.jsonl"
    zone_rows = [
        {
            "name": zone.name.replace("_", " "),
            "surface_temp_k": _round(zone.surface_temp_k, 1),
            "thermal_margin_pct": _percent(zone.thermal_margin),
            "efficiency_pct": _percent(zone.efficiency),
            "status": zone.status,
        }
        for zone in state.zonal_cooling.zones
    ]

    control_score = min(100.0, avg_cooling_efficiency * 58.0 + peak_plasma_reduction * 120.0 + peak_rpic_reduction * 95.0 + state.zonal_cooling.balance_quality * 22.0)
    physics_score = min(100.0, 42.0 + progress_pct * 0.18 + (1.0 - min_margin) * 12.0 + len(samples) * 0.025)
    ml_score = min(100.0, 44.0 + state.ai.model_confidence * 38.0 + (1.0 - state.ai.anomaly_score) * 14.0 + (1 if state.ai.spatial_heatmap_k else 0) * 4.0)
    reliability_score = max(0.0, 100.0 - state.ai.failure_probability * 42.0 - state.structural.fatigue_damage * 130.0)
    overall_score = _round(0.28 * control_score + 0.26 * physics_score + 0.24 * ml_score + 0.22 * reliability_score, 1)

    judge_highlights = [
        f"Bounded flight envelope holds Mach at {state.aircraft.target_mach:.2f} instead of runaway acceleration.",
        f"Active thermal controls cut exposed heat through plasma shielding ({_percent(peak_plasma_reduction)}%) and RPIC ({_percent(peak_rpic_reduction)}%).",
        f"Spatial ML heatmap generated at {heatmap['rows']}x{heatmap['cols']} resolution with hotspot classification: {heatmap['hotspot']}.",
        f"Structural module estimates {state.structural.remaining_life_cycles} remaining TPS cycles with {state.structural.ablation_depth_mm:.3f} mm ablation depth.",
        f"Telemetry replay is captured to datasets/generated for real model training and scenario comparison.",
    ]

    report: dict[str, Any] = {
        "status": "generated",
        "report_id": report_id,
        "generated_at": generated_at,
        "download_filename": f"{report_id}.md",
        "executive_summary": {
            "mission_generated": True,
            "risk_level": state.risk.level,
            "assessment": _assessment(state, min_margin),
            "recommended_action": state.risk.recommended_action,
        },
        "scorecard": {
            "overall": overall_score,
            "thermal_control": _round(control_score, 1),
            "physics_depth": _round(physics_score, 1),
            "ml_readiness": _round(ml_score, 1),
            "reliability": _round(reliability_score, 1),
        },
        "judge_highlights": judge_highlights,
        "mission": {
            "mission_id": state.mission_id,
            "simulation_id": state.simulation_id,
            "vehicle_name": state.vehicle.name,
            "initial_mach": _round(initial_conditions.mach if initial_conditions else samples[0].aircraft.mach, 2),
            "final_mach": _round(state.aircraft.mach, 2),
            "target_mach": _round(state.aircraft.target_mach, 2),
            "flight_phase": state.aircraft.flight_phase,
            "initial_altitude_m": _round(initial_conditions.altitude_m if initial_conditions else samples[0].aircraft.altitude_m, 1),
            "final_altitude_m": _round(state.aircraft.altitude_m, 1),
            "cruise_altitude_m": _round(state.aircraft.cruise_altitude_m, 1),
            "final_velocity_m_s": _round(state.aircraft.velocity_m_s, 1),
            "angle_of_attack_deg": _round(state.aircraft.angle_of_attack_deg, 1),
            "planned_duration_s": planned_duration,
            "covered_duration_s": _round(state.time_s, 1),
            "progress_pct": progress_pct,
            "samples": len(samples),
        },
        "thermal": {
            "material_id": state.tps.material_id,
            "thickness_mm": _round(state.tps.thickness_mm, 1),
            "surface_area_m2": _round(state.tps.surface_area_m2, 1),
            "peak_heat_flux_w_m2": _round(peak_heat_flux, 1),
            "peak_heat_flux_mw_m2": _mw_m2(peak_heat_flux),
            "avg_heat_flux_mw_m2": _mw_m2(avg_heat_flux),
            "peak_net_heat_flux_w_m2": _round(peak_net_heat_flux, 1),
            "peak_net_heat_flux_mw_m2": _mw_m2(peak_net_heat_flux),
            "peak_surface_temp_k": _round(peak_surface_temp, 1),
            "avg_surface_temp_k": _round(avg_surface_temp, 1),
            "final_surface_temp_k": _round(state.thermal.max_surface_temp_k, 1),
            "minimum_thermal_margin": _round(min_margin, 3),
            "minimum_thermal_margin_pct": _percent(min_margin),
            "thermal_load_mj_m2": _round(state.thermal.thermal_load_mj_m2, 3),
        },
        "aerodynamic": {
            "peak_dynamic_pressure_pa": _round(peak_dynamic_pressure, 1),
            "peak_dynamic_pressure_kpa": _round(peak_dynamic_pressure / 1000.0, 1),
            "avg_dynamic_pressure_kpa": _round(avg_dynamic_pressure / 1000.0, 1),
            "shock_cone_angle_deg": _round(state.aerodynamic.shock_cone_angle_deg, 2),
            "stagnation_temperature_k": _round(state.aerodynamic.stagnation_temperature_k, 1),
        },
        "cooling": {
            "enabled": state.cooling.enabled,
            "coolant": state.cooling.coolant,
            "mass_flow_kg_s": _round(state.cooling.mass_flow_kg_s, 2),
            "average_efficiency_pct": _percent(avg_cooling_efficiency),
            "final_heat_removed_w_m2": _round(state.cooling.heat_removed_w_m2, 1),
            "final_heat_removed_kw_m2": _kw_m2(state.cooling.heat_removed_w_m2),
            "peak_heat_removed_kw_m2": _kw_m2(peak_heat_removed),
        },
        "zonal_cooling": {
            "active_zone": state.zonal_cooling.active_zone,
            "balance_quality_pct": _percent(state.zonal_cooling.balance_quality),
            "max_zone_temp_k": _round(state.zonal_cooling.max_zone_temp_k, 1),
            "min_zone_margin_pct": _percent(state.zonal_cooling.min_zone_margin),
            "zones": zone_rows,
        },
        "plasma_shielding": {
            "peak_reduction_pct": _percent(peak_plasma_reduction),
            "final_reduction_pct": _percent(state.plasma_shielding.reduction_factor),
            "final_heat_flux_before_mw_m2": _mw_m2(state.plasma_shielding.heat_flux_before_w_m2),
            "final_heat_flux_after_mw_m2": _mw_m2(state.plasma_shielding.heat_flux_after_w_m2),
        },
        "rpic": {
            "peak_heat_flux_reduction_pct": _percent(peak_rpic_reduction),
            "final_heat_flux_reduction_pct": _percent(state.rpic.heat_flux_reduction),
            "peak_power_draw_kw": _round(peak_rpic_power, 1),
            "control_effort_pct": _percent(state.rpic.control_effort),
            "ionization_fraction_pct": _percent(state.rpic.ionization_fraction),
            "plasma_density_m3": state.rpic.plasma_density_m3,
        },
        "structural": {
            "peak_thermal_stress_mpa": _round(peak_thermal_stress, 2),
            "peak_joint_stress_mpa": _round(peak_joint_stress, 2),
            "final_thermal_stress_mpa": _round(state.structural.thermal_stress_mpa, 2),
            "final_joint_stress_mpa": _round(state.structural.joint_stress_mpa, 2),
            "fatigue_damage_pct": _percent(state.structural.fatigue_damage),
            "ablation_depth_mm": _round(state.structural.ablation_depth_mm, 4),
            "cycles": state.structural.cycles,
            "remaining_life_cycles": state.structural.remaining_life_cycles,
            "failure_probability_pct": _percent(max_failure_probability),
            "limiting_location": state.structural.limiting_location,
        },
        "risk": {
            "level": state.risk.level,
            "maximum_score": _round(max_risk_score, 3),
            "failure_warning": state.risk.failure_warning,
            "failure_probability_pct": _percent(state.ai.failure_probability),
            "anomaly_score": _round(state.ai.anomaly_score, 3),
            "sustainability_score_pct": _percent(state.sustainability.score),
        },
        "intelligence": {
            "model_stage": state.ai.model_stage,
            "model_confidence_pct": _percent(state.ai.model_confidence),
            "material_recommendation": [item.replace("_", " ") for item in state.ai.material_recommendation],
            "heat_forecast_k": state.ai.heat_forecast_k,
            "heatmap": heatmap,
            "maintenance_remaining_cycles": state.ai.maintenance_remaining_cycles,
            "surrogate_notes": state.ai.surrogate_notes,
        },
        "data_products": {
            "telemetry_jsonl": str(dataset_path),
            "report_markdown": str(report_path),
        },
        "alerts": [alert.model_dump() for alert in alerts_by_code.values()],
        "recommendations": recommendations,
    }

    markdown = _build_markdown(report)
    report["markdown"] = markdown

    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path.write_text(markdown, encoding="utf-8")
    report["report_path"] = str(report_path)

    return report
