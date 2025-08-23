import { cn } from "@/lib/utils"

interface LoadingSpinnerProps {
  size?: "sm" | "md" | "lg"
  className?: string
}

export function LoadingSpinner({ size = "md", className }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: "h-4 w-4",
    md: "h-6 w-6", 
    lg: "h-8 w-8"
  }

  return (
    <div 
      className={cn(
        "animate-spin rounded-full border-b-2 border-primary",
        sizeClasses[size],
        className
      )}
    />
  )
}

interface LoadingStateProps {
  message?: string
  size?: "sm" | "md" | "lg"
  className?: string
}

export function LoadingState({ 
  message = "Loading...", 
  size = "lg",
  className 
}: LoadingStateProps) {
  return (
    <div className={cn("min-h-screen bg-background flex items-center justify-center", className)}>
      <div className="text-center">
        <LoadingSpinner size={size} className="mx-auto mb-4" />
        <p className="text-muted-foreground">{message}</p>
      </div>
    </div>
  )
}

export function InlineLoading({ 
  message = "Loading...", 
  size = "md",
  className 
}: LoadingStateProps) {
  return (
    <div className={cn("flex items-center justify-center py-8", className)}>
      <div className="text-center">
        <LoadingSpinner size={size} className="mx-auto mb-2" />
        <p className="text-muted-foreground text-sm">{message}</p>
      </div>
    </div>
  )
}