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
        priceId: 'price_1T1x6nGc5yiFDDpmdYmwEnLj',
        color: 'emerald',
        gradient: 'from-emerald-500/20 to-emerald-600/5',
        border: 'border-emerald-500/50'
    },
    {
        id: 'pro',
        name: 'Pro',
        price: 9.99,
        interval: 'mo',
        features: ['Unlimited PDFs', 'Priority Support', 'Advanced Analytics', 'Team Access'],
        priceId: 'price_1T1x7fGc5yiFDDpmDvUBB2YV',
        color: 'blue',
        gradient: 'from-blue-500/20 to-indigo-600/5',
        border: 'border-blue-500/50',
        popular: true
    }
];

const PACKS = [
    {
        id: '10_credits',
        name: '10 Credits',
        price: 2.99,
        priceId: 'price_1T1x8bGc5yiFDDpmpy8bXZyW',
    },
    {
        id: '25_credits',
        name: '25 Credits',
        price: 4.99,
        priceId: 'price_1T1x9VGc5yiFDDpmqXzwV5o6',
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
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md z-50 flex items-center justify-center p-4 animate-fade-in">
            <div className="bg-slate-900/90 border border-white/10 rounded-3xl max-w-5xl w-full max-h-[90vh] overflow-y-auto shadow-2xl relative animate-slide-up">
                {/* Close button */}
                <button
                    onClick={onClose}
                    className="absolute top-6 right-6 p-2 rounded-full bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-colors z-20"
                >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>

                <div className="p-8 md:p-12">
                    <div className="text-center mb-12">
                        <h2 className="text-3xl md:text-4xl font-bold text-white mb-4 text-glow">Upgrade Your Workflow</h2>
                        <p className="text-slate-400 text-lg max-w-2xl mx-auto">Choose the plan that fits your needs. Cancel anytime.</p>
                    </div>

                    <div className="grid md:grid-cols-2 gap-8 mb-16">
                        {PLANS.map((plan) => (
                            <div
                                key={plan.id}
                                className={`relative p-8 rounded-2xl border-2 transition-all duration-300 flex flex-col ${currentPlan.includes(plan.id)
                                        ? `bg-slate-800/50 ${plan.border}`
                                        : `bg-gradient-to-br ${plan.gradient} border-transparent hover:border-white/10 hover:shadow-xl hover:-translate-y-1`
                                    }`}
                            >
                                {plan.popular && !currentPlan.includes(plan.id) && (
                                    <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm font-bold rounded-full shadow-lg shadow-blue-500/20">
                                        MOST POPULAR
                                    </div>
                                )}
                                {currentPlan.includes(plan.id) && (
                                    <div className={`absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1.5 bg-${plan.color}-600 text-white text-sm font-bold rounded-full shadow-lg`}>
                                        CURRENT PLAN
                                    </div>
                                )}

                                <div className="mb-6">
                                    <h3 className={`text-2xl font-bold text-white mb-2`}>{plan.name}</h3>
                                    <div className="flex items-baseline gap-1">
                                        <span className="text-4xl font-bold text-white">${plan.price}</span>
                                        <span className="text-slate-400 font-medium">/{plan.interval}</span>
                                    </div>
                                </div>

                                <ul className="space-y-4 mb-8 flex-1">
                                    {plan.features.map((feat, i) => (
                                        <li key={i} className="flex items-center gap-3 text-slate-300">
                                            <div className={`flex-shrink-0 w-6 h-6 rounded-full bg-${plan.color}-500/20 flex items-center justify-center`}>
                                                <svg className={`w-4 h-4 text-${plan.color}-400`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                                </svg>
                                            </div>
                                            {feat}
                                        </li>
                                    ))}
                                </ul>

                                <button
                                    onClick={() => handleSubscribe(plan.priceId, plan.id)}
                                    disabled={!!loadingId || currentPlan.includes(plan.id)}
                                    className={`w-full py-4 rounded-xl font-bold transition-all ${currentPlan.includes(plan.id)
                                            ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
                                            : `bg-gradient-to-r from-${plan.color}-600 to-${plan.color}-500 hover:from-${plan.color}-500 hover:to-${plan.color}-400 text-white shadow-lg shadow-${plan.color}-500/25`
                                        }`}
                                >
                                    {loadingId === plan.id ? (
                                        <span className="flex items-center justify-center gap-2">
                                            <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                            </svg>
                                            Processing...
                                        </span>
                                    ) : currentPlan.includes(plan.id) ? 'Active Plan' : `Upgrade to ${plan.name}`}
                                </button>
                            </div>
                        ))}
                    </div>

                    {/* One-time Credits */}
                    <div className="pt-10 border-t border-white/10">
                        <div className="flex flex-col md:flex-row items-center justify-between gap-6 mb-8">
                            <div>
                                <h3 className="text-xl font-bold text-white mb-2">Need a quick top-up?</h3>
                                <p className="text-slate-400">Buy one-time credits for occasional use.</p>
                            </div>
                        </div>

                        <div className="grid md:grid-cols-2 gap-4">
                            {PACKS.map(pack => (
                                <button
                                    key={pack.id}
                                    onClick={() => handleSubscribe(pack.priceId, pack.id)}
                                    disabled={!!loadingId}
                                    className="group flex items-center justify-between p-6 rounded-xl bg-slate-800/30 border border-white/5 hover:border-emerald-500/50 hover:bg-slate-800/60 transition-all hover:scale-[1.01]"
                                >
                                    <div className="flex items-center gap-4">
                                        <div className="w-10 h-10 rounded-full bg-emerald-500/10 flex items-center justify-center group-hover:bg-emerald-500/20 transition-colors">
                                            <span className="text-lg">⚡️</span>
                                        </div>
                                        <span className="font-semibold text-lg text-slate-200 group-hover:text-white transition-colors">{pack.name}</span>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <span className="font-bold text-xl text-emerald-400">${pack.price}</span>
                                        <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center group-hover:bg-emerald-500/20 transition-colors">
                                            <svg className="w-4 h-4 text-slate-400 group-hover:text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                            </svg>
                                        </div>
                                    </div>
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
