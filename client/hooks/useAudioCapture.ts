"use client"

import { useState, useRef, useCallback, useEffect } from "react"

interface AudioCaptureConfig {
  sampleRate: number
  channelCount: number
  echoCancellation: boolean
  noiseSuppression: boolean
}

interface AudioCaptureHook {
  isRecording: boolean
  audioLevel: number
  startRecording: () => Promise<void>
  stopRecording: () => void
  error: string | null
}

const defaultConfig: AudioCaptureConfig = {
  sampleRate: 16000,
  channelCount: 1,
  echoCancellation: true,
  noiseSuppression: true,
}

export function useAudioCapture(
  onAudioData: (audioData: string) => void,
  config: Partial<AudioCaptureConfig> = {},
): AudioCaptureHook {
  const [isRecording, setIsRecording] = useState(false)
  const [audioLevel, setAudioLevel] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const animationFrameRef = useRef<number | null>(null)

  const finalConfig = { ...defaultConfig, ...config }

  const startRecording = useCallback(async () => {
    try {
      setError(null)

      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: finalConfig.sampleRate,
          channelCount: finalConfig.channelCount,
          echoCancellation: finalConfig.echoCancellation,
          noiseSuppression: finalConfig.noiseSuppression,
        },
      })

      streamRef.current = stream

      // Create audio context for analysis
      audioContextRef.current = new AudioContext({
        sampleRate: finalConfig.sampleRate,
      })

      const source = audioContextRef.current.createMediaStreamSource(stream)
      analyserRef.current = audioContextRef.current.createAnalyser()
      analyserRef.current.fftSize = 256

      source.connect(analyserRef.current)

      // Start audio level monitoring
      const monitorAudioLevel = () => {
        if (analyserRef.current) {
          const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount)
          analyserRef.current.getByteFrequencyData(dataArray)

          const average = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length
          setAudioLevel(average / 255) // Normalize to 0-1

          animationFrameRef.current = requestAnimationFrame(monitorAudioLevel)
        }
      }

      monitorAudioLevel()

      // Create MediaRecorder for audio capture
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: "audio/webm;codecs=opus",
      })

      mediaRecorderRef.current = mediaRecorder

      // Handle audio data
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          // Convert blob to base64
          const reader = new FileReader()
          reader.onloadend = () => {
            const base64Data = reader.result as string
            const audioData = base64Data.split(",")[1] // Remove data URL prefix
            onAudioData(audioData)
          }
          reader.readAsDataURL(event.data)
        }
      }

      // Start recording with time slices
      mediaRecorder.start(1000) // Send data every 1 second
      setIsRecording(true)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to start recording"
      setError(errorMessage)
      console.error("Audio capture error:", err)
    }
  }, [onAudioData])

  const stopRecording = useCallback(() => {
    try {
      // Stop MediaRecorder
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
        mediaRecorderRef.current.stop()
      }

      // Stop audio level monitoring
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
        animationFrameRef.current = null
      }

      // Close audio context
      if (audioContextRef.current) {
        audioContextRef.current.close()
        audioContextRef.current = null
      }

      // Stop media stream
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop())
        streamRef.current = null
      }

      setIsRecording(false)
      setAudioLevel(0)
    } catch (err) {
      console.error("Error stopping recording:", err)
    }
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopRecording()
    }
  }, [stopRecording])

  return {
    isRecording,
    audioLevel,
    startRecording,
    stopRecording,
    error,
  }
}
