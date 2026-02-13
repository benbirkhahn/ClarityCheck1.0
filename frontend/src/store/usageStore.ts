import { create } from 'zustand';
import { getUsage } from '../api';

interface UsageState {
    plan: string;
    limit: number;
    usage: number;
    canUpload: boolean;
    isLoading: boolean;
    error: string | null;

    fetchUsage: () => Promise<void>;
    incrementUsage: () => void; // Optimistic update
}

export const useUsageStore = create<UsageState>((set, get) => ({
    plan: 'free_anon',
    limit: 5,
    usage: 0,
    canUpload: true,
    isLoading: false,
    error: null,

    fetchUsage: async () => {
        set({ isLoading: true });
        try {
            const data = await getUsage();
            set({
                plan: data.plan,
                limit: data.limit,
                usage: data.usage,
                canUpload: data.can_upload,
                isLoading: false,
                error: null
            });
        } catch (err) {
            set({
                error: err instanceof Error ? err.message : 'Failed to fetch usage',
                isLoading: false
            });
        }
    },

    incrementUsage: () => {
        const { usage, limit } = get();
        const newUsage = usage + 1;
        // For unlimited plans (limit < 0), always can upload
        // For limited plans, check if newUsage < limit
        const canUpload = limit < 0 ? true : newUsage < limit;

        set({
            usage: newUsage,
            canUpload
        });
    }
}));
