import { useState, useCallback } from 'react';
import { uploadDocument, getAnalysis, downloadSanitized, pollJobStatus } from '../api';
import type { UploadResponse, AnalysisResponse } from '../types';
import PDFViewer from '../components/PDFViewer';
import Sidebar from '../components/Sidebar';
import UsageBadge from '../components/UsageBadge';
import PricingModal from '../components/PricingModal';
import { useFindingStore } from '../store/findingStore';
import { useUsageStore } from '../store/usageStore';
import { useAuth } from '../context/AuthContext';

export default function Dashboard() {
    const [isDragging, setIsDragging] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [statusMessage, setStatusMessage] = useState<string>("");
    const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
    const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [isDrawingMode, setIsDrawingMode] = useState(false);
    const [editingFindingId, setEditingFindingId] = useState<string | null>(null);
    const [fileUrl, setFileUrl] = useState<string | null>(null);

    const { logout, user } = useAuth();

    // Store actions
    const setFindings = useFindingStore(state => state.setFindings);
    const resetStore = useFindingStore(state => state.reset);
    const findings = useFindingStore(state => state.findings);
    const manualFindings = useFindingStore(state => state.manualFindings);
    const ignoredFindingIds = useFindingStore(state => state.ignoredFindingIds);
    const updateFinding = useFindingStore(state => state.updateFinding);
    const updateManualFinding = useFindingStore(state => state.updateManualFinding);

    // Usage store
    const { fetchUsage, isPricingOpen, setPricingOpen } = useUsageStore();

    const handleFile = useCallback(async (file: File) => {
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            setError('Please upload a PDF file');
            return;
        }

        setIsLoading(true);
        setStatusMessage("Uploading document...");
        setError(null);
        setUploadResult(null);
        setAnalysis(null);
        resetStore();

        try {
            // 1. Upload
            const result = await uploadDocument(file);
            setUploadResult(result);

            // Refresh usage stats
            fetchUsage();

            // 2. Poll for completion
            setStatusMessage("Analyzing document (this may take a moment)...");
            await pollJobStatus(result.job_id);

            // 3. Get final results
            const analysisData = await getAnalysis(result.job_id);
            setAnalysis(analysisData);

            // Initialize Store
            setFindings(analysisData.findings);

        } catch (err) {
            const message = err instanceof Error ? err.message : 'Upload failed';
            // Use friendly error if it's a 429
            if (message.includes('429') || message.includes('Limit reached')) {
                setError('You have reached your free monthly upload limit.');
            } else {
                setError(message);
            }
        } finally {
            setIsLoading(false);
            setStatusMessage("");
        }
    }, [resetStore, setFindings]);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        const file = e.dataTransfer.files[0];
        if (file) handleFile(file);
    }, [handleFile]);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback(() => {
        setIsDragging(false);
    }, []);

    const handleSanitize = useCallback(async () => {
        if (!uploadResult) return;
        try {
            // Track which auto findings have been edited
            const editedFindingIds = useFindingStore.getState().editedFindingIds;

            // Split auto findings into edited and unedited
            const uneditedAutoFindings = findings.filter(f => !editedFindingIds.has(f.id));
            const editedAutoFindings = findings.filter(f => editedFindingIds.has(f.id));

            // Unedited auto findings use backend's stored coordinates
            const uneditedConfirmedIds = uneditedAutoFindings
                .filter(f => !ignoredFindingIds.has(f.id))
                .map(f => f.id);

            // Manual regions: BOTH manual findings AND edited auto findings
            const manualRegions = [
                // Edited auto findings with updated coordinates
                ...editedAutoFindings
                    .filter(f => !ignoredFindingIds.has(f.id))
                    .map(f => ({
                        id: f.id,
                        page: f.page,
                        x: f.x || 0,
                        y: f.y || 0,
                        width: f.width || 100,
                        height: f.height || 20,
                    })),
                // Manual findings
                ...manualFindings
                    .filter(f => !ignoredFindingIds.has(f.id))
                    .map(f => ({
                        id: f.id,
                        page: f.page,
                        x: f.x,
                        y: f.y,
                        width: f.width,
                        height: f.height,
                    }))
            ];

            await downloadSanitized(uploadResult.job_id, uploadResult.filename, uneditedConfirmedIds, manualRegions);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Sanitization failed');
        }
    }, [uploadResult, findings, manualFindings, ignoredFindingIds]);

    // Handle visual edit mode complete
    const handleEditComplete = (id: string, updates: { x: number; y: number; width: number; height: number }) => {
        const manualFinding = manualFindings.find(f => f.id === id);
        if (manualFinding) {
            updateManualFinding(id, updates);
        } else {
            updateFinding(id, updates);
        }
        setEditingFindingId(null);
    };


    const resetState = () => {
        setUploadResult(null);
        setAnalysis(null);
        setError(null);
        resetStore();
    };

    // Wrap handleFile to save URL
    const onFileSelect = (file: File) => {
        const url = URL.createObjectURL(file);
        setFileUrl(url);
        handleFile(file);
    };

    return (
        <div className="min-h-screen bg-slate-950 text-slate-200 flex flex-col relative overflow-hidden">
            {/* Background Effects for Dashboard */}
            <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-brand-500/10 rounded-full blur-[120px] pointer-events-none" />
            <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-600/10 rounded-full blur-[120px] pointer-events-none" />

            {/* Header */}
            <header className="border-b border-white/10 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
                    <div className="flex items-center gap-6">
                        <h1 className="text-2xl font-bold tracking-tight">
                            <span className="text-brand-400 text-glow">Clarity</span>Check
                        </h1>
                        {analysis && (
                            <div className={`px-4 py-1.5 rounded-full text-sm font-semibold border ${analysis.risk_score > 70 ? 'bg-red-500/20 border-red-500/50 text-red-300' :
                                    analysis.risk_score > 30 ? 'bg-yellow-500/20 border-yellow-500/50 text-yellow-300' :
                                        'bg-brand-500/20 border-brand-500/50 text-brand-300'
                                }`}>
                                Score: {analysis.risk_score}
                            </div>
                        )}
                        <UsageBadge />
                    </div>
                    <div className="flex items-center gap-4">
                        {analysis && (
                            <button onClick={resetState} className="text-sm font-medium text-slate-400 hover:text-white transition-colors">
                                New Scan
                            </button>
                        )}
                        <div className="flex items-center gap-3 border-l border-white/10 pl-6">
                            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brand-500 to-blue-600 flex items-center justify-center text-xs font-bold text-white shadow-lg">
                                {user?.email?.charAt(0).toUpperCase()}
                            </div>
                            <button onClick={logout} className="text-sm font-medium text-slate-400 hover:text-white transition-colors">
                                Logout
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            <main className="flex-1 overflow-hidden relative flex flex-col">
                {/* Upload Area */}
                {!analysis && (
                    <div className="flex-1 flex flex-col items-center justify-center p-6 animate-fade-in relative z-10">
                        <div className="max-w-xl w-full">
                            <div className="text-center mb-10">
                                <h2 className="text-4xl font-bold text-white mb-4">Upload your document</h2>
                                <p className="text-slate-400 text-lg">Securely analyze and redact sensitive information from your PDFs.</p>
                            </div>

                            <div
                                className={`border-2 border-dashed rounded-3xl p-16 text-center transition-all duration-300 ${isDragging
                                    ? 'border-brand-500 bg-brand-500/10 scale-[1.02] shadow-2xl shadow-brand-500/20'
                                    : 'border-slate-700 hover:border-brand-500/50 hover:bg-slate-800/50 bg-slate-900/40 backdrop-blur-sm'
                                    }`}
                                onDrop={handleDrop}
                                onDragOver={handleDragOver}
                                onDragLeave={handleDragLeave}
                            >
                                {isLoading ? (
                                    <div className="space-y-6">
                                        <div className="relative w-20 h-20 mx-auto">
                                            <div className="absolute inset-0 rounded-full border-4 border-slate-700 opacity-25"></div>
                                            <div className="absolute inset-0 rounded-full border-4 border-brand-500 border-t-transparent animate-spin"></div>
                                        </div>
                                        <div>
                                            <h3 className="text-xl font-semibold text-white mb-2">{statusMessage || "Processing..."}</h3>
                                            <p className="text-slate-500 text-sm">This typically takes 5-10 seconds</p>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="py-4">
                                        <div className="w-24 h-24 bg-slate-800/80 rounded-full flex items-center justify-center mx-auto mb-8 shadow-inner ring-1 ring-white/10">
                                            <svg className="w-10 h-10 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                                            </svg>
                                        </div>
                                        <h3 className="text-xl font-bold text-white mb-2">Drop your PDF here</h3>
                                        <p className="text-slate-400 mb-8">or click to browse from your computer</p>
                                        <input
                                            type="file"
                                            accept=".pdf"
                                            onChange={(e) => e.target.files?.[0] && onFileSelect(e.target.files[0])}
                                            className="hidden"
                                            id="file-input"
                                        />
                                        <label
                                            htmlFor="file-input"
                                            className="inline-flex items-center gap-2 px-8 py-4 bg-brand-600 hover:bg-brand-500 text-white rounded-xl cursor-pointer transition-all font-semibold shadow-lg shadow-brand-500/20 hover:scale-105"
                                        >
                                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                                            </svg>
                                            Select PDF File
                                        </label>
                                    </div>
                                )}
                            </div>

                            {error && (
                                <div className="mt-8 p-4 bg-red-500/10 border border-red-500/50 rounded-xl text-red-200 text-center animate-slide-up flex items-center justify-center gap-3">
                                    <svg className="w-5 h-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                    </svg>
                                    {error}
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Interactive Workspace */}
                {analysis && uploadResult && fileUrl && (
                    <div className="flex h-full animate-fade-in relative z-10">
                        {/* Main Viewer Area */}
                        <div className="flex-1 bg-slate-950/50 p-6 overflow-auto flex justify-center backdrop-blur-sm">
                            <div className="shadow-2xl shadow-black/50">
                                <PDFViewer
                                    fileUrl={fileUrl}
                                    isDrawingMode={isDrawingMode}
                                    onDrawingComplete={() => setIsDrawingMode(false)}
                                    editingFindingId={editingFindingId}
                                    onEditComplete={handleEditComplete}
                                    onEditCancel={() => setEditingFindingId(null)}
                                />
                            </div>
                        </div>

                        {/* Sidebar */}
                        <Sidebar
                            onSanitize={handleSanitize}
                            onStartDrawing={() => setIsDrawingMode(true)}
                            onEditFinding={(finding) => setEditingFindingId(finding.id)}
                            onUpgrade={() => setPricingOpen(true)}
                        />
                    </div>
                )}

                {/* Pricing Modal */}
                {isPricingOpen && <div className="fixed inset-0 z-[100]"><PricingModal onClose={() => setPricingOpen(false)} /></div>}
            </main>
        </div>
    );
}
