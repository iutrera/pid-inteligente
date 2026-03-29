import { describe, it, expect, beforeEach } from "vitest";
import { usePidStore } from "@/stores/pidStore";

describe("pidStore", () => {
  beforeEach(() => {
    // Reset store between tests
    usePidStore.setState({
      pids: [],
      activePidId: null,
      loading: false,
    });
  });

  it("should start with empty state", () => {
    const state = usePidStore.getState();
    expect(state.pids).toEqual([]);
    expect(state.activePidId).toBeNull();
    expect(state.loading).toBe(false);
  });

  it("should add a PID and set it as active", () => {
    const pid = {
      pid_id: "test-1",
      node_count: 10,
      edge_count: 8,
      equipment_count: 3,
      instrument_count: 5,
      file_name: "test.drawio",
    };

    usePidStore.getState().addPid(pid);

    const state = usePidStore.getState();
    expect(state.pids).toHaveLength(1);
    expect(state.pids[0]).toEqual(pid);
    expect(state.activePidId).toBe("test-1");
  });

  it("should set active PID", () => {
    const pid1 = {
      pid_id: "pid-1",
      node_count: 5,
      edge_count: 4,
      equipment_count: 2,
      instrument_count: 1,
    };
    const pid2 = {
      pid_id: "pid-2",
      node_count: 8,
      edge_count: 6,
      equipment_count: 3,
      instrument_count: 2,
    };

    usePidStore.getState().addPid(pid1);
    usePidStore.getState().addPid(pid2);
    expect(usePidStore.getState().activePidId).toBe("pid-2");

    usePidStore.getState().setActivePid("pid-1");
    expect(usePidStore.getState().activePidId).toBe("pid-1");
  });

  it("should remove a PID and clear active if it was active", () => {
    const pid = {
      pid_id: "pid-1",
      node_count: 5,
      edge_count: 4,
      equipment_count: 2,
      instrument_count: 1,
    };

    usePidStore.getState().addPid(pid);
    expect(usePidStore.getState().activePidId).toBe("pid-1");

    usePidStore.getState().removePid("pid-1");

    const state = usePidStore.getState();
    expect(state.pids).toHaveLength(0);
    expect(state.activePidId).toBeNull();
  });

  it("should not clear activePidId when removing a different PID", () => {
    const pid1 = {
      pid_id: "pid-1",
      node_count: 5,
      edge_count: 4,
      equipment_count: 2,
      instrument_count: 1,
    };
    const pid2 = {
      pid_id: "pid-2",
      node_count: 8,
      edge_count: 6,
      equipment_count: 3,
      instrument_count: 2,
    };

    usePidStore.getState().addPid(pid1);
    usePidStore.getState().addPid(pid2);

    usePidStore.getState().removePid("pid-1");

    const state = usePidStore.getState();
    expect(state.pids).toHaveLength(1);
    expect(state.activePidId).toBe("pid-2");
  });

  it("should set loading state", () => {
    usePidStore.getState().setLoading(true);
    expect(usePidStore.getState().loading).toBe(true);

    usePidStore.getState().setLoading(false);
    expect(usePidStore.getState().loading).toBe(false);
  });
});
