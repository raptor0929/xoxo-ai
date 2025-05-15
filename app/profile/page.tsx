"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Slider } from "@/components/ui/slider"
import { ChevronRight, Music, Film, Coffee, Book, Gamepad } from "lucide-react"

export default function ProfilePage() {
  const router = useRouter()
  const [step, setStep] = useState(1)
  const [profile, setProfile] = useState({
    name: "",
    age: "",
    gender: "",
    lookingFor: "",
    bio: "",
    interests: [],
    importanceOfHumor: 50,
    importanceOfLooks: 50,
    importanceOfValues: 50,
  })

  const totalSteps = 3

  const handleChange = (field, value) => {
    setProfile((prev) => ({ ...prev, [field]: value }))
  }

  const handleInterestToggle = (interest) => {
    setProfile((prev) => {
      const interests = [...prev.interests]
      if (interests.includes(interest)) {
        return { ...prev, interests: interests.filter((i) => i !== interest) }
      } else {
        return { ...prev, interests: [...interests, interest] }
      }
    })
  }

  const nextStep = () => {
    if (step < totalSteps) {
      setStep(step + 1)
    } else {
      router.push("/matching")
    }
  }

  const prevStep = () => {
    if (step > 1) {
      setStep(step - 1)
    }
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-pink-50 to-purple-100 p-4">
      <Card className="w-full max-w-md overflow-hidden border-2 border-pink-300 shadow-lg">
        <CardContent className="p-6">
          <div className="mb-6 flex items-center justify-between">
            <h1 className="text-2xl font-bold text-pink-600">Create Your Profile</h1>
            <div className="text-sm text-gray-500">
              Step {step} of {totalSteps}
            </div>
          </div>

          {step === 1 && (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Your Name</Label>
                <Input
                  id="name"
                  value={profile.name}
                  onChange={(e) => handleChange("name", e.target.value)}
                  placeholder="Enter your name"
                  className="border-pink-200"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="age">Your Age</Label>
                <Input
                  id="age"
                  type="number"
                  value={profile.age}
                  onChange={(e) => handleChange("age", e.target.value)}
                  placeholder="Enter your age"
                  className="border-pink-200"
                />
              </div>

              <div className="space-y-2">
                <Label>Gender</Label>
                <RadioGroup
                  value={profile.gender}
                  onValueChange={(value) => handleChange("gender", value)}
                  className="flex space-x-4"
                >
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="male" id="male" />
                    <Label htmlFor="male">Male</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="female" id="female" />
                    <Label htmlFor="female">Female</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="other" id="other" />
                    <Label htmlFor="other">Other</Label>
                  </div>
                </RadioGroup>
              </div>

              <div className="space-y-2">
                <Label>Looking For</Label>
                <RadioGroup
                  value={profile.lookingFor}
                  onValueChange={(value) => handleChange("lookingFor", value)}
                  className="flex space-x-4"
                >
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="men" id="men" />
                    <Label htmlFor="men">Men</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="women" id="women" />
                    <Label htmlFor="women">Women</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="both" id="both" />
                    <Label htmlFor="both">Both</Label>
                  </div>
                </RadioGroup>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="bio">About You</Label>
                <Textarea
                  id="bio"
                  value={profile.bio}
                  onChange={(e) => handleChange("bio", e.target.value)}
                  placeholder="Tell us about yourself..."
                  className="min-h-[100px] border-pink-200"
                />
              </div>

              <div className="space-y-2">
                <Label>Your Interests</Label>
                <div className="flex flex-wrap gap-2">
                  <Button
                    type="button"
                    variant={profile.interests.includes("music") ? "default" : "outline"}
                    className={
                      profile.interests.includes("music")
                        ? "bg-pink-500 hover:bg-pink-600"
                        : "border-pink-300 text-pink-600 hover:bg-pink-50"
                    }
                    onClick={() => handleInterestToggle("music")}
                  >
                    <Music className="mr-2 h-4 w-4" />
                    Music
                  </Button>
                  <Button
                    type="button"
                    variant={profile.interests.includes("movies") ? "default" : "outline"}
                    className={
                      profile.interests.includes("movies")
                        ? "bg-pink-500 hover:bg-pink-600"
                        : "border-pink-300 text-pink-600 hover:bg-pink-50"
                    }
                    onClick={() => handleInterestToggle("movies")}
                  >
                    <Film className="mr-2 h-4 w-4" />
                    Movies
                  </Button>
                  <Button
                    type="button"
                    variant={profile.interests.includes("coffee") ? "default" : "outline"}
                    className={
                      profile.interests.includes("coffee")
                        ? "bg-pink-500 hover:bg-pink-600"
                        : "border-pink-300 text-pink-600 hover:bg-pink-50"
                    }
                    onClick={() => handleInterestToggle("coffee")}
                  >
                    <Coffee className="mr-2 h-4 w-4" />
                    Coffee
                  </Button>
                  <Button
                    type="button"
                    variant={profile.interests.includes("reading") ? "default" : "outline"}
                    className={
                      profile.interests.includes("reading")
                        ? "bg-pink-500 hover:bg-pink-600"
                        : "border-pink-300 text-pink-600 hover:bg-pink-50"
                    }
                    onClick={() => handleInterestToggle("reading")}
                  >
                    <Book className="mr-2 h-4 w-4" />
                    Reading
                  </Button>
                  <Button
                    type="button"
                    variant={profile.interests.includes("gaming") ? "default" : "outline"}
                    className={
                      profile.interests.includes("gaming")
                        ? "bg-pink-500 hover:bg-pink-600"
                        : "border-pink-300 text-pink-600 hover:bg-pink-50"
                    }
                    onClick={() => handleInterestToggle("gaming")}
                  >
                    <Gamepad className="mr-2 h-4 w-4" />
                    Gaming
                  </Button>
                </div>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-6">
              <div className="space-y-4">
                <Label>How important is sense of humor to you?</Label>
                <div className="space-y-2">
                  <Slider
                    value={[profile.importanceOfHumor]}
                    min={0}
                    max={100}
                    step={1}
                    onValueChange={(value) => handleChange("importanceOfHumor", value[0])}
                    className="py-4"
                  />
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>Not important</span>
                    <span>Very important</span>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <Label>How important are looks to you?</Label>
                <div className="space-y-2">
                  <Slider
                    value={[profile.importanceOfLooks]}
                    min={0}
                    max={100}
                    step={1}
                    onValueChange={(value) => handleChange("importanceOfLooks", value[0])}
                    className="py-4"
                  />
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>Not important</span>
                    <span>Very important</span>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <Label>How important are shared values to you?</Label>
                <div className="space-y-2">
                  <Slider
                    value={[profile.importanceOfValues]}
                    min={0}
                    max={100}
                    step={1}
                    onValueChange={(value) => handleChange("importanceOfValues", value[0])}
                    className="py-4"
                  />
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>Not important</span>
                    <span>Very important</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </CardContent>

        <CardFooter className="flex justify-between border-t bg-gray-50 p-4">
          <Button
            onClick={prevStep}
            variant="outline"
            disabled={step === 1}
            className="border-pink-300 text-pink-600 hover:bg-pink-50"
          >
            Back
          </Button>

          <Button onClick={nextStep} className="bg-pink-500 hover:bg-pink-600">
            {step === totalSteps ? (
              <>
                Find Matches
                <ChevronRight className="ml-2 h-4 w-4" />
              </>
            ) : (
              <>
                Next
                <ChevronRight className="ml-2 h-4 w-4" />
              </>
            )}
          </Button>
        </CardFooter>
      </Card>
    </main>
  )
}
