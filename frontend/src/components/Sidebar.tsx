import { useFindingStore, type ManualFinding } from '../store/findingStore';
import type { Finding } from '../types';

interface SidebarProps {
    onSanitize: () => void;
    onStartDrawing: () => void;
    onEditFinding?: (finding: Finding | ManualFinding) => void;
}

export default function Sidebar({ onSanitize, onStartDrawing, onEditFinding }: SidebarProps) {
    const {
        findings,
        manualFindings,
        isIgnored,
        toggleIgnored,
        invertSelection,
        removeManualFinding
    } = useFindingStore();

    const allFindings = [...findings, ...manualFindings];
    const toRemoveCount = allFindings.filter(f => !isIgnored(f.id)).length;
    const toKeepCount = allFindings.filter(f => isIgnored(f.id)).length;

    return (
        <div className="w-96 bg-slate-800 border-l border-slate-700 flex flex-col h-full">
            <div className="p-4 border-b border-slate-700">
                <h2 className="text-xl font-bold text-white mb-2">Review Findings</h2>
                <div className="flex gap-2 text-sm mb-3">
                    <div className="px-2 py-1 bg-red-500/20 border border-red-500 rounded text-red-300">
                        <strong>{toRemoveCount}</strong> Will Remove
                    </div>
                    <div className="px-2 py-1 bg-slate-700 border border-slate-600 rounded text-slate-300">
                        <strong>{toKeepCount}</strong> Will Keep
                    </div>
                </div>
                <div className="space-y-2">
                    <button
                        onClick={invertSelection}
                        className="w-full px-3 py-1.5 bg-slate-700 hover:bg-slate-600 border border-slate-600 rounded text-sm text-white transition-colors"
                    >
                        ⇄ Invert Selection
                    </button>
                    {onStartDrawing && (
                        <button
                            onClick={onStartDrawing}
                            className="w-full px-3 py-1.5 bg-blue-600 hover:bg-blue-700 border border-blue-500 rounded text-sm text-white transition-colors font-medium"
                        >
                            ➕ Add Manual Region
                        </button>
                    )}
                </div>
                <p className="text-xs text-slate-500 mt-2">Click any finding to toggle Keep/Remove</p>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {findings.map((finding, index) => (
                    <FindingCard
                        key={finding.id}
                        finding={finding}
                        findingNumber={index + 1}
                        ignored={isIgnored(finding.id)}
                        onToggle={() => toggleIgnored(finding.id)}
                        onEdit={() => onEditFinding?.(finding)}
                    />
                ))}

                {manualFindings.map((finding, index) => (
                    <ManualFindingCard
                        key={finding.id}
                        finding={finding}
                        findingNumber={findings.length + index + 1}
                        ignored={isIgnored(finding.id)}
                        onToggle={() => toggleIgnored(finding.id)}
                        onDelete={() => removeManualFinding(finding.id)}
                        onEdit={() => onEditFinding?.(finding)}
                    />
                ))}

                {allFindings.length === 0 && (
                    <div className="text-center text-slate-500 py-8">
                        No findings to review.
                    </div>
                )}
            </div>

            <div className="p-4 border-t border-slate-700 bg-slate-900 space-y-3">
                <button
                    onClick={onSanitize}
                    disabled={toRemoveCount === 0}
                    className={`w - full py - 3 rounded - lg font - semibold text - white transition - colors flex items - center justify - center gap - 2 ${toRemoveCount === 0
                        ? 'bg-slate-700 cursor-not-allowed'
                        : 'bg-emerald-500 hover:bg-emerald-600'
                        } `}
                >
                    <span>✨ Download Sanitized PDF</span>
                    {toRemoveCount > 0 && (
                        <span className="bg-emerald-700 px-2 py-0.5 rounded text-xs">
                            Remove {toRemoveCount}
                        </span>
                    )}
                </button>
                <p className="text-xs text-center text-slate-500">
                    {toRemoveCount === 0 ? 'All findings will be kept' : `${toKeepCount} finding(s) will be preserved`}
                </p>
            </div>
        </div >
    );
}

function FindingCard({ finding, findingNumber, ignored, onToggle, onEdit }: {
    finding: Finding,
    findingNumber: number,
    ignored: boolean,
    onToggle: () => void,
    onEdit: () => void
}) {
    const { hoveredFindingId, setHoveredFinding } = useFindingStore();
    const isHovered = hoveredFindingId === finding.id;

    return (
        <div
            className={`
p - 3 rounded - lg border transition - all cursor - pointer
                ${ignored
                    ? 'bg-slate-800 border-slate-700 opacity-80'
                    : isHovered
                        ? 'bg-slate-700 border-yellow-400 ring-2 ring-yellow-400/50'
                        : 'bg-slate-700/50 border-slate-600 hover:border-red-500/50'
                }
`}
            onClick={onToggle}
            onMouseEnter={() => setHoveredFinding(finding.id)}
            onMouseLeave={() => setHoveredFinding(null)}
        >
            <div className="flex justify-between items-start mb-2">
                <div className="flex items-center gap-2">
                    <span className={`
text - xs font - bold px - 2 py - 1 rounded
                        ${ignored ? 'bg-slate-600 text-white' : 'bg-red-600 text-white'}
`}>
                        #{findingNumber}
                    </span>
                    <span className="text-xs text-slate-400">Page {finding.page}</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className={`
                        flex items - center gap - 1 text - xs font - semibold px - 2 py - 1 rounded
                        ${ignored ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}
`}>
                        {ignored ? '✓ KEEP' : '✗ REMOVE'}
                    </div>
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            onEdit();
                        }}
                        className="px-2 py-1 bg-blue-600 hover:bg-blue-700 rounded text-xs text-white transition-colors"
                        title="Edit coordinates"
                    >
                        ✏️
                    </button>
                </div>
            </div>

            <p className="text-xs text-slate-300 mb-2 leading-relaxed">
                {finding.explanation}
            </p>

            <div className="text-xs font-mono bg-slate-900 px-2 py-1 rounded text-emerald-400 truncate">
                {finding.decoded_text || "Hidden Content"}
            </div>
        </div>
    );
}

function ManualFindingCard({ finding, findingNumber, ignored, onToggle, onDelete, onEdit }: {
    finding: ManualFinding,
    findingNumber: number,
    ignored: boolean,
    onToggle: () => void,
    onDelete: () => void,
    onEdit: () => void
}) {
    const { hoveredFindingId, setHoveredFinding } = useFindingStore();
    const isHovered = hoveredFindingId === finding.id;

    return (
        <div
            className={`
p - 3 rounded - lg border transition - all cursor - pointer
                ${ignored
                    ? 'bg-slate-800 border-slate-700 opacity-80'
                    : isHovered
                        ? 'bg-slate-700 border-yellow-400 ring-2 ring-yellow-400/50'
                        : 'bg-blue-700/30 border-blue-600 hover:border-blue-500/50'
                }
`}
            onClick={onToggle}
            onMouseEnter={() => setHoveredFinding(finding.id)}
            onMouseLeave={() => setHoveredFinding(null)}
        >
            <div className="flex justify-between items-start mb-2">
                <div className="flex items-center gap-2">
                    <span className={`
text - xs font - bold px - 2 py - 1 rounded
                        ${ignored ? 'bg-slate-600 text-white' : 'bg-blue-600 text-white'}
`}>
                        #{findingNumber}
                    </span>
                    <span className="text-xs text-blue-300 font-medium">📍 Manual</span>
                    <span className="text-xs text-slate-400">Page {finding.page}</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className={`
                        flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded
                        ${ignored ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}
                    `}>
                        {ignored ? '✓ KEEP' : '✗ REMOVE'}
                    </div>
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            onEdit();
                        }}
                        className="px-2 py-1 bg-blue-600 hover:bg-blue-700 rounded text-xs text-white transition-colors"
                        title="Edit coordinates"
                    >
                        ✏️
                    </button>
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            onDelete();
                        }}
                        className="px-2 py-1 bg-red-600 hover:bg-red-700 rounded text-xs text-white transition-colors"
                        title="Delete manual region"
                    >
                        🗑️
                    </button>
                </div>
            </div>

            <p className="text-xs text-slate-300 mb-2 leading-relaxed">
                User-defined region for removal
            </p>

            <div className="text-xs font-mono bg-slate-900 px-2 py-1 rounded text-blue-400">
                x: {Math.round(finding.x)}, y: {Math.round(finding.y)}, w: {Math.round(finding.width)}, h: {Math.round(finding.height)}
            </div>
        </div>
    );
}
