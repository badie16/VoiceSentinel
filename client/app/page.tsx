"use client"

import { useState, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { AudioVisualizer } from "@/components/AudioVisualizer"
import { useAudioCapture } from "@/hooks/useAudioCapture"
import { useWebSocket } from "@/hooks/useWebSocket"
import { Play, Square, Mic, MicOff, Shield, AlertTriangle, CheckCircle, Volume2, VolumeX } from "lucide-react"

type RiskLevel = "safe" | "suspicious" | "scam"
type CallStatus = "idle" | "active" | "analyzing"

interface TranscriptSegment {
  id: string
  speaker: "user" | "caller"
  text: string
  timestamp: string
  riskLevel: RiskLevel
  confidence: number
}

interface AnalysisResult {
  type: string
  timestamp: string
  transcript: {
    text: string
    speaker: string
    language: string
    confidence: number
  }
  risk_assessment: {
    score: number
    level: RiskLevel
    scam_indicators: string[]
    voice_spoofing: boolean
    spoofing_confidence: number
  }
}

export default function LiveMonitor() {
  const [callStatus, setCallStatus] = useState<CallStatus>("idle")
  const [riskScore, setRiskScore] = useState(0)
  const [currentRiskLevel, setCurrentRiskLevel] = useState<RiskLevel>("safe")
  const [isAudioEnabled, setIsAudioEnabled] = useState(true)
  const [transcript, setTranscript] = useState<TranscriptSegment[]>([])

  // WebSocket connection
  const { isConnected, sendMessage, lastMessage } = useWebSocket(
    `ws://localhost:8000/ws/${Date.now()}`,
    handleWebSocketMessage,
  )

  // Audio capture
  const { isRecording, audioLevel, startRecording, stopRecording, error } = useAudioCapture(handleAudioData, {
    sampleRate: 16000,
    channelCount: 1,
    echoCancellation: true,
    noiseSuppression: true,
  })

  function handleWebSocketMessage(message: any) {
    console.log("Received message:", message)

    switch (message.type) {
      case "analysis_result":
        handleAnalysisResult(message as AnalysisResult)
        break
      case "audio_alert":
        if (isAudioEnabled) {
          playAudioAlert(message.audio_data)
        }
        break
      case "error":
        console.error("Server error:", message.message)
        break
    }
  }

  function handleAnalysisResult(result: AnalysisResult) {
    // Update transcript
    if (result.transcript.text.trim()) {
      const newSegment: TranscriptSegment = {
        id: Date.now().toString(),
        speaker: result.transcript.speaker === "user" ? "user" : "caller",
        text: result.transcript.text,
        timestamp: new Date(result.timestamp).toLocaleTimeString(),
        riskLevel: result.risk_assessment.level,
        confidence: result.transcript.confidence,
      }

      setTranscript((prev) => [...prev.slice(-10), newSegment])
    }

    // Update risk assessment
    setRiskScore(result.risk_assessment.score)
    setCurrentRiskLevel(result.risk_assessment.level)
  }

  function handleAudioData(audioData: string) {
    if (callStatus === "active" && isConnected) {
      sendMessage({
        type: "audio_chunk",
        data: audioData,
      })
    }
  }

  function playAudioAlert(audioData: string) {
    try {
      const audio = new Audio(`data:audio/mpeg;base64,${audioData}`)
      audio.volume = 0.5
      audio.play().catch(console.error)
    } catch (error) {
      console.error("Failed to play audio alert:", error)
    }
  }

  const startAnalysis = useCallback(async () => {
    try {
      setCallStatus("active")
      setTranscript([])
      setRiskScore(0)
      setCurrentRiskLevel("safe")

      // Start audio recording
      await startRecording()

      // Notify server
      if (isConnected) {
        sendMessage({ type: "start_analysis" })
      }
    } catch (error) {
      console.error("Failed to start analysis:", error)
      setCallStatus("idle")
    }
  }, [startRecording, isConnected, sendMessage])

  const stopAnalysis = useCallback(() => {
    setCallStatus("idle")
    stopRecording()

    // Notify server
    if (isConnected) {
      sendMessage({ type: "stop_analysis" })
    }
  }, [stopRecording, isConnected, sendMessage])

  const getRiskColor = (level: RiskLevel) => {
    switch (level) {
      case "safe":
        return "text-green-600 bg-green-50 border-green-200"
      case "suspicious":
        return "text-orange-600 bg-orange-50 border-orange-200"
      case "scam":
        return "text-red-600 bg-red-50 border-red-200"
    }
  }

  const getRiskIcon = (level: RiskLevel) => {
    switch (level) {
      case "safe":
        return <CheckCircle className="h-4 w-4" />
      case "suspicious":
        return <AlertTriangle className="h-4 w-4" />
      case "scam":
        return <Shield className="h-4 w-4" />
    }
  }

  return (
    <div className="flex-1 space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <SidebarTrigger />
          <div>
            <h1 className="text-3xl font-bold">Live Call Monitor</h1>
            <p className="text-muted-foreground">Real-time scam detection and voice analysis</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant={isConnected ? "default" : "destructive"}>{isConnected ? "Connected" : "Disconnected"}</Badge>
          <Button variant="outline" size="sm" onClick={() => setIsAudioEnabled(!isAudioEnabled)}>
            {isAudioEnabled ? <Volume2 className="h-4 w-4" /> : <VolumeX className="h-4 w-4" />}
            Audio Alerts
          </Button>
        </div>
      </div>

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <p className="text-red-600">Audio Error: {error}</p>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Risk Score Card */}
        <Card className="md:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Risk Assessment
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-center">
              <div className={`text-4xl font-bold ${getRiskColor(currentRiskLevel).split(" ")[0]}`}>
                {riskScore.toFixed(0)}%
              </div>
              <Badge className={getRiskColor(currentRiskLevel)}>
                {getRiskIcon(currentRiskLevel)}
                {currentRiskLevel.toUpperCase()}
              </Badge>
            </div>

            <Progress
              value={riskScore}
              className={`h-3 ${
                currentRiskLevel === "scam"
                  ? "[&>div]:bg-red-500"
                  : currentRiskLevel === "suspicious"
                    ? "[&>div]:bg-orange-500"
                    : "[&>div]:bg-green-500"
              }`}
            />

            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span>Voice Analysis:</span>
                <Badge variant="outline" className="text-xs">
                  {callStatus === "active" ? "Analyzing" : "Idle"}
                </Badge>
              </div>
              <div className="flex justify-between">
                <span>Connection:</span>
                <span className="text-muted-foreground">{isConnected ? "Active" : "Disconnected"}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Control Panel */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mic className="h-5 w-5" />
              Call Control
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-center gap-4">
              {callStatus === "idle" ? (
                <Button
                  onClick={startAnalysis}
                  size="lg"
                  className="bg-green-600 hover:bg-green-700"
                  disabled={!isConnected}
                >
                  <Play className="h-5 w-5 mr-2" />
                  Start Analysis
                </Button>
              ) : (
                <Button onClick={stopAnalysis} size="lg" variant="destructive">
                  <Square className="h-5 w-5 mr-2" />
                  Stop Analysis
                </Button>
              )}
            </div>

            {/* Audio Visualizer */}
            <div className="flex justify-center">
              <AudioVisualizer audioLevel={audioLevel} isActive={isRecording} className="w-full max-w-md" />
            </div>

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="flex items-center gap-2">
                {isRecording ? (
                  <Mic className="h-4 w-4 text-green-600" />
                ) : (
                  <MicOff className="h-4 w-4 text-gray-400" />
                )}
                <span>Microphone: {isRecording ? "Active" : "Inactive"}</span>
              </div>
              <div className="flex items-center gap-2">
                <div
                  className={`h-2 w-2 rounded-full ${callStatus === "active" ? "bg-green-500 animate-pulse" : "bg-gray-400"}`}
                />
                <span>Status: {callStatus === "active" ? "Monitoring" : "Standby"}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Live Transcript */}
      <Card>
        <CardHeader>
          <CardTitle>Live Transcript</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {transcript.length === 0 ? (
              <div className="text-center text-muted-foreground py-8">
                {callStatus === "active" ? "Listening for speech..." : "Start analysis to see live transcript"}
              </div>
            ) : (
              transcript.map((segment) => (
                <div key={segment.id} className="flex gap-3 p-3 rounded-lg bg-muted/50">
                  <div className="flex-shrink-0">
                    <Badge variant={segment.speaker === "user" ? "default" : "secondary"}>
                      {segment.speaker === "user" ? "You" : "Caller"}
                    </Badge>
                  </div>
                  <div className="flex-1">
                    <p className="text-sm">{segment.text}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-muted-foreground">{segment.timestamp}</span>
                      <Badge variant="outline" className={`text-xs ${getRiskColor(segment.riskLevel)}`}>
                        {getRiskIcon(segment.riskLevel)}
                        {segment.riskLevel}
                      </Badge>
                      <span className="text-xs text-muted-foreground">{segment.confidence.toFixed(0)}% confidence</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
