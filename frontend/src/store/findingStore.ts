import { create } from 'zustand';
import type { Finding } from '../types';

interface FindingState {
    findings: Finding[];
    ignoredFindingIds: Set<string>;
    hoveredFindingId: string | null;

    setFindings: (findings: Finding[]) => void;
    toggleIgnored: (id: string) => void;
    isIgnored: (id: string) => boolean;
    invertSelection: () => void;
    setHoveredFinding: (id: string | null) => void;
    reset: () => void;
}

export const useFindingStore = create<FindingState>((set, get) => ({
    findings: [],
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
        const allIds = new Set(state.findings.map(f => f.id));
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

    reset: () => set({ findings: [], ignoredFindingIds: new Set(), hoveredFindingId: null })
}));
