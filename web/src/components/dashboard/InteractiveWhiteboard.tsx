import React, { useRef, useState, useEffect, useCallback } from 'react'
import {
  Pencil,
  Highlighter,
  Eraser,
  Square,
  Circle as CircleIcon,
  Type,
  RotateCcw,
  Trash2,
  Download,
  Maximize2,
  Minimize2,
  Check,
} from 'lucide-react'
import { useApp } from '../../context/AppContext'

type ToolType = 'pencil' | 'highlighter' | 'eraser' | 'rectangle' | 'circle' | 'text'

const COLORS = ['#111111', '#1d5fd1', '#6c4ce0', '#ef4444', '#0f9d58', '#f59e0b', '#ffffff']
const STROKE_SIZES = [2, 4, 8, 14]

export function InteractiveWhiteboard() {
  const { addToast } = useApp()
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const [tool, setTool] = useState<ToolType>('pencil')
  const [color, setColor] = useState('#1d5fd1')
  const [lineWidth, setLineWidth] = useState(4)
  const [isDrawing, setIsDrawing] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [history, setHistory] = useState<ImageData[]>([])
  const [startPos, setStartPos] = useState<{ x: number; y: number } | null>(null)
  const [snapshot, setSnapshot] = useState<ImageData | null>(null)

  // Initialize canvas
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d', { willReadFrequently: true })
    if (!ctx) return

    // Set background to clean white
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    // Save initial state
    const initialData = ctx.getImageData(0, 0, canvas.width, canvas.height)
    setHistory([initialData])
  }, [])

  const saveState = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d', { willReadFrequently: true })
    if (!ctx) return
    const currentState = ctx.getImageData(0, 0, canvas.width, canvas.height)
    setHistory((prev) => [...prev.slice(-15), currentState])
  }, [])

  const undo = () => {
    if (history.length <= 1) {
      addToast('No more steps to undo', undefined, 'info')
      return
    }
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const newHistory = [...history]
    newHistory.pop() // remove current
    const previous = newHistory[newHistory.length - 1]
    ctx.putImageData(previous, 0, 0)
    setHistory(newHistory)
    addToast('Undo action applied', undefined, 'info')
  }

  const clearCanvas = () => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    saveState()
    addToast('Whiteboard Cleared', undefined, 'info')
  }

  const downloadCanvas = () => {
    const canvas = canvasRef.current
    if (!canvas) return
    const link = document.createElement('a')
    link.download = `skillsup-whiteboard-${Date.now()}.png`
    link.href = canvas.toDataURL('image/png')
    link.click()
    addToast('Saved to Computer!', 'Whiteboard snapshot downloaded as PNG.', 'success')
  }

  const getCanvasCoords = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    if (!canvas) return { x: 0, y: 0 }
    const rect = canvas.getBoundingClientRect()
    const scaleX = canvas.width / rect.width
    const scaleY = canvas.height / rect.height
    return {
      x: (e.clientX - rect.left) * scaleX,
      y: (e.clientY - rect.top) * scaleY,
    }
  }

  const startDraw = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const coords = getCanvasCoords(e)
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d', { willReadFrequently: true })
    if (!ctx) return

    setIsDrawing(true)
    setStartPos(coords)
    setSnapshot(ctx.getImageData(0, 0, canvas.width, canvas.height))

    if (tool === 'text') {
      const userText = prompt('Enter text note for whiteboard:')
      if (userText) {
        ctx.fillStyle = color
        ctx.font = `bold ${lineWidth * 4 + 14}px 'Poppins', sans-serif`
        ctx.fillText(userText, coords.x, coords.y)
        saveState()
      }
      setIsDrawing(false)
      return
    }

    ctx.beginPath()
    ctx.moveTo(coords.x, coords.y)
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'

    if (tool === 'eraser') {
      ctx.strokeStyle = '#ffffff'
      ctx.lineWidth = lineWidth * 3.5
      ctx.globalAlpha = 1.0
    } else if (tool === 'highlighter') {
      ctx.strokeStyle = color
      ctx.lineWidth = lineWidth * 3
      ctx.globalAlpha = 0.35
    } else {
      ctx.strokeStyle = color
      ctx.lineWidth = lineWidth
      ctx.globalAlpha = 1.0
    }
  }

  const draw = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d', { willReadFrequently: true })
    if (!ctx || !startPos) return

    const coords = getCanvasCoords(e)

    if (tool === 'pencil' || tool === 'eraser' || tool === 'highlighter') {
      ctx.lineTo(coords.x, coords.y)
      ctx.stroke()
    } else if (tool === 'rectangle' && snapshot) {
      ctx.putImageData(snapshot, 0, 0)
      ctx.globalAlpha = 1.0
      ctx.strokeStyle = color
      ctx.lineWidth = lineWidth
      ctx.strokeRect(startPos.x, startPos.y, coords.x - startPos.x, coords.y - startPos.y)
    } else if (tool === 'circle' && snapshot) {
      ctx.putImageData(snapshot, 0, 0)
      ctx.globalAlpha = 1.0
      ctx.strokeStyle = color
      ctx.lineWidth = lineWidth
      ctx.beginPath()
      const radius = Math.sqrt(Math.pow(coords.x - startPos.x, 2) + Math.pow(coords.y - startPos.y, 2))
      ctx.arc(startPos.x, startPos.y, radius, 0, 2 * Math.PI)
      ctx.stroke()
    }
  }

  const endDraw = () => {
    if (!isDrawing) return
    setIsDrawing(false)
    const canvas = canvasRef.current
    if (canvas) {
      const ctx = canvas.getContext('2d')
      if (ctx) ctx.globalAlpha = 1.0
    }
    saveState()
  }

  return (
    <div
      className={`relative flex flex-col font-mono transition-all duration-300 ${
        isFullscreen
          ? 'fixed inset-4 z-50 rounded-2xl bg-white p-4 shadow-2xl border-4 border-ink'
          : 'w-full'
      }`}
    >
      {/* Whiteboard Controls Toolbar (Neo-Brutalist) */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-2 border-ink bg-white p-2 shadow-[2px_2px_0_#0d1b3e]">
        {/* Color Palette */}
        <div className="flex items-center gap-1.5">
          {COLORS.map((c) => (
            <button
              key={c}
              onClick={() => {
                setColor(c)
                if (tool === 'eraser') setTool('pencil')
              }}
              aria-label={`Color ${c}`}
              className={`relative h-5 w-5 rounded-full border border-ink transition-transform hover:scale-110 ${
                color === c && tool !== 'eraser' ? 'ring-2 ring-brand ring-offset-1' : ''
              }`}
              style={{ backgroundColor: c }}
            >
              {color === c && tool !== 'eraser' && (
                <Check
                  className={`mx-auto h-3 w-3 ${c === '#ffffff' ? 'text-black' : 'text-white'}`}
                  strokeWidth={3}
                />
              )}
            </button>
          ))}
        </div>

        {/* Stroke width selector */}
        <div className="flex items-center gap-1 border-2 border-ink bg-paper px-1.5 py-0.5 text-xs text-gray-700">
          <span className="text-[10px] font-bold text-ink">PX:</span>
          {STROKE_SIZES.map((size) => (
            <button
              key={size}
              onClick={() => setLineWidth(size)}
              className={`flex h-5 w-5 items-center justify-center text-[10px] font-bold transition ${
                lineWidth === size
                  ? 'border border-ink bg-brand text-white shadow-xs'
                  : 'text-gray-500 hover:text-black'
              }`}
            >
              {size}
            </button>
          ))}
        </div>

        {/* Tool selector */}
        <div className="flex items-center gap-1">
          <button
            onClick={() => setTool('pencil')}
            title="Pencil"
            className={`flex h-7 w-7 items-center justify-center border transition-all ${
              tool === 'pencil'
                ? 'border-2 border-ink bg-brand text-white shadow-[1.5px_1.5px_0_#0d1b3e]'
                : 'border-transparent text-gray-600 hover:border-ink hover:bg-gray-100'
            }`}
          >
            <Pencil className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => setTool('highlighter')}
            title="Highlighter"
            className={`flex h-7 w-7 items-center justify-center border transition-all ${
              tool === 'highlighter'
                ? 'border-2 border-ink bg-brand text-white shadow-[1.5px_1.5px_0_#0d1b3e]'
                : 'border-transparent text-gray-600 hover:border-ink hover:bg-gray-100'
            }`}
          >
            <Highlighter className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => setTool('rectangle')}
            title="Rectangle"
            className={`flex h-7 w-7 items-center justify-center border transition-all ${
              tool === 'rectangle'
                ? 'border-2 border-ink bg-brand text-white shadow-[1.5px_1.5px_0_#0d1b3e]'
                : 'border-transparent text-gray-600 hover:border-ink hover:bg-gray-100'
            }`}
          >
            <Square className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => setTool('circle')}
            title="Circle"
            className={`flex h-7 w-7 items-center justify-center border transition-all ${
              tool === 'circle'
                ? 'border-2 border-ink bg-brand text-white shadow-[1.5px_1.5px_0_#0d1b3e]'
                : 'border-transparent text-gray-600 hover:border-ink hover:bg-gray-100'
            }`}
          >
            <CircleIcon className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => setTool('text')}
            title="Add Text"
            className={`flex h-7 w-7 items-center justify-center border transition-all ${
              tool === 'text'
                ? 'border-2 border-ink bg-accent text-white shadow-[1.5px_1.5px_0_#0d1b3e]'
                : 'border-transparent text-gray-600 hover:border-ink hover:bg-gray-100'
            }`}
          >
            <Type className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => setTool('eraser')}
            title="Eraser"
            className={`flex h-7 w-7 items-center justify-center border transition-all ${
              tool === 'eraser'
                ? 'border-2 border-ink bg-red-500 text-white shadow-[1.5px_1.5px_0_#0d1b3e]'
                : 'border-transparent text-gray-600 hover:border-ink hover:bg-gray-100'
            }`}
          >
            <Eraser className="h-3.5 w-3.5" />
          </button>
        </div>

        {/* Action icons */}
        <div className="flex items-center gap-1 border-l-2 border-ink/20 pl-2">
          <button
            onClick={undo}
            title="Undo"
            className="flex h-7 w-7 items-center justify-center border border-transparent text-gray-600 hover:border-ink hover:bg-gray-100"
          >
            <RotateCcw className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={clearCanvas}
            title="Clear Board"
            className="flex h-7 w-7 items-center justify-center border border-transparent text-gray-600 hover:border-ink hover:bg-red-50 hover:text-red-600"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={downloadCanvas}
            title="Save Snapshot (PNG)"
            className="flex h-7 w-7 items-center justify-center border border-ink bg-accent text-white shadow-[1.5px_1.5px_0_#0d1b3e] hover:bg-accent-dark"
          >
            <Download className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen Board'}
            className="flex h-7 w-7 items-center justify-center border border-transparent text-gray-600 hover:border-ink hover:bg-gray-100"
          >
            {isFullscreen ? <Minimize2 className="h-3.5 w-3.5" /> : <Maximize2 className="h-3.5 w-3.5" />}
          </button>
        </div>
      </div>

      {/* Canvas Drawing Surface */}
      <div
        className={`relative mt-2 overflow-hidden border-2 border-ink bg-white transition-all ${
          isFullscreen ? 'flex-1' : 'h-[230px] sm:h-[260px]'
        }`}
      >
        <div className="pointer-events-none absolute inset-0 opacity-15 [background-image:radial-gradient(#1d5fd1_1px,transparent_1px)] [background-size:16px_16px]" />
        
        <canvas
          ref={canvasRef}
          width={900}
          height={isFullscreen ? 750 : 360}
          onMouseDown={startDraw}
          onMouseMove={draw}
          onMouseUp={endDraw}
          onMouseLeave={endDraw}
          className="relative h-full w-full cursor-crosshair touch-none"
        />

        <div className="pointer-events-none absolute bottom-2 left-3 flex items-center gap-1.5 border border-ink bg-white/95 px-2 py-0.5 text-[9px] font-bold text-ink shadow-[1.5px_1.5px_0_#0d1b3e]">
          <span className="h-2 w-2 rounded-full bg-accent animate-pulse" />
          Vector Canvas Active · Draw shapes or text notes
        </div>
      </div>
    </div>
  )
}
