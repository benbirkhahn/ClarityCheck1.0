import { useState } from 'react';
import { createCheckoutSession } from '../api';
import { useUsageStore } from '../store/usageStore';

interface PricingModalProps {
    onClose: () => void;
}

const PLANS = [
    {
        id: 'student',
        name: 'Student',
        price: 4.99,
        interval: 'mo',
        features: ['50 PDFs / month', 'Basic Support', '1 User'],
        priceId: 'price_student_monthly_placeholder', // TODO: User to header
        color: 'emerald'
    },
    {
        id: 'pro',
        name: 'Pro',
        price: 9.99,
        interval: 'mo',
        features: ['Unlimited PDFs', 'Priority Support', 'Advanced Analytics'],
        priceId: 'price_pro_monthly_placeholder',
        color: 'blue'
    }
];

const PACKS = [
    {
        id: '10_credits',
        name: '10 Credits',
        price: 2.99,
        priceId: 'price_10_credits_placeholder',
    },
    {
        id: '25_credits',
        name: '25 Credits',
        price: 4.99,
        priceId: 'price_25_credits_placeholder',
    }
]

export default function PricingModal({ onClose }: PricingModalProps) {
    const [loadingId, setLoadingId] = useState<string | null>(null);
    const { plan: currentPlan } = useUsageStore();

    const handleSubscribe = async (priceId: string, id: string) => {
        setLoadingId(id);
        try {
            const { url } = await createCheckoutSession(priceId);
            if (url) window.location.href = url;
        } catch (err) {
            alert('Failed to start checkout: ' + (err instanceof Error ? err.message : String(err)));
            setLoadingId(null);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
                <div className="p-6 border-b border-slate-700 flex justify-between items-center sticky top-0 bg-slate-900/95 backdrop-blur z-10">
                    <div>
                        <h2 className="text-2xl font-bold text-white">Upgrade Plan</h2>
                        <p className="text-slate-400">Choose the best plan for your needs</p>
                    </div>
                    <button onClick={onClose} className="text-slate-400 hover:text-white p-2">✕</button>
                </div>

                <div className="p-6 md:p-8 space-y-8">
                    {/* Subscriptions */}
                    <div className="grid md:grid-cols-2 gap-6">
                        {PLANS.map((plan) => (
                            <div
                                key={plan.id}
                                className={`relative p-6 rounded-xl border-2 transition-all ${currentPlan.includes(plan.id)
                                        ? `border-${plan.color}-500 bg-${plan.color}-500/10`
                                        : 'border-slate-700 hover:border-slate-500 bg-slate-800/50'
                                    }`}
                            >
                                {currentPlan.includes(plan.id) && (
                                    <div className={`absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-${plan.color}-500 text-white text-xs font-bold rounded-full`}>
                                        CURRENT PLAN
                                    </div>
                                )}
                                <h3 className={`text-xl font-bold text-${plan.color}-400 mb-2`}>{plan.name}</h3>
                                <div className="flex items-baseline gap-1 mb-4">
                                    <span className="text-3xl font-bold text-white">${plan.price}</span>
                                    <span className="text-slate-400">/{plan.interval}</span>
                                </div>
                                <ul className="space-y-3 mb-6">
                                    {plan.features.map((feat, i) => (
                                        <li key={i} className="flex items-center gap-2 text-slate-300">
                                            <span className={`text-${plan.color}-400`}>✓</span> {feat}
                                        </li>
                                    ))}
                                </ul>
                                <button
                                    onClick={() => handleSubscribe(plan.priceId, plan.id)}
                                    disabled={!!loadingId || currentPlan.includes(plan.id)}
                                    className={`w-full py-3 rounded-lg font-bold transition-all ${currentPlan.includes(plan.id)
                                            ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
                                            : `bg-${plan.color}-600 hover:bg-${plan.color}-500 text-white`
                                        }`}
                                >
                                    {loadingId === plan.id ? 'Loading...' : currentPlan.includes(plan.id) ? 'Active' : 'Upgrade'}
                                </button>
                            </div>
                        ))}
                    </div>

                    {/* One-time Credits */}
                    <div className="pt-6 border-t border-slate-700">
                        <h3 className="text-lg font-bold text-white mb-4">Need a quick top-up?</h3>
                        <div className="grid md:grid-cols-2 gap-4">
                            {PACKS.map(pack => (
                                <button
                                    key={pack.id}
                                    onClick={() => handleSubscribe(pack.priceId, pack.id)}
                                    disabled={!!loadingId}
                                    className="flex items-center justify-between p-4 rounded-lg bg-slate-800 border border-slate-700 hover:border-emerald-500 group transition-all"
                                >
                                    <span className="font-medium text-slate-200 group-hover:text-white">{pack.name}</span>
                                    <span className="font-bold text-emerald-400">${pack.price}</span>
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
