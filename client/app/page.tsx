import { AudioRecorder } from "@/components/audio-recorder"
import { CallerVerification } from "@/components/caller-verification" 
import Image from "next/image"

export default function Home() {
  return (
    <div className="font-sans flex flex-col items-center min-h-screen p-8 pb-20 gap-8 sm:p-20 bg-gray-50 dark:bg-gray-900">
      <main className="flex flex-col gap-8 items-center w-full max-w-4xl">
        <div className="flex flex-col items-center justify-center w-full">
          <h1 className="text-4xl font-bold text-center mb-4 text-gray-800 dark:text-gray-100">Voice Scam Shield</h1>
          <p className="text-lg text-center mb-12 text-gray-600 dark:text-gray-300">
            Détection d'arnaques vocales en temps réel et vérification de l'appelant.
          </p>
          <AudioRecorder />
          <CallerVerification /> {/* Add the new component here */}
        </div>
      </main>
    </div>
  )
}
