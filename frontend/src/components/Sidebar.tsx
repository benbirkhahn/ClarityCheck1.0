import { useFindingStore } from '../store/findingStore';
import type { Finding } from '../types';

interface SidebarProps {
    onSanitize: () => void;
    onReset: () => void;
}

export default function Sidebar({ onSanitize, onReset }: SidebarProps) {
    const { findings, isIgnored, toggleIgnored } = useFindingStore();

    const criticalCount = findings.filter(f => f.impact === 'critical' && !isIgnored(f.id)).length;
    const ignoredCount = findings.filter(f => isIgnored(f.id)).length;

    return (
        <div className="w-96 bg-slate-800 border-l border-slate-700 flex flex-col h-full">
            <div className="p-4 border-b border-slate-700">
                <h2 className="text-xl font-bold text-white mb-2">Review Findings</h2>
                <div className="flex justify-between text-sm text-slate-400">
                    <span>{findings.length} total</span>
                    <span>{ignoredCount} ignored</span>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {findings.map((finding) => (
                    <FindingCard
                        key={finding.id}
                        finding={finding}
                        ignored={isIgnored(finding.id)}
                        onToggle={() => toggleIgnored(finding.id)}
                    />
                ))}

                {findings.length === 0 && (
                    <div className="text-center text-slate-500 py-8">
                        No findings to review.
                    </div>
                )}
            </div>

            <div className="p-4 border-t border-slate-700 bg-slate-900 space-y-3">
                <button
                    onClick={onSanitize}
                    className="w-full py-3 bg-emerald-500 hover:bg-emerald-600 rounded-lg font-semibold text-white transition-colors flex items-center justify-center gap-2"
                >
                    <span>✨ Sanitize Document</span>
                    {criticalCount > 0 && (
                        <span className="bg-emerald-700 px-2 py-0.5 rounded text-xs">
                            {criticalCount} Critical
                        </span>
                    )}
                </button>
                <button
                    onClick={onReset}
                    className="w-full py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-300 text-sm transition-colors"
                >
                    Invert Selection
                </button>
            </div>
        </div>
    );
}

function FindingCard({ finding, ignored, onToggle }: { finding: Finding, ignored: boolean, onToggle: () => void }) {
    return (
        <div
            className={`
                p-3 rounded-lg border transition-all cursor-pointer
                ${ignored
                    ? 'bg-slate-800 border-slate-700 opacity-60'
                    : 'bg-slate-700/50 border-slate-600 hover:border-emerald-500/50'
                }
            `}
            onClick={onToggle}
        >
            <div className="flex justify-between items-start mb-2">
                <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${getTrapColor(finding.trap_type)}`} />
                    <span className="font-medium text-slate-200 text-sm capitalize">{finding.trap_type}</span>
                </div>
                <span className="text-xs text-slate-500">Pg {finding.page}</span>
            </div>

            <p className="text-xs text-slate-400 mb-2 truncate" title={finding.explanation}>
                {finding.explanation}
            </p>

            <div className="flex items-center justify-between mt-2">
                <div className="text-xs font-mono bg-slate-900 px-2 py-1 rounded text-emerald-400 truncate max-w-[180px]">
                    {finding.decoded_text || "Hidden Content"}
                </div>
                <div className={`
                    w-4 h-4 rounded border flex items-center justify-center
                    ${ignored ? 'border-slate-500' : 'bg-emerald-500 border-emerald-500'}
                 `}>
                    {!ignored && <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>}
                </div>
            </div>
        </div>
    );
}

function getTrapColor(type: string): string {
    switch (type) {
        case 'instruction': return 'bg-red-500';
        case 'canary': return 'bg-yellow-500';
        case 'watermark': return 'bg-purple-500';
        case 'obfuscation': return 'bg-blue-500';
        default: return 'bg-slate-500';
    }
}
