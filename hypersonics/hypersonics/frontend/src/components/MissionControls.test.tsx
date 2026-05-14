import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { defaultMission } from "../state/defaultMission";
import { MissionControls } from "./MissionControls";

describe("MissionControls", () => {
  const defaultProps = {
    mission: defaultMission,
    onMissionChange: vi.fn(),
    onReset: vi.fn(),
  };

  it("starts the REGEN-TWIN mission from the primary action", async () => {
    const user = userEvent.setup();
    const onStart = vi.fn();

    render(<MissionControls {...defaultProps} running={false} onStart={onStart} />);

    await user.click(screen.getByRole("button", { name: /run regen-twin mission/i }));

    expect(onStart).toHaveBeenCalledTimes(1);
  });

  it("shows streaming state while mission is running", () => {
    render(<MissionControls {...defaultProps} running={true} onStart={vi.fn()} />);

    expect(screen.getByRole("button", { name: /streaming regen-twin/i })).toBeInTheDocument();
  });

  it("updates mission settings from the range controls", () => {
    const onMissionChange = vi.fn();

    render(<MissionControls {...defaultProps} running={false} onStart={vi.fn()} onMissionChange={onMissionChange} />);

    fireEvent.change(screen.getByLabelText(/mach/i), { target: { value: "7.2" } });

    expect(onMissionChange).toHaveBeenCalledWith({
      ...defaultMission,
      initial_conditions: {
        ...defaultMission.initial_conditions,
        mach: 7.2,
      },
    });
  });
});
