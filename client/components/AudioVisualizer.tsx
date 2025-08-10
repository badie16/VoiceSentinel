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

    // Set canvas size
    const rect = canvas.getBoundingClientRect()
    canvas.width = rect.width * window.devicePixelRatio
    canvas.height = rect.height * window.devicePixelRatio
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio)

    const draw = () => {
      const width = rect.width
      const height = rect.height

      // Clear canvas
      ctx.clearRect(0, 0, width, height)

      if (isActive) {
        // Draw waveform visualization
        const centerY = height / 2
        const barCount = 32
        const barWidth = width / barCount
        const maxBarHeight = height * 0.8

        for (let i = 0; i < barCount; i++) {
          const x = i * barWidth

          // Create more realistic frequency simulation
          const frequency = i / barCount
          const baseHeight = audioLevel * maxBarHeight
          const variation = Math.sin(Date.now() * 0.01 + i * 0.5) * 0.3
          const barHeight = Math.max(2, baseHeight * (0.7 + variation))

          // Color based on audio level and frequency
          const hue = isActive ? Math.max(0, 120 - audioLevel * 120) : 120 // Green to red
          const saturation = 70 + audioLevel * 20
          const lightness = 40 + audioLevel * 30

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
        ctx.moveTo(10, centerY)
        ctx.lineTo(width - 10, centerY)
        ctx.stroke()

        // Draw microphone icon placeholder
        ctx.fillStyle = "#ccc"
        ctx.font = "16px Arial"
        ctx.textAlign = "center"
        ctx.fillText("🎤", width / 2, centerY - 20)
        ctx.fillText("Ready to listen", width / 2, centerY + 20)
      }

      if (isActive) {
        animationFrameRef.current = requestAnimationFrame(draw)
      }
    }

    draw()

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
    }
  }, [audioLevel, isActive])

  return (
    <canvas
      ref={canvasRef}
      className={`border rounded-lg bg-gray-50 ${className}`}
      style={{ width: "100%", height: "100px" }}
    />
  )
}
