import { useEffect, useMemo, useState } from "react";

import { API_URL } from "../utils/api";
import { useAuth } from "./auth-context";
import { RealtimeContext } from "./realtime-context";

function websocketUrl() {
  const url = new URL(API_URL, window.location.origin);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = `${url.pathname.replace(/\/$/, "")}/ws`;
  url.search = "";
  url.hash = "";
  return url.toString();
}

export function RealtimeProvider({ children }) {
  const { accessToken, authStatus } = useAuth();
  const [lastEvent, setLastEvent] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState("disconnected");

  useEffect(() => {
    if (authStatus !== "authenticated" || !accessToken) {
      return undefined;
    }

    let socket;
    let reconnectTimer;
    let heartbeatTimer;
    let stopped = false;
    let reconnectDelay = 1000;

    const connect = () => {
      setConnectionStatus("connecting");
      socket = new WebSocket(websocketUrl());

      socket.addEventListener("open", () => {
        socket.send(JSON.stringify({ type: "authenticate", token: accessToken }));
      });

      socket.addEventListener("message", (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "authenticated") {
          reconnectDelay = 1000;
          setConnectionStatus("connected");
          heartbeatTimer = window.setInterval(() => {
            if (socket.readyState === WebSocket.OPEN) {
              socket.send(JSON.stringify({ type: "ping" }));
            }
          }, 25000);
          return;
        }
        if (data.type === "message.created") {
          setLastEvent({ ...data, receivedAt: Date.now() });
        }
      });

      socket.addEventListener("close", () => {
        window.clearInterval(heartbeatTimer);
        if (stopped) return;
        setConnectionStatus("reconnecting");
        reconnectTimer = window.setTimeout(connect, reconnectDelay);
        reconnectDelay = Math.min(reconnectDelay * 2, 30000);
      });

      socket.addEventListener("error", () => socket.close());
    };

    connect();
    return () => {
      stopped = true;
      window.clearTimeout(reconnectTimer);
      window.clearInterval(heartbeatTimer);
      socket?.close();
    };
  }, [accessToken, authStatus]);

  const effectiveStatus = authStatus === "authenticated"
    ? connectionStatus
    : "disconnected";
  const value = useMemo(
    () => ({ lastEvent, connectionStatus: effectiveStatus }),
    [lastEvent, effectiveStatus],
  );

  return <RealtimeContext.Provider value={value}>{children}</RealtimeContext.Provider>;
}
