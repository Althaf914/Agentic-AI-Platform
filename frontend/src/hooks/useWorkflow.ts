import { useState, useEffect, useRef } from "react";
import { useWorkflowStore } from "@/store/workflowStore";
import { startWorkflow as startApi, getWorkflowStatus } from "@/api/workflows";

export function useWorkflow(workflowId?: string) {
  const { setActiveWorkflow } = useWorkflowStore();
  const [activeWorkflow, setActiveWorkflowLocal] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval>>();

  const startWorkflow = async (configId: string) => {
    const data = await startApi(configId);
    const wfId = data.workflow_id || data.id;
    setActiveWorkflow(wfId, configId);
    return { id: wfId, ...data };
  };

  // Poll workflow status every 3 seconds
  useEffect(() => {
    if (!workflowId) return;

    setIsLoading(true);
    const fetchStatus = async () => {
      try {
        const data = await getWorkflowStatus(workflowId);
        setActiveWorkflowLocal(data);
        setIsLoading(false);

        // Stop polling when workflow is done
        if (data.status === "completed" || data.status === "failed") {
          if (intervalRef.current) clearInterval(intervalRef.current);
        }
      } catch (e) {
        console.error("Failed to fetch workflow status:", e);
      }
    };

    fetchStatus();
    intervalRef.current = setInterval(fetchStatus, 3000);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [workflowId]);

  return {
    startWorkflow,
    activeWorkflow,
    status: activeWorkflow?.status,
    isLoading,
  };
}
