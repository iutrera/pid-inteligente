import { create } from "zustand";
import type { PidStats } from "@/types/api";

export interface PidState {
  pids: PidStats[];
  activePidId: string | null;
  loading: boolean;
  addPid: (pid: PidStats) => void;
  setActivePid: (pidId: string | null) => void;
  removePid: (pidId: string) => void;
  setLoading: (loading: boolean) => void;
}

export const usePidStore = create<PidState>((set) => ({
  pids: [],
  activePidId: null,
  loading: false,

  addPid: (pid) =>
    set((state) => ({
      pids: [...state.pids, pid],
      activePidId: pid.pid_id,
    })),

  setActivePid: (pidId) => set({ activePidId: pidId }),

  removePid: (pidId) =>
    set((state) => ({
      pids: state.pids.filter((p) => p.pid_id !== pidId),
      activePidId:
        state.activePidId === pidId ? null : state.activePidId,
    })),

  setLoading: (loading) => set({ loading }),
}));
