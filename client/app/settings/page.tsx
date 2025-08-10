"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Slider } from "@/components/ui/slider"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { Globe, Volume2, Shield, Mic, Bell, Save, RotateCcw } from "lucide-react"

export default function Settings() {
  const [detectionLanguage, setDetectionLanguage] = useState("auto")
  const [audioAlerts, setAudioAlerts] = useState(true)
  const [visualAlerts, setVisualAlerts] = useState(true)
  const [riskThreshold, setRiskThreshold] = useState([50])
  const [autoRecord, setAutoRecord] = useState(false)
  const [realTimeTranscription, setRealTimeTranscription] = useState(true)
  const [voicePrintVerification, setVoicePrintVerification] = useState(false)

  const handleSave = () => {
    // Save settings logic here
    console.log("Settings saved")
  }

  const handleReset = () => {
    // Reset to defaults
    setDetectionLanguage("auto")
    setAudioAlerts(true)
    setVisualAlerts(true)
    setRiskThreshold([50])
    setAutoRecord(false)
    setRealTimeTranscription(true)
    setVoicePrintVerification(false)
  }

  return (
    <div className="flex-1 space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <SidebarTrigger />
          <div>
            <h1 className="text-3xl font-bold">Settings</h1>
            <p className="text-muted-foreground">Configure your VoiceSentinel preferences</p>
          </div>
        </div>

        <div className="flex gap-2">
          <Button variant="outline" onClick={handleReset}>
            <RotateCcw className="h-4 w-4 mr-2" />
            Reset
          </Button>
          <Button onClick={handleSave}>
            <Save className="h-4 w-4 mr-2" />
            Save Changes
          </Button>
        </div>
      </div>

      <div className="grid gap-6">
        {/* Language Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Globe className="h-5 w-5" />
              Language Detection
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Detection Language</label>
              <Select value={detectionLanguage} onValueChange={setDetectionLanguage}>
                <SelectTrigger>
                  <SelectValue placeholder="Select language" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="auto">Auto-detect</SelectItem>
                  <SelectItem value="en">English</SelectItem>
                  <SelectItem value="es">Spanish</SelectItem>
                  <SelectItem value="fr">French</SelectItem>
                  <SelectItem value="de">German (Beta)</SelectItem>
                  <SelectItem value="it">Italian (Beta)</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                Auto-detect will identify the language automatically. Manual selection may improve accuracy.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Alert Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              Alert Preferences
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Volume2 className="h-4 w-4" />
                  <span className="font-medium">Audio Alerts</span>
                </div>
                <p className="text-sm text-muted-foreground">Play discrete audio warnings during suspicious calls</p>
              </div>
              <Switch checked={audioAlerts} onCheckedChange={setAudioAlerts} />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Shield className="h-4 w-4" />
                  <span className="font-medium">Visual Alerts</span>
                </div>
                <p className="text-sm text-muted-foreground">Show visual warnings on screen during calls</p>
              </div>
              <Switch checked={visualAlerts} onCheckedChange={setVisualAlerts} />
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Shield className="h-4 w-4" />
                <span className="font-medium">Risk Alert Threshold</span>
              </div>
              <div className="px-3">
                <Slider
                  value={riskThreshold}
                  onValueChange={setRiskThreshold}
                  max={100}
                  min={10}
                  step={5}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-muted-foreground mt-1">
                  <span>Low (10%)</span>
                  <span className="font-medium">Current: {riskThreshold[0]}%</span>
                  <span>High (100%)</span>
                </div>
              </div>
              <p className="text-sm text-muted-foreground">Alert when risk score exceeds this threshold</p>
            </div>
          </CardContent>
        </Card>

        {/* Recording & Analysis */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mic className="h-5 w-5" />
              Recording & Analysis
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <span className="font-medium">Real-time Transcription</span>
                <p className="text-sm text-muted-foreground">Show live transcript during calls</p>
              </div>
              <Switch checked={realTimeTranscription} onCheckedChange={setRealTimeTranscription} />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <span className="font-medium">Auto-record Suspicious Calls</span>
                <p className="text-sm text-muted-foreground">Automatically save audio when scam is detected</p>
              </div>
              <Switch checked={autoRecord} onCheckedChange={setAutoRecord} />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <span className="font-medium">Voice Print Verification</span>
                <p className="text-sm text-muted-foreground">Verify known contacts against saved voice prints</p>
              </div>
              <Switch checked={voicePrintVerification} onCheckedChange={setVoicePrintVerification} />
            </div>
          </CardContent>
        </Card>

        {/* Privacy & Data */}
        <Card>
          <CardHeader>
            <CardTitle>Privacy & Data</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <h4 className="font-medium">Data Retention</h4>
              <p className="text-sm text-muted-foreground">
                Call recordings and transcripts are stored locally and encrypted. Data is automatically deleted after 30
                days unless marked for retention.
              </p>
            </div>

            <div className="space-y-2">
              <h4 className="font-medium">AI Processing</h4>
              <p className="text-sm text-muted-foreground">
                Voice analysis is performed locally when possible. Some features may require secure cloud processing for
                optimal accuracy.
              </p>
            </div>

            <Button variant="outline" className="w-full bg-transparent">
              View Privacy Policy
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
