import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../services/api';
import { VideoStatus } from '../types/video';

export function useVideoStatus(videoId: string | null) {
  const [statusData, setStatusData] = useState<VideoStatus | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const pollTimerRef = useRef<any>(null);

  const fetchStatus = useCallback(async () => {
    if (!videoId) return;
    try {
      const data = await api.getVideoStatus(videoId);
      setStatusData(data);
      setError(null);
      return data;
    } catch (err: any) {
      console.error('Error fetching video status:', err);
      setError(err?.response?.data?.detail || err.message || 'Failed to fetch status');
      return null;
    }
  }, [videoId]);

  useEffect(() => {
    if (!videoId) {
      setStatusData(null);
      return;
    }

    setIsLoading(true);
    let isMounted = true;

    const check = async () => {
      const data = await fetchStatus();
      if (!isMounted) return;
      setIsLoading(false);

      if (data && (data.status === 'pending' || data.status === 'processing')) {
        pollTimerRef.current = setTimeout(check, 1500);
      }
    };

    check();

    return () => {
      isMounted = false;
      if (pollTimerRef.current) {
        clearTimeout(pollTimerRef.current);
      }
    };
  }, [videoId, fetchStatus]);

  return {
    statusData,
    isLoading,
    error,
    refetch: fetchStatus,
    isCompleted: statusData?.status === 'completed',
    isFailed: statusData?.status === 'failed',
    isProcessing: statusData?.status === 'processing' || statusData?.status === 'pending',
  };
}

