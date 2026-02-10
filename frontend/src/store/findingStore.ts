import { create } from 'zustand';
import type { Finding } from '../types';

interface FindingState {
    findings: Finding[];
    ignoredFindingIds: Set<string>; // IDs of findings to IGNORE (keep in doc)

    setFindings: (findings: Finding[]) => void;
    toggleIgnored: (id: string) => void;
    isIgnored: (id: string) => boolean;
    reset: () => void;
}

export const useFindingStore = create<FindingState>((set, get) => ({
    findings: [],
    ignoredFindingIds: new Set(),

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

    reset: () => set({ findings: [], ignoredFindingIds: new Set() })
}));
