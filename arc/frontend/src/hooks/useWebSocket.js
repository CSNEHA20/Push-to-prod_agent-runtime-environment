import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Custom hook to maintain a WebSocket connection to the ARC runtime API
 * ws://localhost:8000/ws/sessions/{sessionId}
 * 
 * Auto-reconnects on disconnect and maintains an event buffer.
 * 
 * @param {string} sessionId - Active session ID to subscribe to
 * @returns {{ events: Array, isConnected: boolean, lastEvent: Object|null }}
 */
export default function useWebSocket(sessionId) {
  const [events, setEvents] = useState([]);
  const [lastEvent, setLastEvent] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const connect = useCallback(() => {
    if (!sessionId) return;

    // Use environment variable or fallback to localhost:8000
    const wsHost = window.location.hostname || 'localhost';
    const wsUrl = `ws://${wsHost}:8000/ws/sessions/${sessionId}`;

    try {
      const ws = new WebSocket(wsUrl);
      socketRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        console.log(`[WebSocket] Connected to session ${sessionId}`);
      };

      ws.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          setLastEvent(data);
          setEvents((prev) => [data, ...prev].slice(0, 100)); // Keep latest 100 events
        } catch (err) {
          console.warn('[WebSocket] Failed to parse message data:', e.data);
        }
      };

      ws.onerror = (err) => {
        console.warn('[WebSocket] Connection error:', err);
      };

      ws.onclose = () => {
        setIsConnected(false);
        console.log('[WebSocket] Connection closed. Reconnecting in 3s...');
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 3000);
      };
    } catch (err) {
      console.warn('[WebSocket] Exception during initialization:', err);
      setIsConnected(false);
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, 5000);
    }
  }, [sessionId]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [connect]);

  return { events, isConnected, lastEvent };
}
