import { afterEach, describe, expect, it, vi } from "vitest";
import { defaultMission } from "../state/defaultMission";
import { generateReport, startSimulation } from "./client";

describe("API client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("starts a simulation through the backend API", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ simulation_id: "sim_123", telemetry_ws: "/api/v1/telemetry/ws?simulation_id=sim_123" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const response = await startSimulation(defaultMission);

    expect(response.simulation_id).toBe("sim_123");
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/simulations/start",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("throws when report generation fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false }));

    await expect(generateReport("sim_404")).rejects.toThrow("Unable to generate report");
  });
});
