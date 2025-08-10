"use client"

import { useState, useRef, useCallback, useEffect } from "react"

interface WebSocketMessage {
  type: string
  [key: string]: any
}

interface WebSocketHook {
  isConnected: boolean
  sendMessage: (message: WebSocketMessage) => void
  lastMessage: WebSocketMessage | null
  error: string | null
  connect: () => void
  disconnect: () => void
  connectionState: "connecting" | "connected" | "disconnected" | "error"
}

export function useWebSocket(url: string, onMessage?: (message: WebSocketMessage) => void): WebSocketHook {
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [connectionState, setConnectionState] = useState<"connecting" | "connected" | "disconnected" | "error">(
    "disconnected",
  )

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttempts = useRef(0)
  const maxReconnectAttempts = 3
  const isManualDisconnect = useRef(false)

  const connect = useCallback(() => {
    // Don't attempt connection if already connecting or connected
    if (wsRef.current?.readyState === WebSocket.CONNECTING || wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    try {
      setError(null)
      setConnectionState("connecting")
      isManualDisconnect.current = false

      console.log(`Attempting to connect to WebSocket: ${url}`)
      const ws = new WebSocket(url)
      wsRef.current = ws

      // Set a connection timeout
      const connectionTimeout = setTimeout(() => {
        if (ws.readyState === WebSocket.CONNECTING) {
          console.log("WebSocket connection timeout")
          ws.close()
          setError("Connection timeout")
          setConnectionState("error")
        }
      }, 10000) // 10 second timeout

      ws.onopen = () => {
        clearTimeout(connectionTimeout)
        console.log("WebSocket connected successfully")
        setIsConnected(true)
        setConnectionState("connected")
        setError(null)
        reconnectAttempts.current = 0
      }

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as WebSocketMessage
          setLastMessage(message)
          onMessage?.(message)
        } catch (err) {
          console.error("Failed to parse WebSocket message:", err)
          setError("Failed to parse server message")
        }
      }

      ws.onclose = (event) => {
        clearTimeout(connectionTimeout)
        console.log(`WebSocket disconnected: Code ${event.code}, Reason: ${event.reason}`)
        setIsConnected(false)
        wsRef.current = null

        if (event.code === 1000 || isManualDisconnect.current) {
          // Normal closure or manual disconnect
          setConnectionState("disconnected")
          setError(null)
        } else {
          // Unexpected closure
          setConnectionState("error")
          setError(`Connection lost (Code: ${event.code})`)

          // Attempt to reconnect if not manually closed and within retry limit
          if (reconnectAttempts.current < maxReconnectAttempts) {
            const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 10000) // Exponential backoff, max 10s
            console.log(
              `Attempting to reconnect in ${delay}ms (attempt ${reconnectAttempts.current + 1}/${maxReconnectAttempts})`,
            )

            reconnectTimeoutRef.current = setTimeout(() => {
              reconnectAttempts.current++
              connect()
            }, delay)
          } else {
            setError("Failed to connect after multiple attempts. Please check if the server is running.")
          }
        }
      }

      ws.onerror = (event) => {
        clearTimeout(connectionTimeout)
        console.error("WebSocket error:", event)
        setError("WebSocket connection failed. Make sure the server is running on localhost:8000")
        setConnectionState("error")
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to create WebSocket connection"
      console.error("WebSocket creation error:", err)
      setError(errorMessage)
      setConnectionState("error")
    }
  }, [url, onMessage])

  const disconnect = useCallback(() => {
    isManualDisconnect.current = true

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (wsRef.current) {
      console.log("Manually disconnecting WebSocket")
      wsRef.current.close(1000, "Manual disconnect")
      wsRef.current = null
    }

    setIsConnected(false)
    setConnectionState("disconnected")
    setError(null)
    reconnectAttempts.current = 0
  }, [])

  const sendMessage = useCallback((message: WebSocketMessage) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify(message))
        console.log("Message sent:", message.type)
      } catch (err) {
        console.error("Failed to send message:", err)
        setError("Failed to send message")
      }
    } else {
      console.warn(`WebSocket not ready (state: ${wsRef.current?.readyState}), message not sent:`, message.type)
      setError("Connection not ready")
    }
  }, [])

  // Auto-connect on mount, but don't reconnect automatically
  useEffect(() => {
    // Small delay to allow component to mount properly
    const timer = setTimeout(() => {
      connect()
    }, 100)

    return () => {
      clearTimeout(timer)
      disconnect()
    }
  }, []) // Remove connect/disconnect from deps to avoid infinite loops

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect()
    }
  }, [disconnect])

  return {
    isConnected,
    sendMessage,
    lastMessage,
    error,
    connect,
    disconnect,
    connectionState,
  }
}
