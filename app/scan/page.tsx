"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Loader2, Camera } from "lucide-react"

export default function ScanPage() {
  const router = useRouter()
  const [scanning, setScanning] = useState(false)

  const handleScan = () => {
    setScanning(true)
    // Simulate QR code scanning
    setTimeout(() => {
      setScanning(false)
      router.push("/profile")
    }, 2000)
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-pink-50 to-purple-100 p-4">
      <Card className="w-full max-w-md overflow-hidden border-2 border-pink-300 shadow-lg">
        <CardContent className="p-6">
          <div className="flex flex-col items-center justify-center space-y-6 text-center">
            <h1 className="text-2xl font-bold text-pink-600">Scan QR Code</h1>

            <div className="relative h-64 w-full overflow-hidden rounded-lg border-2 border-dashed border-gray-300 bg-gray-50">
              {scanning ? (
                <div className="flex h-full w-full flex-col items-center justify-center">
                  <Loader2 className="h-12 w-12 animate-spin text-pink-500" />
                  <p className="mt-4 text-gray-600">Scanning...</p>
                </div>
              ) : (
                <div className="flex h-full w-full flex-col items-center justify-center">
                  <Camera className="h-16 w-16 text-gray-400" />
                  <p className="mt-4 text-gray-600">Position QR code in frame</p>
                </div>
              )}
            </div>

            <Button
              onClick={handleScan}
              disabled={scanning}
              className="w-full bg-pink-500 text-lg font-semibold hover:bg-pink-600"
            >
              {scanning ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Scanning...
                </>
              ) : (
                "Start Scanning"
              )}
            </Button>

            <Button
              onClick={() => router.push("/profile")}
              variant="outline"
              className="w-full border-pink-300 text-pink-600 hover:bg-pink-50"
            >
              Skip to Profile
            </Button>
          </div>
        </CardContent>
      </Card>
    </main>
  )
}
