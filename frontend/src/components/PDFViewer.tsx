import { useState } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { useFindingStore } from '../store/findingStore';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// Configure worker (should be handled by vite-plugin-static-copy, but explicit path helps)
// Actually, with vite-plugin-static-copy, it is at root.
pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs';

interface PDFViewerProps {
    fileUrl: string;
}

export default function PDFViewer({ fileUrl }: PDFViewerProps) {
    const [numPages, setNumPages] = useState<number>(0);
    const [scale, setScale] = useState<number>(1.2); // Default zoom
    const { findings, isIgnored, toggleIgnored } = useFindingStore();

    function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
        setNumPages(numPages);
    }

    return (
        <div className="flex flex-col items-center bg-slate-900/50 p-4 rounded-xl min-h-[600px]">
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
                    <div key={`page_${index + 1}`} className="mb-4 relative group">
                        <Page
                            pageNumber={index + 1}
                            scale={scale}
                            renderTextLayer={false} // Disable text selection for cleaner UI? Or keep it? keeping it for now.
                            renderAnnotationLayer={false}
                            className="border border-slate-700"
                        />

                        {/* Findings Overlay */}
                        <div className="absolute inset-0 pointer-events-none">
                            {findings
                                .filter(f => f.page === index + 1)
                                .map(finding => {
                                    const ignored = isIgnored(finding.id);

                                    // Default width/height if not present (fallback for older findings)
                                    // This shouldn't happen with new backend code.
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
                                                border-2 rounded-sm
                                                ${ignored
                                                    ? 'border-slate-500 bg-slate-500/20 opacity-50 grayscale'
                                                    : 'border-red-500 bg-red-500/20 animate-pulse hover:bg-red-500/40'
                                                }
                                            `}
                                            onClick={() => toggleIgnored(finding.id)}
                                            title={`${finding.trap_type}: ${finding.explanation}`}
                                        >
                                            {!ignored && (
                                                <span className="absolute -top-6 left-0 bg-red-600 text-white text-[10px] px-1 rounded shadow whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity">
                                                    {finding.trap_type}
                                                </span>
                                            )}
                                        </div>
                                    );
                                })}
                        </div>
                    </div>
                ))}
            </Document>
        </div>
    );
}
