"use client"

import { Loader2, Heart } from "lucide-react"

interface LoadingSpinnerProps {
  message?: string
}

export function LoadingSpinner({ message = "Loading..." }: LoadingSpinnerProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center">
      <div className="text-center space-y-4">
        
        {/* Spinner */}
        <div className="flex justify-center">
          <div className="relative">
            <Loader2 className="h-12 w-12 text-purple-600 animate-spin" />
            <Heart className="absolute inset-0 h-6 w-6 text-red-500 animate-pulse m-auto" />
          </div>
        </div>

        {/* Message */}
        <div className="space-y-2">
          <p className="text-lg font-medium text-gray-900">{message}</p>
          <p className="text-sm text-gray-600">Please wait while we prepare your pet's journey...</p>
        </div>

        {/* Animated dots */}
        <div className="flex justify-center space-x-1">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="w-2 h-2 bg-purple-600 rounded-full animate-bounce"
              style={{
                animationDelay: `${i * 0.2}s`,
                animationDuration: '1s'
              }}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
