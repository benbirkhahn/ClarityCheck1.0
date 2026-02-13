import { useEffect } from 'react';
import { useUsageStore } from '../store/usageStore';

export default function UsageBadge() {
    const { usage, limit, plan, isLoading, fetchUsage } = useUsageStore();

    useEffect(() => {
        fetchUsage();
    }, [fetchUsage]);

    if (isLoading) return <div className="animate-pulse h-6 w-20 bg-slate-800 rounded"></div>;

    const isUnlimited = limit < 0;
    const remaining = isUnlimited ? Infinity : Math.max(0, limit - usage);

    // Color coding based on remaining credits
    let colorClass = "bg-emerald-500/10 text-emerald-400 border-emerald-500/50";
    if (!isUnlimited && remaining === 0) {
        colorClass = "bg-red-500/10 text-red-400 border-red-500/50";
    } else if (!isUnlimited && remaining <= 2) {
        colorClass = "bg-amber-500/10 text-amber-400 border-amber-500/50";
    }

    return (
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border ${colorClass} text-sm font-medium transition-colors`}>
            <span className="text-xs uppercase opacity-70 tracking-wider">
                {plan.replace('_', ' ')}
            </span>
            <span className="w-px h-3 bg-current opacity-30 mx-1" />
            <span>
                {isUnlimited ? '∞' : `${remaining} left`}
            </span>
        </div>
    );
}
