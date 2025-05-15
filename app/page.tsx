import Link from "next/link"
import Image from "next/image"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { QrCode } from "lucide-react"

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-pink-50 to-purple-100 p-4">
      <Card className="w-full max-w-md overflow-hidden border-2 border-pink-300 shadow-lg">
        <CardContent className="p-0">
          <div className="flex flex-col items-center justify-center space-y-6 p-6 text-center">
            <h1 className="text-3xl font-bold text-pink-600">XOXO AI</h1>

            <div className="relative h-64 w-full overflow-hidden rounded-lg">
              <Image
                src="/xoxo-ai.png"
                alt="Dating Simulation Characters"
                height={0}
                width={400}
                className="object-cover"
              />
            </div>

            <h2 className="text-xl font-semibold text-gray-800">JOIN THE DATING SIMULATION</h2>

            <div className="flex h-48 w-48 items-center justify-center rounded-lg border-2 border-dashed border-gray-300 bg-gray-50">
              <QrCode className="h-24 w-24 text-gray-400" />
            </div>

            <Link href="/scan" className="w-full">
              <Button className="w-full bg-pink-500 text-lg font-semibold hover:bg-pink-600">Scan QR Code</Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </main>
  )
}
