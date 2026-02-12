import { useState, useEffect } from 'react';
import type { Finding } from '../types';
import type { ManualFinding } from '../store/findingStore';

interface CoordEditorProps {
    isOpen: boolean;
    finding: Finding | ManualFinding | null;
    onSave: (updates: { x: number; y: number; width: number; height: number; page?: number }) => void;
    onClose: () => void;
}

export default function CoordEditor({ isOpen, finding, onSave, onClose }: CoordEditorProps) {
    const [x, setX] = useState(0);
    const [y, setY] = useState(0);
    const [width, setWidth] = useState(0);
    const [height, setHeight] = useState(0);
    const [page, setPage] = useState(1);

    // Initialize form values when finding changes
    useEffect(() => {
        if (finding) {
            if ('type' in finding && finding.type === 'manual') {
                // Manual finding
                setX(finding.x);
                setY(finding.y);
                setWidth(finding.width);
                setHeight(finding.height);
                setPage(finding.page);
            } else {
                // Auto finding (has flat properties)
                const autoFinding = finding as Finding;
                setX(autoFinding.x || 0);
                setY(autoFinding.y || 0);
                setWidth(autoFinding.width || 100);
                setHeight(autoFinding.height || 20);
                setPage(autoFinding.page);
            }
        }
    }, [finding]);

    if (!isOpen || !finding) return null;

    const isManual = 'type' in finding && finding.type === 'manual';
    const findingNumber = finding.id;

    const handleSave = () => {
        // Validate
        if (x < 0 || y < 0 || width <= 0 || height <= 0) {
            alert('Coordinates must be positive numbers');
            return;
        }

        onSave({ x, y, width, height, ...(isManual ? { page } : {}) });
        onClose();
    };

    return (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50" onClick={onClose}>
            <div
                className="bg-slate-800 rounded-xl p-6 max-w-md w-full mx-4 shadow-2xl border border-slate-700"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="flex justify-between items-start mb-4">
                    <div>
                        <h2 className="text-xl font-bold text-white">Edit Coordinates</h2>
                        <p className="text-sm text-slate-400 mt-1">
                            {isManual ? '📍 Manual Selection' : `${('detector' in finding ? finding.detector : 'Auto')}`} #{findingNumber}
                        </p>
                    </div>
                    <button
                        onClick={onClose}
                        className="text-slate-400 hover:text-white transition-colors"
                    >
                        ✕
                    </button>
                </div>

                <div className="space-y-4">
                    {/* Page selector - only for manual findings */}
                    {isManual && (
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-1">
                                Page Number
                            </label>
                            <input
                                type="number"
                                min="1"
                                value={page}
                                onChange={(e) => setPage(parseInt(e.target.value) || 1)}
                                className="w-full bg-slate-900 border border-slate-600 rounded px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>
                    )}

                    {/* X Coordinate */}
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-1">
                            X Position (left edge)
                        </label>
                        <input
                            type="number"
                            min="0"
                            step="0.1"
                            value={x}
                            onChange={(e) => setX(parseFloat(e.target.value) || 0)}
                            className="w-full bg-slate-900 border border-slate-600 rounded px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>

                    {/* Y Coordinate */}
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-1">
                            Y Position (top edge)
                        </label>
                        <input
                            type="number"
                            min="0"
                            step="0.1"
                            value={y}
                            onChange={(e) => setY(parseFloat(e.target.value) || 0)}
                            className="w-full bg-slate-900 border border-slate-600 rounded px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>

                    {/* Width */}
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-1">
                            Width
                        </label>
                        <input
                            type="number"
                            min="0.1"
                            step="0.1"
                            value={width}
                            onChange={(e) => setWidth(parseFloat(e.target.value) || 0)}
                            className="w-full bg-slate-900 border border-slate-600 rounded px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>

                    {/* Height */}
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-1">
                            Height
                        </label>
                        <input
                            type="number"
                            min="0.1"
                            step="0.1"
                            value={height}
                            onChange={(e) => setHeight(parseFloat(e.target.value) || 0)}
                            className="w-full bg-slate-900 border border-slate-600 rounded px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>

                    {/* Preview Info */}
                    <div className="bg-slate-900 rounded p-3 text-xs font-mono text-slate-400">
                        <div className="font-semibold text-slate-300 mb-1">Preview:</div>
                        <div>Box at ({Math.round(x)}, {Math.round(y)})</div>
                        <div>Size: {Math.round(width)} × {Math.round(height)} px</div>
                        {isManual && <div>Page: {page}</div>}
                    </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-3 mt-6">
                    <button
                        onClick={onClose}
                        className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors text-white font-medium"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSave}
                        className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors text-white font-medium"
                    >
                        💾 Save Changes
                    </button>
                </div>
            </div>
        </div>
    );
}
