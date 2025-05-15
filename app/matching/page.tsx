"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Loader2 } from "lucide-react"

export default function MatchingPage() {
  const router = useRouter()
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    const timer = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(timer)
          setTimeout(() => {
            router.push("/matches")
          }, 500)
          return 100
        }
        return prev + 5
      })
    }, 150)

    return () => clearInterval(timer)
  }, [router])

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-pink-50 to-purple-100 p-4">
      <Card className="w-full max-w-md overflow-hidden border-2 border-pink-300 shadow-lg">
        <CardContent className="p-6">
          <div className="flex flex-col items-center justify-center space-y-6 text-center">
            <h1 className="text-2xl font-bold text-pink-600">Finding Your Matches</h1>

            <div className="flex h-24 w-24 items-center justify-center rounded-full bg-pink-100">
              <Loader2 className="h-12 w-12 animate-spin text-pink-500" />
            </div>

            <div className="w-full space-y-2">
              <Progress value={progress} className="h-2 w-full bg-pink-100" indicatorClassName="bg-pink-500" />
              <p className="text-sm text-gray-600">{progress}% Complete</p>
            </div>

            <div className="space-y-2 text-center">
              <p className="text-lg font-medium text-gray-700">
                {progress < 30 && "Analyzing your preferences..."}
                {progress >= 30 && progress < 60 && "Searching for compatible matches..."}
                {progress >= 60 && progress < 90 && "Calculating compatibility scores..."}
                {progress >= 90 && "Almost there! Preparing your matches..."}
              </p>
              <p className="text-sm text-gray-500">
                Our AI is working to find your perfect matches based on your profile
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </main>
  )
}
