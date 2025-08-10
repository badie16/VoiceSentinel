"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { Search, Calendar, Clock, Shield, AlertTriangle, CheckCircle, Eye, Download } from "lucide-react"

interface CallRecord {
  id: string
  date: string
  time: string
  duration: string
  riskScore: number
  riskLevel: "safe" | "suspicious" | "scam"
  callerInfo: string
  summary: string
  flaggedSegments: number
}

const mockCallHistory: CallRecord[] = [
  {
    id: "1",
    date: "2024-01-15",
    time: "14:30",
    duration: "5:23",
    riskScore: 85,
    riskLevel: "scam",
    callerInfo: "+1 (555) 123-4567",
    summary: "Caller claimed to be from bank, requested account verification",
    flaggedSegments: 3,
  },
  {
    id: "2",
    date: "2024-01-15",
    time: "10:15",
    duration: "2:45",
    riskScore: 25,
    riskLevel: "safe",
    callerInfo: "Mom",
    summary: "Regular family call, no suspicious activity detected",
    flaggedSegments: 0,
  },
  {
    id: "3",
    date: "2024-01-14",
    time: "16:45",
    duration: "8:12",
    riskScore: 60,
    riskLevel: "suspicious",
    callerInfo: "+1 (555) 987-6543",
    summary: "Telemarketing call with pressure tactics detected",
    flaggedSegments: 2,
  },
  {
    id: "4",
    date: "2024-01-14",
    time: "09:20",
    duration: "1:30",
    riskScore: 15,
    riskLevel: "safe",
    callerInfo: "Dr. Smith's Office",
    summary: "Appointment confirmation call",
    flaggedSegments: 0,
  },
  {
    id: "5",
    date: "2024-01-13",
    time: "19:30",
    duration: "12:45",
    riskScore: 90,
    riskLevel: "scam",
    callerInfo: "+1 (555) 456-7890",
    summary: "Tech support scam attempt, voice cloning detected",
    flaggedSegments: 5,
  },
]

export default function CallHistory() {
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedCall, setSelectedCall] = useState<CallRecord | null>(null)

  const filteredCalls = mockCallHistory.filter(
    (call) =>
      call.callerInfo.toLowerCase().includes(searchTerm.toLowerCase()) ||
      call.summary.toLowerCase().includes(searchTerm.toLowerCase()),
  )

  const getRiskColor = (level: "safe" | "suspicious" | "scam") => {
    switch (level) {
      case "safe":
        return "text-green-600 bg-green-50 border-green-200"
      case "suspicious":
        return "text-orange-600 bg-orange-50 border-orange-200"
      case "scam":
        return "text-red-600 bg-red-50 border-red-200"
    }
  }

  const getRiskIcon = (level: "safe" | "suspicious" | "scam") => {
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
            <h1 className="text-3xl font-bold">Call History</h1>
            <p className="text-muted-foreground">Review past calls and security analysis</p>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search calls by caller or content..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Button variant="outline">
              <Calendar className="h-4 w-4 mr-2" />
              Filter by Date
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Call List */}
      <div className="grid gap-4">
        {filteredCalls.map((call) => (
          <Card key={call.id} className="hover:shadow-md transition-shadow">
            <CardContent className="pt-6">
              <div className="flex items-start justify-between">
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-3">
                    <div className="font-semibold">{call.callerInfo}</div>
                    <Badge className={getRiskColor(call.riskLevel)}>
                      {getRiskIcon(call.riskLevel)}
                      {call.riskLevel.toUpperCase()}
                    </Badge>
                    <div className="text-2xl font-bold text-muted-foreground">{call.riskScore}%</div>
                  </div>

                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <Calendar className="h-4 w-4" />
                      {call.date}
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock className="h-4 w-4" />
                      {call.time} ({call.duration})
                    </div>
                    {call.flaggedSegments > 0 && (
                      <div className="flex items-center gap-1 text-orange-600">
                        <AlertTriangle className="h-4 w-4" />
                        {call.flaggedSegments} flagged segments
                      </div>
                    )}
                  </div>

                  <p className="text-sm">{call.summary}</p>
                </div>

                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={() => setSelectedCall(call)}>
                    <Eye className="h-4 w-4 mr-2" />
                    View Details
                  </Button>
                  <Button variant="outline" size="sm">
                    <Download className="h-4 w-4 mr-2" />
                    Export
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Call Details Modal/Panel */}
      {selectedCall && (
        <Card className="border-2 border-blue-200">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Call Details - {selectedCall.callerInfo}</CardTitle>
              <Button variant="outline" size="sm" onClick={() => setSelectedCall(null)}>
                Close
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="font-medium">Date:</span>
                <div className="text-muted-foreground">{selectedCall.date}</div>
              </div>
              <div>
                <span className="font-medium">Time:</span>
                <div className="text-muted-foreground">{selectedCall.time}</div>
              </div>
              <div>
                <span className="font-medium">Duration:</span>
                <div className="text-muted-foreground">{selectedCall.duration}</div>
              </div>
              <div>
                <span className="font-medium">Risk Score:</span>
                <div className="text-muted-foreground">{selectedCall.riskScore}%</div>
              </div>
            </div>

            <div>
              <span className="font-medium">Summary:</span>
              <p className="text-muted-foreground mt-1">{selectedCall.summary}</p>
            </div>

            <div>
              <span className="font-medium">Transcript Preview:</span>
              <div className="mt-2 p-3 bg-muted rounded-lg text-sm">
                <p className="italic">Full transcript and detailed analysis would be displayed here...</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
