"use client"

import { useState, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Mic, StopCircle, UserPlus } from "lucide-react"

const ENROLL_VOICE_URL = "http://localhost:8000/enroll-voice"

export function CallerVerification() {
    const [enrollName, setEnrollName] = useState("")
    const [isEnrolling, setIsEnrolling] = useState(false)
    const [enrollMessage, setEnrollMessage] = useState("")
    const mediaRecorderRef = useRef<MediaRecorder | null>(null)
    const audioChunksRef = useRef<Blob[]>([])
    const streamRef = useRef<MediaStream | null>(null)
    const audioContextRef = useRef<AudioContext | null>(null)

    const startEnrollRecording = async () => {
        if (!enrollName.trim()) {
            setEnrollMessage("Veuillez entrer un nom pour l'inscription vocale.")
            return
        }
        setEnrollMessage("")
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
            streamRef.current = stream
            mediaRecorderRef.current = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" })
            audioChunksRef.current = []

            mediaRecorderRef.current.ondataavailable = (event) => {
                audioChunksRef.current.push(event.data)
            }

            mediaRecorderRef.current.onstop = async () => {
                const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm;codecs=opus" })
                await sendEnrollAudio(audioBlob)
                audioChunksRef.current = []
            }

            mediaRecorderRef.current.start()
            setIsEnrolling(true)
            setEnrollMessage("Enregistrement de la voix en cours...")
            console.log("Enrollment recording started...")
        } catch (err) {
            console.error("Error accessing microphone for enrollment:", err)
            setEnrollMessage("Erreur d'accès au microphone. Veuillez autoriser l'accès.")
        }
    }

    const stopEnrollRecording = () => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
            mediaRecorderRef.current.stop()
            setIsEnrolling(false)
            console.log("Stopping enrollment recording...")
        }
        if (streamRef.current) {
            streamRef.current.getTracks().forEach((track) => track.stop())
        }
    }

    const sendEnrollAudio = async (audioBlob: Blob) => {
        try {
            if (!audioContextRef.current) {
                audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)()
            }
            const arrayBuffer = await audioBlob.arrayBuffer()
            const audioBuffer = await audioContextRef.current.decodeAudioData(arrayBuffer)
            const wavBlob = audioBufferToWav(audioBuffer) // Convert to WAV for backend

            const formData = new FormData()
            formData.append("audio_file", wavBlob, `${enrollName}.wav`)

            const response = await fetch(`${ENROLL_VOICE_URL}/${encodeURIComponent(enrollName)}`, {
                method: "POST",
                body: formData,
            })

            if (response.ok) {
                const data = await response.json()
                setEnrollMessage(data.message)
                setEnrollName("") // Clear input after successful enrollment
            } else {
                const errorData = await response.json()
                setEnrollMessage(`Échec de l'inscription: ${errorData.detail || response.statusText}`)
            }
        } catch (error) {
            console.error("Error sending enrollment audio:", error)
            setEnrollMessage("Erreur lors de l'envoi de l'audio d'inscription.")
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

    return (
        <Card className="w-full max-w-2xl mx-auto mt-8">
            <CardHeader>
                <CardTitle className="flex items-center">
                    <UserPlus className="mr-2 h-5 w-5" /> Inscription vocale pour vérification
                </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                    Enregistrez la voix d'un contact connu pour l'ajouter à la liste de vérification.
                </p>
                <div>
                    <Label htmlFor="enrollName" className="mb-1 block">
                        Nom du contact
                    </Label>
                    <Input
                        id="enrollName"
                        type="text"
                        placeholder="Ex: Maman, Banque XYZ"
                        value={enrollName}
                        onChange={(e) => setEnrollName(e.target.value)}
                        disabled={isEnrolling}
                    />
                </div>
                {isEnrolling ? (
                    <Button onClick={stopEnrollRecording} className="w-full py-3" variant="secondary">
                        <StopCircle className="mr-2 h-5 w-5" /> Arrêter l'enregistrement
                    </Button>
                ) : (
                    <Button onClick={startEnrollRecording} className="w-full py-3" disabled={!enrollName.trim()}>
                        <Mic className="mr-2 h-5 w-5" /> Démarrer l'enregistrement
                    </Button>
                )}
                {enrollMessage && (
                    <p className={`text-sm ${enrollMessage.includes("Échec") ? "text-red-500" : "text-green-500"}`}>
                        {enrollMessage}
                    </p>
                )}
            </CardContent>
        </Card>
    )
}
