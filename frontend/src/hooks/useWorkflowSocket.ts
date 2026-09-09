import { useEffect, useRef, useCallback } from "react";
import { useWorkflowStore } from "@/store/workflowStore";
import type { WorkflowEvent } from "@/types/workflow";

/**
 * WebSocket hook handling all 14 event types from the enhanced event system.
 * Reconnects on disconnect with exponential backoff (1s, 2s, 4s, max 30s).
 * No polling — pure WebSocket.
 */
export function useWorkflowSocket(workflowId: string | null) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>();
  const reconnectAttemptRef = useRef(0);
  const mountedRef = useRef(true);

  const store = useWorkflowStore();

  const connect = useCallback(() => {
    if (!workflowId || !mountedRef.current) return;

    // Close existing socket
    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.onmessage = null;
      wsRef.current.onerror = null;
      if (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING) {
        wsRef.current.close();
      }
    }

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsHost = import.meta.env.VITE_WS_URL || `${protocol}//localhost:8000`;
    const url = `${wsHost}/ws/${workflowId}`;

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!mountedRef.current) { ws.close(); return; }
        reconnectAttemptRef.current = 0;
        store.setConnected(true);
      };

      ws.onmessage = (event) => {
        if (!mountedRef.current) return;
        try {
          const msg: WorkflowEvent = JSON.parse(event.data);
          handleEvent(msg);
        } catch (e) {
          console.error("[WS] Parse error:", e);
        }
      };

      ws.onclose = () => {
        store.setConnected(false);
        if (mountedRef.current) {
          scheduleReconnect();
        }
      };

      ws.onerror = () => {
        // onclose will fire after this, triggering reconnect
      };
    } catch (e) {
      console.error("[WS] Connection error:", e);
      if (mountedRef.current) scheduleReconnect();
    }
  }, [workflowId]);

  const scheduleReconnect = useCallback(() => {
    const attempt = reconnectAttemptRef.current;
    const delay = Math.min(1000 * Math.pow(2, attempt), 30000); // 1s, 2s, 4s, 8s, 16s, 30s max
    reconnectAttemptRef.current = attempt + 1;

    console.log(`[WS] Reconnecting in ${delay}ms (attempt ${attempt + 1})`);

    reconnectTimeoutRef.current = setTimeout(() => {
      if (mountedRef.current) connect();
    }, delay);
  }, [connect]);

  useEffect(() => {
    mountedRef.current = true;
    if (workflowId) {
      reconnectAttemptRef.current = 0;
      connect();
    }

    return () => {
      mountedRef.current = false;
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
      }
    };
  }, [workflowId, connect]);

  return null; // All state lives in the store
}

// ── Event router ─────────────────────────────────────────────────────────

function handleEvent(msg: WorkflowEvent) {
  const { event_type, agent_name, data } = msg;
  const store = useWorkflowStore.getState();

  switch (event_type) {
    case "workflow_started":
      store.handleWorkflowStarted(data);
      break;

    case "agent_started":
      store.handleAgentStarted(agent_name, data);
      break;

    case "agent_substep":
      store.handleAgentSubstep(agent_name, data);
      break;

    case "agent_completed":
      store.handleAgentCompleted(agent_name, data);
      break;

    case "agent_failed":
      store.handleAgentFailed(agent_name, data);
      break;

    case "company_discovered":
      store.handleCompanyDiscovered(data);
      break;

    case "company_validated":
      store.handleCompanyValidated(data);
      break;

    case "company_rejected":
      store.handleCompanyRejected(data);
      break;

    case "tech_detected":
      store.handleTechDetected(data);
      break;

    case "contact_found":
      store.handleContactFound(data);
      break;

    case "qualification_scored":
      store.handleQualificationScored(data);
      break;

    case "recommendation_created":
      store.handleRecommendationCreated(data);
      break;

    case "workflow_completed":
      store.handleWorkflowCompleted(data);
      break;

    case "workflow_failed":
      store.handleWorkflowFailed(data);
      break;

    default:
      // Unknown event type — log and ignore
      console.debug("[WS] Unknown event type:", event_type);
  }
}
