"use client"

import { useEffect, useRef } from "react"

interface AudioVisualizerProps {
  audioLevel: number
  isActive: boolean
  className?: string
}

export function AudioVisualizer({ audioLevel, isActive, className = "" }: AudioVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animationFrameRef = useRef<number | null>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext("2d")
    if (!ctx) return

    const draw = () => {
      const { width, height } = canvas

      // Clear canvas
      ctx.clearRect(0, 0, width, height)

      if (isActive) {
        // Draw waveform visualization
        const centerY = height / 2
        const barWidth = width / 32
        const maxBarHeight = height * 0.8

        for (let i = 0; i < 32; i++) {
          const x = i * barWidth

          // Simulate frequency data with some randomness
          const barHeight = (audioLevel + Math.random() * 0.3) * maxBarHeight

          // Color based on audio level
          const hue = isActive ? 120 - audioLevel * 120 : 120 // Green to red
          const saturation = 70
          const lightness = 50 + audioLevel * 30

          ctx.fillStyle = `hsl(${hue}, ${saturation}%, ${lightness}%)`
          ctx.fillRect(x, centerY - barHeight / 2, barWidth - 2, barHeight)
        }

        // Draw center line
        ctx.strokeStyle = "#666"
        ctx.lineWidth = 1
        ctx.beginPath()
        ctx.moveTo(0, centerY)
        ctx.lineTo(width, centerY)
        ctx.stroke()
      } else {
        // Draw inactive state
        const centerY = height / 2
        ctx.strokeStyle = "#ccc"
        ctx.lineWidth = 2
        ctx.beginPath()
        ctx.moveTo(0, centerY)
        ctx.lineTo(width, centerY)
        ctx.stroke()
      }

      animationFrameRef.current = requestAnimationFrame(draw)
    }

    draw()

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
    }
  }, [audioLevel, isActive])

  return <canvas ref={canvasRef} width={300} height={100} className={`border rounded-lg bg-gray-50 ${className}`} />
}
