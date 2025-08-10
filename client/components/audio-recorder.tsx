"use client"

import { useState, useRef, useEffect, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Mic, StopCircle, Wifi, AlertTriangle, CheckCircle, XCircle, FileText, UserCheck } from "lucide-react" 

const WEBSOCKET_URL = "ws://localhost:8000/ws" // Adjust if your backend runs on a different host/port
const REPORT_URL = "http://localhost:8000/generate-report" // Endpoint for incident report

export function AudioRecorder() {
  const [isRecording, setIsRecording] = useState(false)
  const [wsConnected, setWsConnected] = useState(false)
  const [analysisResults, setAnalysisResults] = useState<any[]>([]) // State to store analysis results
  const [report, setReport] = useState<any | null>(null) // State to store incident report
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)

  const connectWebSocket = useCallback(() => {
    const ws = new WebSocket(WEBSOCKET_URL)
    wsRef.current = ws

    ws.onopen = () => {
      console.log("WebSocket connected")
      setWsConnected(true)
      setReport(null) // Clear report on new connection
    }

    ws.onmessage = async (event) => {
      // console.log("Message from server:", event.data)
      if (typeof event.data === "string") {
        try {
          const data = JSON.parse(event.data)
          if (data.type === "analysis_result") {
            setAnalysisResults((prev) => [...prev, data.data])
          }
        } catch (e) {
          console.error("Failed to parse WebSocket message:", e)
        }
      } else if (event.data instanceof Blob) {
        // Handle binary data (TTS audio alerts)
        const reader = new FileReader()
        reader.onload = async () => {
          const arrayBuffer = reader.result as ArrayBuffer
          const audioBytes = new Uint8Array(arrayBuffer)

          // Check for start/end markers for alert audio
          const startMarker = new TextEncoder().encode("ALERT_AUDIO_START")
          const endMarker = new TextEncoder().encode("ALERT_AUDIO_END")

          const startIndex = findBytes(audioBytes, startMarker)
          const endIndex = findBytes(audioBytes, endMarker, startIndex + startMarker.length)

          if (startIndex !== -1 && endIndex !== -1) {
            const alertAudioData = audioBytes.slice(startIndex + startMarker.length, endIndex)
            console.log("Received TTS alert audio blob.")
            if (!audioContextRef.current) {
              audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)()
            }
            try {
              const audioBuffer = await audioContextRef.current.decodeAudioData(alertAudioData.buffer)
              const source = audioContextRef.current.createBufferSource()
              source.buffer = audioBuffer
              source.connect(audioContextRef.current.destination)
              source.start(0)
              console.log("Playing TTS alert.")
            } catch (e) {
              console.error("Error decoding or playing alert audio:", e)
            }
          }
        }
        reader.readAsArrayBuffer(event.data)
      }
    }

    ws.onclose = () => {
      console.log("WebSocket disconnected")
      setWsConnected(false)
      // Attempt to reconnect after a delay if disconnected
      setTimeout(() => {
        console.log("Attempting to reconnect WebSocket...")
        connectWebSocket()
      }, 3000)
    }

    ws.onerror = (error) => {
      console.error("WebSocket error:", error)
      setWsConnected(false)
    }

    return () => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close()
      }
    }
  }, [])

  useEffect(() => {
    connectWebSocket()
    return () => {
      if (audioContextRef.current) {
        audioContextRef.current.close()
      }
    }
  }, [connectWebSocket])

  const startRecording = async () => {
    if (!wsConnected) {
      console.error("WebSocket not connected. Cannot start recording.")
      return
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      // Use audio/webm for efficient capture, then convert to WAV for server
      mediaRecorderRef.current = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" })

      mediaRecorderRef.current.ondataavailable = async (event) => {
        if (event.data.size > 0) {
          // Convert WebM Blob to WAV Blob
          if (!audioContextRef.current) {
            audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)()
          }
          const arrayBuffer = await event.data.arrayBuffer()
          const audioBuffer = await audioContextRef.current.decodeAudioData(arrayBuffer)

          // Convert AudioBuffer to WAV Blob (mono, 16-bit PCM)
          const wavBlob = audioBufferToWav(audioBuffer)

          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(wavBlob)
          }
        }
      }

      mediaRecorderRef.current.onstop = () => {
        console.log("Recording stopped.")
      }

      mediaRecorderRef.current.start(1000) // Record in 1-second chunks
      setIsRecording(true)
      setAnalysisResults([]) // Clear previous results
      setReport(null) // Clear previous report
      console.log("Recording started...")
    } catch (err) {
      console.error("Error accessing microphone:", err)
      alert("Please allow microphone access to start recording.")
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      console.log("Stopping recording...")
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
    }
  }

  const generateReport = async () => {
    try {
      const response = await fetch(REPORT_URL)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const reportData = await response.json()
      setReport(reportData)
      console.log("Incident Report:", reportData)
    } catch (error) {
      console.error("Error generating report:", error)
      alert("Failed to generate report. See console for details.")
    }
  }

  // Helper function to convert AudioBuffer to WAV Blob (mono, 16-bit PCM)
  const audioBufferToWav = (audioBuffer: AudioBuffer) => {
    const ambuf = audioBuffer.getChannelData(0) // Get mono channel
    const len = ambuf.length
    const buf = new ArrayBuffer(44 + len * 2) // 44 bytes for WAV header, 2 bytes per sample (16-bit)
    const view = new DataView(buf)

    function writeString(view: DataView, offset: number, s: string) {
      for (let i = 0; i < s.length; i++) {
        view.setUint8(offset + i, s.charCodeAt(i))
      }
    }

    let p = 0
    writeString(view, p, "RIFF")
    p += 4
    view.setUint32(p, 36 + len * 2, true) // File size - 8
    p += 4
    writeString(view, p, "WAVE")
    p += 4
    writeString(view, p, "fmt ")
    p += 4
    view.setUint32(p, 16, true) // Subchunk1Size (16 for PCM)
    p += 4
    view.setUint16(p, 1, true) // AudioFormat (1 for PCM)
    p += 2
    view.setUint16(p, 1, true) // NumChannels (1 for mono)
    p += 2
    view.setUint32(p, audioBuffer.sampleRate, true) // SampleRate
    p += 4
    view.setUint32(p, audioBuffer.sampleRate * 2, true) // ByteRate (SampleRate * NumChannels * BitsPerSample/8)
    p += 4
    view.setUint16(p, 2, true) // BlockAlign (NumChannels * BitsPerSample/8)
    p += 2
    view.setUint16(p, 16, true) // BitsPerSample
    p += 2
    writeString(view, p, "data")
    p += 4
    view.setUint32(p, len * 2, true) // Subchunk2Size (NumSamples * NumChannels * BitsPerSample/8)
    p += 4

    // Write audio data (16-bit PCM)
    for (let i = 0; i < len; i++) {
      let s = Math.max(-1, Math.min(1, ambuf[i]))
      s = s < 0 ? s * 0x8000 : s * 0x7fff // Convert to 16-bit integer
      view.setInt16(p, s, true)
      p += 2
    }

    return new Blob([view], { type: "audio/wav" })
  }

  // Helper to find byte sequence in Uint8Array
  const findBytes = (haystack: Uint8Array, needle: Uint8Array, offset = 0) => {
    for (let i = offset; i <= haystack.length - needle.length; i++) {
      let found = true
      for (let j = 0; j < needle.length; j++) {
        if (haystack[i + j] !== needle[j]) {
          found = false
          break
        }
      }
      if (found) return i
    }
    return -1
  }

  const getScamLabelColor = (label: string) => {
    switch (label) {
      case "Scam":
        return "text-red-500"
      case "Suspicious":
        return "text-yellow-500"
      case "Safe":
        return "text-green-500"
      case "Error":
        return "text-gray-500"
      default:
        return "text-gray-500"
    }
  }

  const getScamLabelIcon = (label: string) => {
    switch (label) {
      case "Scam":
        return <XCircle className="h-4 w-4" />
      case "Suspicious":
        return <AlertTriangle className="h-4 w-4" />
      case "Safe":
        return <CheckCircle className="h-4 w-4" />
      default:
        return null
    }
  }

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          Voice Scam Shield
          <span className={`flex items-center gap-1 text-sm ${wsConnected ? "text-green-500" : "text-red-500"}`}>
            <Wifi className="mr-1 h-4 w-4" /> {wsConnected ? "Connecté" : "Déconnecté"}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col items-center gap-4">
        {isRecording ? (
          <Button onClick={stopRecording} className="w-full py-3 text-lg" variant="destructive">
            <StopCircle className="mr-2 h-5 w-5" /> Arrêter l'enregistrement
          </Button>
        ) : (
          <Button onClick={startRecording} className="w-full py-3 text-lg" disabled={!wsConnected}>
            <Mic className="mr-2 h-5 w-5" /> Démarrer l'enregistrement
          </Button>
        )}
        {!wsConnected && (
          <p className="text-sm text-red-500">
            Impossible de se connecter au backend. Assurez-vous que le serveur Python est en cours d'exécution.
          </p>
        )}

        <Button
          onClick={generateReport}
          className="w-full py-3 text-lg mt-4 bg-transparent"
          variant="outline"
          disabled={isRecording || analysisResults.length === 0}
        >
          <FileText className="mr-2 h-5 w-5" /> Générer le rapport d'incident
        </Button>

        {report && (
          <div className="w-full mt-4 border rounded-md p-4 bg-blue-50 dark:bg-blue-900/20">
            <h3 className="text-lg font-semibold mb-2 text-blue-800 dark:text-blue-200">Rapport d'incident</h3>
            <p className="text-sm text-gray-700 dark:text-gray-300">
              Durée de l'appel: {report.call_duration_seconds?.toFixed(1)}s
            </p>
            <p className="text-sm text-gray-700 dark:text-gray-300">
              Segments analysés: {report.total_segments_analyzed}
            </p>
            <p className="text-sm text-gray-700 dark:text-gray-300">Segments d'arnaque: {report.scam_segments_count}</p>
            <p className="text-sm text-gray-700 dark:text-gray-300">
              Segments suspects: {report.suspicious_segments_count}
            </p>
            <p className="text-sm font-medium mt-2 text-gray-800 dark:text-gray-200">{report.summary}</p>
            <p className="text-sm font-medium mt-2 text-gray-800 dark:text-gray-200">
              Étapes recommandées:
              <ul className="list-disc list-inside text-xs text-gray-700 dark:text-gray-300">
                {report.recommended_next_steps
                  .split("\n")
                  .filter(Boolean)
                  .map((step: string, i: number) => (
                    <li key={i}>{step.trim()}</li>
                  ))}
              </ul>
            </p>
            {report.flagged_segments.length > 0 && (
              <div className="mt-4">
                <h4 className="text-md font-semibold mb-1 text-blue-800 dark:text-blue-200">Segments signalés:</h4>
                <div className="space-y-1 max-h-40 overflow-y-auto pr-2">
                  {report.flagged_segments.map((segment: any, idx: number) => (
                    <div key={idx} className="border rounded-md p-2 bg-blue-100 dark:bg-blue-900/30">
                      <p className="text-xs font-medium flex items-center">
                        <span className={getScamLabelColor(segment.scam_detection.label)}>
                          {getScamLabelIcon(segment.scam_detection.label)}
                        </span>
                        <span className={`ml-1 ${getScamLabelColor(segment.scam_detection.label)}`}>
                          Statut: {segment.scam_detection.label}
                        </span>
                        <span className="ml-auto text-xs text-gray-600 dark:text-gray-400">
                          {segment.start_time?.toFixed(1)}s - {segment.end_time?.toFixed(1)}s
                        </span>
                      </p>
                      {segment.transcription?.text && (
                        <p className="text-xs text-gray-700 dark:text-gray-300 mt-0.5">
                          Transcription: "{segment.transcription.text}"
                        </p>
                      )}
                      {segment.scam_detection?.rationale && (
                        <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
                          Raison: {segment.scam_detection.rationale}
                        </p>
                      )}
                      {segment.anti_spoofing?.is_synthetic && (
                        <p className="text-xs text-orange-600 dark:text-orange-400 mt-0.5">
                          Voix synthétique détectée (Confiance: {segment.anti_spoofing.confidence?.toFixed(2)})
                        </p>
                      )}
                      {segment.caller_verification_matches &&
                        Object.keys(segment.caller_verification_matches).length > 0 && (
                          <p className="text-xs text-blue-600 dark:text-blue-400 mt-0.5 flex items-center">
                            <UserCheck className="h-3 w-3 mr-1" /> Vérifié:{" "}
                            {Object.entries(segment.caller_verification_matches)
                              .map(([name, score]) => `${name} (${((score as number) * 100).toFixed(0)}%)`)
                              .join(", ")}
                          </p>
                        )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        <div className="w-full mt-4">
          <h3 className="text-lg font-semibold mb-2">Résultats d'analyse en temps réel :</h3>
          {analysisResults.length === 0 && (
            <p className="text-gray-500 text-sm">Aucune analyse disponible. Démarrez l'enregistrement.</p>
          )}
          <div className="space-y-2 max-h-60 overflow-y-auto pr-2">
            {analysisResults.map((result, index) => (
              <div key={index} className="border rounded-md p-3 bg-gray-50 dark:bg-gray-800">
                <p className="text-sm font-medium flex items-center">
                  <span className={getScamLabelColor(result.scam_detection.label)}>
                    {getScamLabelIcon(result.scam_detection.label)}
                  </span>
                  <span className={`ml-2 ${getScamLabelColor(result.scam_detection.label)}`}>
                    Statut: {result.scam_detection.label}
                  </span>
                  <span className="ml-auto text-xs text-gray-500">
                    {result.start_time?.toFixed(1)}s - {result.end_time?.toFixed(1)}s
                  </span>
                </p>
                {result.transcription?.text && (
                  <p className="text-xs text-gray-700 dark:text-gray-300 mt-1">
                    Transcription: "{result.transcription.text}"
                  </p>
                )}
                {result.scam_detection?.rationale && (
                  <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                    Raison: {result.scam_detection.rationale}
                  </p>
                )}
                {result.anti_spoofing?.is_synthetic && (
                  <p className="text-xs text-orange-500 mt-1">
                    Voix synthétique détectée (Confiance: {result.anti_spoofing.confidence?.toFixed(2)})
                  </p>
                )}
                {result.caller_verification_matches && Object.keys(result.caller_verification_matches).length > 0 && (
                  <p className="text-xs text-blue-600 dark:text-blue-400 mt-1 flex items-center">
                    <UserCheck className="h-3 w-3 mr-1" /> Vérifié:{" "}
                    {Object.entries(result.caller_verification_matches)
                      .map(([name, score]) => `${name} (${((score as number) * 100).toFixed(0)}%)`)
                      .join(", ")}
                  </p>
                )}
                {result.alert_triggered && <p className="text-xs text-purple-500 mt-1">Alerte TTS déclenchée.</p>}
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
