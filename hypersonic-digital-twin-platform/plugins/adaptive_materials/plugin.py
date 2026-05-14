class AdaptiveMaterialsPlugin:
    name = "adaptive_materials"

    def update(self, state, dt_s: float):
        # Demo subsystem: smart materials improve risk slightly when thermal margin is healthy.
        if state.thermal.thermal_margin > 0.18:
            state.risk.score = max(0.0, state.risk.score - 0.035)
        return state


def register(registry):
    registry.add_module("adaptive_materials", AdaptiveMaterialsPlugin(), phase="post_risk")

