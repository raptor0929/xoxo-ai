"use client"

import { useState, useEffect } from "react"
import Image from "next/image"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Heart, MessageCircle, Download, X, Loader2 } from "lucide-react"

// Sample match data
const matchesData = [
  {
    id: 1,
    name: "Tom",
    avatar: "/man-1.png?height=100&width=100",
    compatibility: 75,
    bio: "I'm a software engineer who loves hiking and trying new restaurants. Looking for someone to share adventures with!",
    interests: ["hiking", "coding", "food", "travel"],
    conversation: [
      { text: "Hi there! I noticed we both like hiking. What's your favorite trail?", sender: "match" },
      { text: "Hey! I love the Pacific Crest Trail. Have you ever been?", sender: "user" },
      { text: "Not yet, but it's on my bucket list! I've mostly hiked around the Rockies.", sender: "match" },
    ],
  },
  {
    id: 2,
    name: "Jake",
    avatar: "/man-2.png?height=100&width=100",
    compatibility: 82,
    bio: "Musician and coffee enthusiast. I spend most weekends at local shows or trying new coffee shops.",
    interests: ["music", "coffee", "art", "photography"],
    conversation: [
      { text: "Your taste in music is amazing! What concerts have you been to recently?", sender: "match" },
      { text: "Thanks! I just saw The National last month. It was incredible!", sender: "user" },
      { text: "No way! They're one of my favorites. We should go to a show sometime.", sender: "match" },
    ],
  },
  {
    id: 3,
    name: "Robert",
    avatar: "/man-3.png?height=100&width=100",
    compatibility: 68,
    bio: "Bookworm and amateur chef. I can make a mean risotto and will always have book recommendations ready.",
    interests: ["reading", "cooking", "movies", "hiking"],
    conversation: [],
  },
]

export default function MatchesPage() {
  const [matches, setMatches] = useState(matchesData)
  const [selectedMatch, setSelectedMatch] = useState(null)
  const [activeTab, setActiveTab] = useState("profile")
  const [showMintDialog, setShowMintDialog] = useState(false)
  const [isRobertLoading, setIsRobertLoading] = useState(true)

  const openMatchDetails = (match) => {
    setSelectedMatch(match)
    setActiveTab("profile")
  }

  const closeMatchDetails = () => {
    setSelectedMatch(null)
  }

  // Simulate Robert's loading state (agents having a conversation)
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsRobertLoading(false)
    }, 10000) // 10 seconds
    
    return () => clearTimeout(timer)
  }, [])

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-pink-50 to-purple-100 p-4">
      <Card className="w-full max-w-md overflow-hidden border-2 border-pink-300 shadow-lg">
        <CardHeader className="border-b bg-white p-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-pink-600">Your Matches</h1>
            <div className="flex items-center space-x-2">
              <div className="relative h-10 w-10 overflow-hidden rounded-full border-2 border-pink-200">
                <Image src="/woman-1.jpeg?height=100&width=100" alt="Ana" fill className="object-cover" />
              </div>
              <span className="font-medium">Ana</span>
            </div>
          </div>
        </CardHeader>

        <CardContent className="p-0">
          <div className="divide-y divide-gray-100">
            {matches.map((match) => (
              <div
                key={match.id}
                className="flex items-center justify-between p-4 transition-colors hover:bg-gray-50"
                onClick={() => match.name !== "Robert" || !isRobertLoading ? openMatchDetails(match) : null}
              >
                <div className="flex items-center space-x-3">
                  <div className="relative h-16 w-16 overflow-hidden rounded-full border-2 border-pink-200">
                    {match.name === "Robert" && isRobertLoading ? (
                      <div className="flex h-full w-full items-center justify-center bg-gray-100">
                        <Loader2 className="h-8 w-8 animate-spin text-pink-500" />
                      </div>
                    ) : (
                      <Image src={match.avatar || "/placeholder.svg"} alt={match.name} fill className="object-cover" />
                    )}
                  </div>

                  <div>
                    <h3 className="text-lg font-semibold">{match.name}</h3>
                    <div className="flex items-center space-x-1">
                      <Heart className="h-4 w-4 text-pink-500" fill="#ec4899" />
                      <span className="text-sm text-gray-600">
                        Compatibility: <span className="font-medium text-pink-600">{match.compatibility}%</span>
                      </span>
                    </div>
                    {match.name === "Robert" && isRobertLoading && (
                      <div className="mt-1 text-xs text-gray-500">
                        AI agents are having a conversation...
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex space-x-2">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="rounded-full text-pink-500 hover:bg-pink-50 hover:text-pink-600"
                  >
                    <MessageCircle className="h-5 w-5" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="rounded-full text-purple-500 hover:bg-purple-50 hover:text-purple-600"
                    onClick={(e) => {
                      e.stopPropagation();
                      // Create a download link for the transcript file
                      const link = document.createElement('a');
                      link.href = '/Users/flaura-macbook/_projects/xoxo/src/xoxo/logs/irvin_maria_conversation.txt';
                      link.download = 'irvin_maria_conversation.txt';
                      document.body.appendChild(link);
                      link.click();
                      document.body.removeChild(link);
                    }}
                  >
                    <Download className="h-5 w-5" aria-label="Download Transcript" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="rounded-full text-pink-500 hover:bg-pink-50 hover:text-pink-600"
                    onClick={(e) => {
                      e.stopPropagation();
                      window.open('https://testnets.opensea.io/assets/base_sepolia/0xb944C6eAFb3b76FCF54aEE0d821b755dFBA17250/2', '_blank');
                    }}
                  >
                    <Heart className="h-5 w-5" aria-label="Mint NFT" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>

        <CardFooter className="flex justify-center border-t bg-gray-50 p-4">
          <Button onClick={() => (window.location.href = "/")} className="bg-pink-500 hover:bg-pink-600">
            Start Over
          </Button>
        </CardFooter>
      </Card>

      {selectedMatch && (
        <Dialog open={!!selectedMatch} onOpenChange={(open) => !open && closeMatchDetails()}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <div className="flex items-center space-x-3">
                <div className="relative h-16 w-16 overflow-hidden rounded-full border-2 border-pink-200">
                  <Image
                    src={selectedMatch.avatar || "/placeholder.svg"}
                    alt={selectedMatch.name}
                    fill
                    className="object-cover"
                  />
                </div>
                <div>
                  <DialogTitle className="text-xl">{selectedMatch.name}</DialogTitle>
                  <DialogDescription>
                    <span className="flex items-center text-pink-600">
                      <Heart className="mr-1 h-4 w-4" fill="#ec4899" />
                      {selectedMatch.compatibility}% Compatible
                    </span>
                  </DialogDescription>
                </div>
              </div>
            </DialogHeader>

            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="profile">Profile</TabsTrigger>
                <TabsTrigger value="chat">Chat</TabsTrigger>
              </TabsList>

              <TabsContent value="profile" className="space-y-4 pt-4">
                <div>
                  <h4 className="font-medium text-gray-700">About</h4>
                  <p className="text-gray-600">{selectedMatch.bio}</p>
                </div>

                <div>
                  <h4 className="font-medium text-gray-700">Interests</h4>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {selectedMatch.interests.map((interest) => (
                      <Badge key={interest} className="bg-pink-100 text-pink-800 hover:bg-pink-200">
                        {interest}
                      </Badge>
                    ))}
                  </div>
                </div>

                <div className="flex space-x-2 pt-2">
                  <Button
                    onClick={() => {
                      window.open('https://testnets.opensea.io/assets/base_sepolia/0xb944C6eAFb3b76FCF54aEE0d821b755dFBA17250/2', '_blank');
                    }}
                    className="flex-1 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
                  >
                    <Heart className="mr-2 h-4 w-4" />
                    Mint NFT
                  </Button>
                  
                  <Button 
                    onClick={() => {
                      // Create a download link for the transcript file
                      const link = document.createElement('a');
                      link.href = '/Users/flaura-macbook/_projects/xoxo/src/xoxo/logs/irvin_maria_conversation.txt';
                      link.download = 'irvin_maria_conversation.txt';
                      document.body.appendChild(link);
                      link.click();
                      document.body.removeChild(link);
                    }}
                    className="flex-1 bg-purple-500 hover:bg-purple-600"
                  >
                    <Download className="mr-2 h-4 w-4" />
                    Transcript
                  </Button>

                  <Button onClick={() => setActiveTab("chat")} className="flex-1 bg-pink-500 hover:bg-pink-600">
                    <MessageCircle className="mr-2 h-4 w-4" />
                    Chat
                  </Button>
                </div>
              </TabsContent>

              <TabsContent value="chat" className="h-[300px] space-y-4 overflow-y-auto pt-4">
                {selectedMatch.conversation.length > 0 ? (
                  <div className="space-y-3">
                    {selectedMatch.conversation.map((message, index) => (
                      <div
                        key={index}
                        className={`flex ${message.sender === "user" ? "justify-end" : "justify-start"}`}
                      >
                        <div
                          className={`max-w-[80%] rounded-lg p-3 ${
                            message.sender === "user" ? "bg-pink-500 text-white" : "bg-gray-100 text-gray-800"
                          }`}
                        >
                          {message.text}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex h-full flex-col items-center justify-center text-center text-gray-500">
                    <div className="flex space-x-2">
                      <MessageCircle className="h-6 w-6 text-pink-400" />
                      <Download className="h-6 w-6 text-purple-400" aria-label="Download Transcript" />
                      <Heart className="h-6 w-6 text-pink-400" aria-label="Mint NFT" />
                    </div>
                    <p>No messages yet</p>
                    <p className="text-sm">Start the conversation!</p>
                  </div>
                )}
              </TabsContent>
            </Tabs>
          </DialogContent>
        </Dialog>
      )}

      <Dialog open={showMintDialog} onOpenChange={setShowMintDialog}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Mint Match as NFT</DialogTitle>
            <DialogDescription>Create a unique NFT of your match to commemorate this connection.</DialogDescription>
          </DialogHeader>

          <div className="flex flex-col items-center justify-center space-y-4 py-4">
            <div className="relative h-40 w-40 overflow-hidden rounded-lg border-4 border-pink-200 bg-gradient-to-r from-purple-100 to-pink-100 p-2">
              {selectedMatch && (
                <Image
                  src={selectedMatch.avatar || "/placeholder.svg"}
                  alt={selectedMatch.name}
                  fill
                  className="object-cover"
                />
              )}
            </div>

            <div className="text-center">
              <h3 className="text-lg font-semibold text-pink-600">{selectedMatch?.name} × You</h3>
              <p className="text-sm text-gray-500">Compatibility: {selectedMatch?.compatibility}%</p>
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowMintDialog(false)}
              className="border-pink-200 text-pink-600 hover:bg-pink-50"
            >
              <X className="mr-2 h-4 w-4" />
              Cancel
            </Button>
            <Button
              onClick={() => {
                // Simulate minting
                setTimeout(() => {
                  setShowMintDialog(false)
                }, 1000)
              }}
              className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
            >
              <Download className="mr-2 h-4 w-4" />
              Mint NFT
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </main>
  )
}
