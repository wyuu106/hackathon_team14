import { createContext, useContext } from "react";

export const RealtimeContext = createContext(null);

export function useRealtime() {
  const context = useContext(RealtimeContext);
  if (!context) throw new Error("useRealtimeはRealtimeProvider内で使用してください");
  return context;
}
