import { useState, useCallback } from 'react';
import { uploadDocument, getAnalysis, downloadSanitized, pollJobStatus } from './api';
import type { UploadResponse, AnalysisResponse } from './types';
import PDFViewer from './components/PDFViewer';
import Sidebar from './components/Sidebar';
import { useFindingStore } from './store/findingStore';

function App() {
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string>("");
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDrawingMode, setIsDrawingMode] = useState(false);
  const [editingFindingId, setEditingFindingId] = useState<string | null>(null);

  // Store actions
  const setFindings = useFindingStore(state => state.setFindings);
  const resetStore = useFindingStore(state => state.reset);
  const findings = useFindingStore(state => state.findings);
  const manualFindings = useFindingStore(state => state.manualFindings);
  const ignoredFindingIds = useFindingStore(state => state.ignoredFindingIds);
  const updateFinding = useFindingStore(state => state.updateFinding);
  const updateManualFinding = useFindingStore(state => state.updateManualFinding);

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

      // 2. Poll for completion
      setStatusMessage("Analyzing document (this may take a moment)...");
      await pollJobStatus(result.job_id);

      // 3. Get final results
      const analysisData = await getAnalysis(result.job_id);
      setAnalysis(analysisData);

      // Initialize Store
      setFindings(analysisData.findings);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
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

  // Construct PDF URL
  // In a real app we might need a signed URL or blob. 
  // For now, assume backend serves it or we can construct it if we had a /documents/{id}/content endpoint.
  // Wait, we don't have a direct "get content" endpoint in api.ts?
  // We accepted "file" in upload.
  // We can use the /jobs/{id}/sanitize endpoint to get content? No that redacts.
  // I need to add an endpoint to serve the ORIGINAL file or just use `URL.createObjectURL(file)` if we still have the file object?
  // We lost the file object in state.
  // But for the prototype, maybe we keep the file object in state or URL.createObjectURL right after upload?
  // Re-architecting slightly: keep the file object URL to render in Viewer.

  // FIX: Let's store the object URL when uploading.
  const [fileUrl, setFileUrl] = useState<string | null>(null);

  // Wrap handleFile to save URL
  const onFileSelect = (file: File) => {
    const url = URL.createObjectURL(file);
    setFileUrl(url);
    handleFile(file);
  };

  return (
    <div className="min-h-screen bg-slate-900 text-white flex flex-col">
      {/* Header */}
      <header className="border-b border-slate-700 bg-slate-900/50 backdrop-blur shrink-0 z-20">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold">
              <span className="text-emerald-400">Clarity</span>Check
            </h1>
            {analysis && (
              <span className={`px-3 py-1 rounded text-sm font-bold bg-slate-800 border border-slate-700`}>
                Score: {analysis.risk_score}
              </span>
            )}
          </div>
          {analysis && (
            <button onClick={resetState} className="text-slate-400 hover:text-white">New Scan</button>
          )}
        </div>
      </header>

      <main className="flex-1 overflow-hidden relative">
        {/* Upload Area */}
        {!analysis && (
          <div className="max-w-2xl mx-auto mt-20 px-6">
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
                    onChange={(e) => e.target.files?.[0] && onFileSelect(e.target.files[0])}
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
            {error && (
              <div className="mt-6 p-4 bg-red-500/20 border border-red-500 rounded-lg text-red-300 text-center">
                {error}
              </div>
            )}
          </div>
        )}

        {/* Interactive Workspace */}
        {analysis && uploadResult && fileUrl && (
          <div className="flex h-full">
            {/* Main Viewer Area */}
            <div className="flex-1 bg-slate-900/50 p-6 overflow-auto flex justify-center">
              <PDFViewer
                fileUrl={fileUrl}
                isDrawingMode={isDrawingMode}
                onDrawingComplete={() => setIsDrawingMode(false)}
                          editingFindingId={editingFindingId}
            onEditComplete={handleEditComplete}
            onEditCancel={() => setEditingFindingId(null)}
            />
            </div>

            {/* Sidebar */}
            <Sidebar
              onSanitize={handleSanitize}
              onStartDrawing={() => setIsDrawingMode(true)}
              onEditFinding={(finding) => setEditingFindingId(finding.id)}
            />
          </div>
        )}

        {/* Coordinate Editor Modal */}
      </main>
    </div>
  );
}

export default App;
