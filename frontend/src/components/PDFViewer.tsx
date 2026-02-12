import { useState, useRef } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { useFindingStore, type ManualFinding } from '../store/findingStore';
import ResizableBox from './ResizableBox';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs';

interface PDFViewerProps {
    fileUrl: string;
    isDrawingMode?: boolean;
    onDrawingComplete?: () => void;
    editingFindingId?: string | null;
    onEditComplete?: (id: string, updates: { x: number; y: number; width: number; height: number }) => void;
    onEditCancel?: () => void;
}

export default function PDFViewer({
    fileUrl,
    isDrawingMode = false,
    onDrawingComplete,
    editingFindingId = null,
    onEditComplete,
    onEditCancel
}: PDFViewerProps) {
    const [numPages, setNumPages] = useState<number>(0);
    const [scale, setScale] = useState<number>(1.2);
    const [isDrawing, setIsDrawing] = useState(false);
    const [drawStart, setDrawStart] = useState<{ x: number, y: number, pageNum: number } | null>(null);
    const [currentRect, setCurrentRect] = useState<{ x: number, y: number, width: number, height: number } | null>(null);
    const [tempCoords, setTempCoords] = useState<{ x: number; y: number; width: number; height: number } | null>(null);
    const pageRefs = useRef<Map<number, HTMLDivElement>>(new Map());

    const { findings, manualFindings, isIgnored, toggleIgnored, hoveredFindingId, setHoveredFinding, addManualFinding } = useFindingStore();

    function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
        setNumPages(numPages);
    }

    // Helper: Convert screen coordinates to PDF coordinates
    function screenToPDFCoords(screenX: number, screenY: number, pageNum: number) {
        const pageDiv = pageRefs.current.get(pageNum);
        if (!pageDiv) return null;

        const rect = pageDiv.getBoundingClientRect();
        const pdfX = (screenX - rect.left) / scale;
        const pdfY = (screenY - rect.top) / scale;

        return { x: pdfX, y: pdfY };
    }

    // Mouse handlers for drawing
    function handleMouseDown(e: React.MouseEvent, pageNum: number) {
        if (!isDrawingMode) return;
        e.preventDefault();
        e.stopPropagation();

        const coords = screenToPDFCoords(e.clientX, e.clientY, pageNum);
        if (coords) {
            setDrawStart({ x: coords.x, y: coords.y, pageNum });
            setIsDrawing(true);
        }
    }

    function handleMouseMove(e: React.MouseEvent, pageNum: number) {
        if (!isDrawing || !drawStart || drawStart.pageNum !== pageNum) return;
        e.preventDefault();

        const coords = screenToPDFCoords(e.clientX, e.clientY, pageNum);
        if (coords) {
            const x = Math.min(drawStart.x, coords.x);
            const y = Math.min(drawStart.y, coords.y);
            const width = Math.abs(coords.x - drawStart.x);
            const height = Math.abs(coords.y - drawStart.y);

            setCurrentRect({ x, y, width, height });
        }
    }

    function handleMouseUp() {
        if (isDrawing && drawStart && currentRect && currentRect.width > 10 && currentRect.height > 10) {
            // Create manual finding
            const manualFinding: ManualFinding = {
                id: `manual-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                type: 'manual',
                page: drawStart.pageNum,
                x: currentRect.x,
                y: currentRect.y,
                width: currentRect.width,
                height: currentRect.height,
            };

            addManualFinding(manualFinding);
            onDrawingComplete?.();
        }

        // Reset drawing state
        setIsDrawing(false);
        setDrawStart(null);
        setCurrentRect(null);
    }

    return (
        <div
            className="flex flex-col items-center bg-slate-900/50 p-4 rounded-xl min-h-[600px]"
            style={{ cursor: isDrawingMode ? 'crosshair' : 'default' }}
        >
            <div className="flex gap-4 mb-4 sticky top-0 z-10 bg-slate-800 p-2 rounded-lg shadow-lg">
                <button onClick={() => setScale(s => Math.max(0.5, s - 0.1))} className="px-3 py-1 bg-slate-700 rounded hover:bg-slate-600">-</button>
                <span className="text-white font-mono self-center">{(scale * 100).toFixed(0)}%</span>
                <button onClick={() => setScale(s => Math.min(3.0, s + 0.1))} className="px-3 py-1 bg-slate-700 rounded hover:bg-slate-600">+</button>
            </div>

            <Document
                file={fileUrl}
                onLoadSuccess={onDocumentLoadSuccess}
                loading={<div className="text-emerald-400 animate-pulse">Loading PDF...</div>}
                error={<div className="text-red-400">Failed to load PDF. Please try again.</div>}
                className="shadow-2xl"
            >
                {Array.from(new Array(numPages), (_, index) => (
                    <div
                        key={`page_${index + 1}`}
                        className="mb-4 relative"
                        ref={(el) => {
                            if (el) pageRefs.current.set(index + 1, el);
                        }}
                        onMouseDown={(e) => handleMouseDown(e, index + 1)}
                        onMouseMove={(e) => handleMouseMove(e, index + 1)}
                        onMouseUp={handleMouseUp}
                        onMouseLeave={handleMouseUp}
                    >
                        <Page
                            pageNumber={index + 1}
                            scale={scale}
                            renderTextLayer={false}
                            renderAnnotationLayer={false}
                            className="border border-slate-700"
                        />

                        {/* Findings Overlay */}
                        <div className="absolute inset-0 pointer-events-none">
                            {findings
                                .filter(f => f.page === index + 1)
                                .map((finding) => {
                                    const ignored = isIgnored(finding.id);
                                    const isHovered = hoveredFindingId === finding.id;
                                    const findingNumber = findings.indexOf(finding) + 1;

                                    const w = finding.width || 100;
                                    const h = finding.height || 20;

                                    return (
                                        <div
                                            key={finding.id}
                                            style={{
                                                position: 'absolute',
                                                left: (finding.x || 0) * scale,
                                                top: (finding.y || 0) * scale,
                                                width: w * scale,
                                                height: h * scale,
                                            }}
                                            className={`
                                                pointer-events-auto cursor-pointer transition-all duration-200
                                                border-2 rounded-sm relative
                                                ${ignored
                                                    ? 'border-slate-500 bg-slate-500/20 opacity-50'
                                                    : isHovered
                                                        ? 'border-yellow-400 bg-yellow-500/40 ring-2 ring-yellow-400'
                                                        : 'border-red-500 bg-red-500/20 hover:bg-red-500/40'
                                                }
                                            `}
                                            onClick={() => toggleIgnored(finding.id)}
                                            onMouseEnter={() => setHoveredFinding(finding.id)}
                                            onMouseLeave={() => setHoveredFinding(null)}
                                            title={`Finding #${findingNumber}: ${finding.explanation}`}
                                        >
                                            {/* Finding Number Badge */}
                                            <div className={`
                                                absolute -top-7 -left-1 
                                                ${ignored ? 'bg-slate-600' : 'bg-red-600'} 
                                                text-white text-xs font-bold px-2 py-1 rounded shadow-lg
                                                flex items-center gap-1
                                            `}>
                                                <span>#{findingNumber}</span>
                                                {ignored && <span className="text-[10px]">✓ Keep</span>}
                                            </div>
                                        </div>
                                    );
                                })}

                            {/* Manual Findings Overlay */}
                            {manualFindings.filter(f => f.page === index + 1)
                                .map((finding) => {
                                    const ignored = isIgnored(finding.id);
                                    const isHovered = hoveredFindingId === finding.id;
                                    const findingNumber = findings.length + manualFindings.indexOf(finding) + 1;

                                    return (
                                        <div
                                            key={finding.id}
                                            style={{
                                                position: 'absolute',
                                                left: finding.x * scale,
                                                top: finding.y * scale,
                                                width: finding.width * scale,
                                                height: finding.height * scale,
                                            }}
                                            className={`
                                                pointer-events-auto cursor-pointer transition-all duration-200
                                                border-2 rounded-sm relative
                                                ${ignored
                                                    ? 'border-slate-500 bg-slate-500/20 opacity-50'
                                                    : isHovered
                                                        ? 'border-yellow-400 bg-yellow-500/40 ring-2 ring-yellow-400'
                                                        : 'border-blue-500 bg-blue-500/20 hover:bg-blue-500/40'
                                                }
                                            `}
                                            onClick={() => toggleIgnored(finding.id)}
                                            onMouseEnter={() => setHoveredFinding(finding.id)}
                                            onMouseLeave={() => setHoveredFinding(null)}
                                            title={`Manual Selection #${findingNumber}`}
                                        >
                                            <div className={`
                                                absolute -top-7 -left-1 
                                                ${ignored ? 'bg-slate-600' : 'bg-blue-600'} 
                                                text-white text-xs font-bold px-2 py-1 rounded shadow-lg
                                                flex items-center gap-1
                                            `}>
                                                <span>#{findingNumber} 📍</span>
                                                {ignored && <span className="text-[10px]">✓ Keep</span>}
                                            </div>
                                        </div>
                                    );
                                })}


                            {/* ResizableBox for editing */}
                            {editingFindingId && (() => {
                                // Find the editing finding (could be auto or manual)
                                const editingFinding = [...findings, ...manualFindings].find(f => f.id === editingFindingId);
                                if (!editingFinding) return null;

                                // Get coordinates
                                const coords = tempCoords || {
                                    x: 'x' in editingFinding ? editingFinding.x || 0 : 0,
                                    y: 'y' in editingFinding ? editingFinding.y || 0 : 0,
                                    width: 'width' in editingFinding ? editingFinding.width || 100 : 100,
                                    height: 'height' in editingFinding ? editingFinding.height || 20 : 20,
                                };

                                // Only render if on current page
                                const findingPage = 'page' in editingFinding ? editingFinding.page : index + 1;
                                if (findingPage !== index + 1) return null;

                                const pageElement = pageRefs.current.get(index + 1);
                                if (!pageElement) return null;

                                const pageRect = pageElement.getBoundingClientRect();

                                return (
                                    <ResizableBox
                                        x={coords.x}
                                        y={coords.y}
                                        width={coords.width}
                                        height={coords.height}
                                        page={index + 1}
                                        scale={scale}
                                        maxWidth={pageRect.width / scale}
                                        maxHeight={pageRect.height / scale}
                                        onUpdate={(updates) => setTempCoords(updates)}
                                        onSave={() => {
                                            if (tempCoords && onEditComplete) {
                                                onEditComplete(editingFindingId, tempCoords);
                                            }
                                            setTempCoords(null);
                                        }}
                                        onCancel={() => {
                                            setTempCoords(null);
                                            onEditCancel?.();
                                        }}
                                    />
                                );
                            })()}
                            {/* Current Drawing Rectangle */}
                            {isDrawing && drawStart && drawStart.pageNum === index + 1 && currentRect && (
                                <div
                                    style={{
                                        position: 'absolute',
                                        left: currentRect.x * scale,
                                        top: currentRect.y * scale,
                                        width: currentRect.width * scale,
                                        height: currentRect.height * scale,
                                    }}
                                    className="border-2 border-dashed border-blue-400 bg-blue-400/20 pointer-events-none"
                                />
                            )}
                        </div>
                    </div>
                ))}
            </Document>
        </div>
    );
}
