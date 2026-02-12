import { useState, useRef, useEffect } from 'react';

interface ResizableBoxProps {
    x: number;
    y: number;
    width: number;
    height: number;
    page: number;
    scale: number;
    onUpdate: (updates: { x: number; y: number; width: number; height: number }) => void;
    onSave: () => void;
    onCancel: () => void;
    maxWidth: number;
    maxHeight: number;
}

type HandleType = 'nw' | 'n' | 'ne' | 'e' | 'se' | 's' | 'sw' | 'w' | 'move';

export default function ResizableBox({
    x, y, width, height, scale,
    onUpdate, onSave, onCancel, maxWidth, maxHeight
}: ResizableBoxProps) {
    const [isDragging, setIsDragging] = useState(false);
    const [dragHandle, setDragHandle] = useState<HandleType | null>(null);
    const dragStartRef = useRef<{ x: number; y: number; boxX: number; boxY: number; boxW: number; boxH: number } | null>(null);

    const handleSize = 10;

    const handleMouseDown = (e: React.MouseEvent, handle: HandleType) => {
        e.stopPropagation();
        setIsDragging(true);
        setDragHandle(handle);
        dragStartRef.current = {
            x: e.clientX,
            y: e.clientY,
            boxX: x,
            boxY: y,
            boxW: width,
            boxH: height
        };
    };

    useEffect(() => {
        if (!isDragging || !dragStartRef.current) return;

        const handleMouseMove = (e: MouseEvent) => {
            const start = dragStartRef.current!;
            const dx = (e.clientX - start.x) / scale;
            const dy = (e.clientY - start.y) / scale;

            let newX = start.boxX;
            let newY = start.boxY;
            let newWidth = start.boxW;
            let newHeight = start.boxH;

            switch (dragHandle) {
                case 'nw': // Top-left corner
                    newX = Math.max(0, Math.min(start.boxX + dx, start.boxX + start.boxW - 10));
                    newY = Math.max(0, Math.min(start.boxY + dy, start.boxY + start.boxH - 10));
                    newWidth = start.boxW - (newX - start.boxX);
                    newHeight = start.boxH - (newY - start.boxY);
                    break;
                case 'n': // Top edge
                    newY = Math.max(0, Math.min(start.boxY + dy, start.boxY + start.boxH - 10));
                    newHeight = start.boxH - (newY - start.boxY);
                    break;
                case 'ne': // Top-right corner
                    newY = Math.max(0, Math.min(start.boxY + dy, start.boxY + start.boxH - 10));
                    newWidth = Math.max(10, Math.min(start.boxW + dx, maxWidth - start.boxX));
                    newHeight = start.boxH - (newY - start.boxY);
                    break;
                case 'e': // Right edge
                    newWidth = Math.max(10, Math.min(start.boxW + dx, maxWidth - start.boxX));
                    break;
                case 'se': // Bottom-right corner
                    newWidth = Math.max(10, Math.min(start.boxW + dx, maxWidth - start.boxX));
                    newHeight = Math.max(10, Math.min(start.boxH + dy, maxHeight - start.boxY));
                    break;
                case 's': // Bottom edge
                    newHeight = Math.max(10, Math.min(start.boxH + dy, maxHeight - start.boxY));
                    break;
                case 'sw': // Bottom-left corner
                    newX = Math.max(0, Math.min(start.boxX + dx, start.boxX + start.boxW - 10));
                    newWidth = start.boxW - (newX - start.boxX);
                    newHeight = Math.max(10, Math.min(start.boxH + dy, maxHeight - start.boxY));
                    break;
                case 'w': // Left edge
                    newX = Math.max(0, Math.min(start.boxX + dx, start.boxX + start.boxW - 10));
                    newWidth = start.boxW - (newX - start.boxX);
                    break;
                case 'move': // Move entire box
                    newX = Math.max(0, Math.min(start.boxX + dx, maxWidth - start.boxW));
                    newY = Math.max(0, Math.min(start.boxY + dy, maxHeight - start.boxH));
                    break;
            }

            onUpdate({ x: newX, y: newY, width: newWidth, height: newHeight });
        };

        const handleMouseUp = () => {
            setIsDragging(false);
            setDragHandle(null);
            dragStartRef.current = null;
        };

        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);

        return () => {
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };
    }, [isDragging, dragHandle, scale, maxWidth, maxHeight, onUpdate]);

    // Keyboard shortcuts
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                onCancel();
            } else if (e.key === 'Enter') {
                onSave();
            }
        };

        document.addEventListener('keydown', handleKeyDown);
        return () => document.removeEventListener('keydown', handleKeyDown);
    }, [onCancel, onSave]);

    const getCursor = (handle: HandleType): string => {
        const cursors = {
            'nw': 'nw-resize',
            'n': 'n-resize',
            'ne': 'ne-resize',
            'e': 'e-resize',
            'se': 'se-resize',
            's': 's-resize',
            'sw': 'sw-resize',
            'w': 'w-resize',
            'move': 'move'
        };
        return cursors[handle];
    };

    return (
        <div
            style={{
                position: 'absolute',
                left: x * scale,
                top: y * scale,
                width: width * scale,
                height: height * scale,
                pointerEvents: 'all',
                zIndex: 1000,
            }}
        >
            {/* Main box */}
            <div
                className="absolute inset-0 border-4 border-blue-500 bg-blue-500/10 cursor-move"
                onMouseDown={(e) => handleMouseDown(e, 'move')}
            />

            {/* Corner handles */}
            {(['nw', 'ne', 'se', 'sw'] as const).map((handle) => (
                <div
                    key={handle}
                    className="absolute w-3 h-3 bg-white border-2 border-blue-600 rounded-full hover:bg-blue-600 transition-colors"
                    style={{
                        cursor: getCursor(handle),
                        ...(handle === 'nw' && { left: -handleSize / 2, top: -handleSize / 2 }),
                        ...(handle === 'ne' && { right: -handleSize / 2, top: -handleSize / 2 }),
                        ...(handle === 'se' && { right: -handleSize / 2, bottom: -handleSize / 2 }),
                        ...(handle === 'sw' && { left: -handleSize / 2, bottom: -handleSize / 2 }),
                    }}
                    onMouseDown={(e) => handleMouseDown(e, handle)}
                />
            ))}

            {/* Edge handles */}
            {(['n', 'e', 's', 'w'] as const).map((handle) => (
                <div
                    key={handle}
                    className="absolute w-3 h-3 bg-white border-2 border-blue-600 rounded-full hover:bg-blue-600 transition-colors"
                    style={{
                        cursor: getCursor(handle),
                        ...(handle === 'n' && { left: '50%', top: -handleSize / 2, transform: 'translateX(-50%)' }),
                        ...(handle === 'e' && { right: -handleSize / 2, top: '50%', transform: 'translateY(-50%)' }),
                        ...(handle === 's' && { left: '50%', bottom: -handleSize / 2, transform: 'translateX(-50%)' }),
                        ...(handle === 'w' && { left: -handleSize / 2, top: '50%', transform: 'translateY(-50%)' }),
                    }}
                    onMouseDown={(e) => handleMouseDown(e, handle)}
                />
            ))}

            {/* Floating toolbar */}
            <div
                className="absolute top-0 flex flex-col gap-2 bg-slate-800 rounded-lg p-2 shadow-lg border border-slate-700"
                style={{ pointerEvents: 'all', left: '100%', marginLeft: '8px' }}
            >
                <button
                    onClick={onSave}
                    className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white rounded text-sm font-medium transition-colors"
                >
                    ✓ Save
                </button>
                <button
                    onClick={onCancel}
                    className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-sm font-medium transition-colors"
                >
                    ✗ Cancel
                </button>
                <div className="px-2 py-1 text-xs text-slate-400 border-l border-slate-600">
                    {Math.round(width)} × {Math.round(height)}
                </div>
            </div>
        </div>
    );
}
