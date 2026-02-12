import { create } from 'zustand';
import type { Finding } from '../types';

export interface ManualFinding {
    id: string;
    type: 'manual';
    page: number;
    x: number;
    y: number;
    width: number;
    height: number;
}

interface FindingState {
    findings: Finding[];
    manualFindings: ManualFinding[];
    ignoredFindingIds: Set<string>;
    hoveredFindingId: string | null;

    setFindings: (findings: Finding[]) => void;
    toggleIgnored: (id: string) => void;
    isIgnored: (id: string) => boolean;
    invertSelection: () => void;
    setHoveredFinding: (id: string | null) => void;
    addManualFinding: (finding: ManualFinding) => void;
    removeManualFinding: (id: string) => void;
    updateManualFinding: (id: string, updates: Partial<ManualFinding>) => void;
    reset: () => void;
}

export const useFindingStore = create<FindingState>((set, get) => ({
    findings: [],
    manualFindings: [],
    ignoredFindingIds: new Set(),
    hoveredFindingId: null,

    setFindings: (findings) => set({ findings }),

    toggleIgnored: (id) => set((state) => {
        const newSet = new Set(state.ignoredFindingIds);
        if (newSet.has(id)) {
            newSet.delete(id);
        } else {
            newSet.add(id);
        }
        return { ignoredFindingIds: newSet };
    }),

    isIgnored: (id) => get().ignoredFindingIds.has(id),

    invertSelection: () => set((state) => {
        const allIds = new Set([
            ...state.findings.map(f => f.id),
            ...state.manualFindings.map(f => f.id)
        ]);
        const newIgnored = new Set<string>();

        // Flip: what was kept becomes removed, what was removed becomes kept
        for (const id of allIds) {
            if (!state.ignoredFindingIds.has(id)) {
                newIgnored.add(id);
            }
        }

        return { ignoredFindingIds: newIgnored };
    }),

    setHoveredFinding: (id) => set({ hoveredFindingId: id }),

    addManualFinding: (finding) => set((state) => ({
        manualFindings: [...state.manualFindings, finding]
    })),

    removeManualFinding: (id) => set((state) => ({
        manualFindings: state.manualFindings.filter(f => f.id !== id),
        ignoredFindingIds: new Set([...state.ignoredFindingIds].filter(fid => fid !== id))
    })),

    updateManualFinding: (id, updates) => set((state) => ({
        manualFindings: state.manualFindings.map(f =>
            f.id === id ? { ...f, ...updates } : f
        )
    })),

    reset: () => set({
        findings: [],
        manualFindings: [],
        ignoredFindingIds: new Set(),
        hoveredFindingId: null
    })
}));
