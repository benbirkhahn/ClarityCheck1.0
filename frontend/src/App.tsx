import { useState, useCallback } from 'react';
import { uploadDocument, getAnalysis, downloadSanitized, pollJobStatus } from './api';
import { UploadResponse, AnalysisResponse, Finding } from './types';

function App() {
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string>("");
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

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

    try {
      // 1. Upload
      const result = await uploadDocument(file);
      setUploadResult(result);

      // 2. Poll for completion
      setStatusMessage("Analyzing document (this may take a moment)...");
      await pollJobStatus(result.job_id);

      // 3. Get final results
      const analysisData = await getAnalysis(result.job_id);
      setAnalysis(analysisData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsLoading(false);
      setStatusMessage("");
    }
  }, []);

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

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const handleSanitize = useCallback(async () => {
    if (!uploadResult) return;
    try {
      await downloadSanitized(uploadResult.job_id, uploadResult.filename);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sanitization failed');
    }
  }, [uploadResult]);

  const resetState = () => {
    setUploadResult(null);
    setAnalysis(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 text-white">
      {/* Header */}
      <header className="border-b border-slate-700 bg-slate-900/50 backdrop-blur">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <h1 className="text-2xl font-bold">
            <span className="text-emerald-400">Clarity</span>Check
          </h1>
          <p className="text-slate-400 text-sm">AI Trap Detection & Removal</p>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* Upload Area */}
        {!analysis && (
          <div
            className={`border-2 border-dashed rounded-xl p-12 text-center transition-all ${isDragging
              ? 'border-emerald-400 bg-emerald-400/10'
              : 'border-slate-600 hover:border-slate-500'
              }`}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
          >
            {isLoading ? (
              <div className="space-y-4">
                <div className="animate-spin w-12 h-12 border-4 border-emerald-400 border-t-transparent rounded-full mx-auto" />
                <p className="text-slate-300">{statusMessage || "Processing..."}</p>
              </div>
            ) : (
              <>
                <div className="text-6xl mb-4">📄</div>
                <p className="text-xl mb-2">Drop your PDF here</p>
                <p className="text-slate-400 mb-4">or click to browse</p>
                <input
                  type="file"
                  accept=".pdf"
                  onChange={handleFileInput}
                  className="hidden"
                  id="file-input"
                />
                <label
                  htmlFor="file-input"
                  className="inline-block px-6 py-3 bg-emerald-500 hover:bg-emerald-600 rounded-lg cursor-pointer transition-colors font-medium"
                >
                  Select PDF
                </label>
              </>
            )}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mt-6 p-4 bg-red-500/20 border border-red-500 rounded-lg text-red-300">
            {error}
          </div>
        )}

        {/* Results */}
        {analysis && uploadResult && (
          <div className="space-y-6">
            {/* Risk Score Card */}
            <div className={`rounded-xl p-6 ${getRiskBg(analysis.risk_level)}`}>
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold mb-1">{analysis.filename}</h2>
                  <p className="text-slate-300">{analysis.total_pages} pages scanned</p>
                </div>
                <div className="text-right">
                  <div className="text-4xl font-bold">{analysis.risk_score}</div>
                  <div className={`text-lg font-semibold ${getRiskColor(analysis.risk_level)}`}>
                    {analysis.risk_level}
                  </div>
                </div>
              </div>
            </div>

            {/* Summary */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(analysis.summary_by_type).map(([type, count]) => (
                <div key={type} className="bg-slate-800 rounded-lg p-4">
                  <div className="text-3xl font-bold text-emerald-400">{count}</div>
                  <div className="text-slate-300 capitalize">{type} trap{count !== 1 ? 's' : ''}</div>
                </div>
              ))}
            </div>

            {/* Findings List */}
            <div className="bg-slate-800 rounded-xl overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-700">
                <h3 className="text-lg font-semibold">Hidden Content Found</h3>
              </div>
              <div className="divide-y divide-slate-700">
                {analysis.findings.map((finding, idx) => (
                  <FindingRow key={idx} finding={finding} />
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-4">
              <button
                onClick={handleSanitize}
                className="flex-1 py-4 bg-emerald-500 hover:bg-emerald-600 rounded-xl font-semibold text-lg transition-colors"
              >
                ✨ Download Sanitized PDF
              </button>
              <button
                onClick={resetState}
                className="px-6 py-4 bg-slate-700 hover:bg-slate-600 rounded-xl font-semibold transition-colors"
              >
                Scan Another
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

function FindingRow({ finding }: { finding: Finding }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="px-6 py-4">
      <div
        className="flex items-center gap-4 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className={`w-3 h-3 rounded-full ${getTrapColor(finding.trap_type)}`} />
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="font-medium capitalize">{finding.trap_type}</span>
            <span className="text-slate-500">•</span>
            <span className="text-slate-400">Page {finding.page}</span>
            <span className={`px-2 py-0.5 rounded text-xs ${getImpactBadge(finding.impact)}`}>
              {finding.impact}
            </span>
          </div>
          <p className="text-slate-400 text-sm truncate">{finding.decoded_text}</p>
        </div>
        <div className="text-slate-500">{expanded ? '▼' : '▶'}</div>
      </div>

      {expanded && (
        <div className="mt-4 ml-7 space-y-2 text-sm">
          <div>
            <span className="text-slate-500">Hidden text:</span>
            <p className="text-slate-300 bg-slate-900 p-2 rounded mt-1 font-mono text-xs">
              {finding.hidden_text}
            </p>
          </div>
          <div>
            <span className="text-slate-500">Decoded:</span>
            <p className="text-emerald-300 bg-slate-900 p-2 rounded mt-1">
              {finding.decoded_text}
            </p>
          </div>
          <p className="text-amber-300">{finding.recommendation}</p>
        </div>
      )}
    </div>
  );
}

function getRiskBg(level: string): string {
  switch (level) {
    case 'CRITICAL': return 'bg-red-900/50 border border-red-500';
    case 'HIGH': return 'bg-orange-900/50 border border-orange-500';
    case 'MEDIUM': return 'bg-yellow-900/50 border border-yellow-500';
    case 'LOW': return 'bg-blue-900/50 border border-blue-500';
    default: return 'bg-emerald-900/50 border border-emerald-500';
  }
}

function getRiskColor(level: string): string {
  switch (level) {
    case 'CRITICAL': return 'text-red-400';
    case 'HIGH': return 'text-orange-400';
    case 'MEDIUM': return 'text-yellow-400';
    case 'LOW': return 'text-blue-400';
    default: return 'text-emerald-400';
  }
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

function getImpactBadge(impact: string): string {
  switch (impact) {
    case 'critical': return 'bg-red-500/30 text-red-300';
    case 'high': return 'bg-orange-500/30 text-orange-300';
    case 'medium': return 'bg-yellow-500/30 text-yellow-300';
    case 'low': return 'bg-blue-500/30 text-blue-300';
    default: return 'bg-slate-500/30 text-slate-300';
  }
}

export default App;
