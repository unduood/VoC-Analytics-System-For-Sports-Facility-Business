import { useEffect, useState, useCallback, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { getSocket, disconnectSocket, WebSocketMessage } from '@/lib/socket';
import { feedbackKeys } from './useFeedback';

export type ConnectionStatus = 'connected' | 'disconnected' | 'connecting' | 'error';

interface UseRealtimeReturn {
  isConnected: boolean;
  connectionStatus: ConnectionStatus;
  lastUpdate: Date | null;
  reconnect: () => void;
}

export function useRealtime(): UseRealtimeReturn {
  const queryClient = useQueryClient();
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const processedMessages = useRef<Set<string>>(new Set());

  const handleNewFeedback = useCallback((message: WebSocketMessage) => {
    // Deduplicate by message_id
    if (processedMessages.current.has(message.meta.message_id)) return;
    processedMessages.current.add(message.meta.message_id);

    // Invalidate queries to refresh data
    queryClient.invalidateQueries({ queryKey: feedbackKeys.lists() });
    queryClient.invalidateQueries({ queryKey: feedbackKeys.dashboard() });
    setLastUpdate(new Date());
  }, [queryClient]);

  const handleAnalysisCompleted = useCallback((message: WebSocketMessage) => {
    // Deduplicate by message_id
    if (processedMessages.current.has(message.meta.message_id)) return;
    processedMessages.current.add(message.meta.message_id);

    const feedbackId = message.data.feedback_id;

    // Invalidate specific feedback detail
    queryClient.invalidateQueries({ queryKey: feedbackKeys.detail(feedbackId) });
    // Also refresh lists and dashboard
    queryClient.invalidateQueries({ queryKey: feedbackKeys.lists() });
    queryClient.invalidateQueries({ queryKey: feedbackKeys.dashboard() });
    // Invalidate all trend queries using prefix match (more efficient than individual calls)
    queryClient.invalidateQueries({ queryKey: [...feedbackKeys.all, 'trends'] });

    setLastUpdate(new Date());
  }, [queryClient]);

  const handleAnalysisFailed = useCallback((message: WebSocketMessage) => {
    // Deduplicate by message_id
    if (processedMessages.current.has(message.meta.message_id)) return;
    processedMessages.current.add(message.meta.message_id);

    const feedbackId = message.data.feedback_id;

    if (process.env.NODE_ENV === 'development') {
      console.warn('[WebSocket] Analysis failed for feedback:', feedbackId, message.data.error_message);
    }

    // Invalidate specific feedback detail to update status to 'failed'
    queryClient.invalidateQueries({ queryKey: feedbackKeys.detail(feedbackId) });
    // Also refresh lists to show updated status
    queryClient.invalidateQueries({ queryKey: feedbackKeys.lists() });

    setLastUpdate(new Date());
  }, [queryClient]);

  const reconnect = useCallback(() => {
    const socket = getSocket();
    if (!socket.connected) {
      setConnectionStatus('connecting');
      socket.connect();
    }
  }, []);

  useEffect(() => {
    const socket = getSocket();

    // Connection handlers
    const handleConnect = () => {
      setConnectionStatus('connected');
      if (process.env.NODE_ENV === 'development') {
        console.log('[WebSocket] Connected');
      }
    };

    const handleDisconnect = (reason: string) => {
      setConnectionStatus('disconnected');
      if (process.env.NODE_ENV === 'development') {
        console.log('[WebSocket] Disconnected:', reason);
      }
    };

    const handleConnectError = (error: Error) => {
      setConnectionStatus('error');
      if (process.env.NODE_ENV === 'development') {
        console.error('[WebSocket] Connection error:', error.message);
      }
    };

    const handleReconnectAttempt = () => {
      setConnectionStatus('connecting');
    };

    // Register event handlers
    socket.on('connect', handleConnect);
    socket.on('disconnect', handleDisconnect);
    socket.on('connect_error', handleConnectError);
    socket.io.on('reconnect_attempt', handleReconnectAttempt);

    // Business event handlers
    socket.on('feedback:new', handleNewFeedback);
    socket.on('feedback:completed', handleAnalysisCompleted);
    socket.on('feedback:failed', handleAnalysisFailed);

    // Connect
    setConnectionStatus('connecting');
    socket.connect();

    // Cleanup
    return () => {
      socket.off('connect', handleConnect);
      socket.off('disconnect', handleDisconnect);
      socket.off('connect_error', handleConnectError);
      socket.io.off('reconnect_attempt', handleReconnectAttempt);
      socket.off('feedback:new', handleNewFeedback);
      socket.off('feedback:completed', handleAnalysisCompleted);
      socket.off('feedback:failed', handleAnalysisFailed);
      disconnectSocket();
    };
  }, [handleNewFeedback, handleAnalysisCompleted, handleAnalysisFailed]);

  // Cleanup old message IDs periodically to prevent memory leak
  useEffect(() => {
    const interval = setInterval(() => {
      if (processedMessages.current.size > 1000) {
        processedMessages.current.clear();
      }
    }, 60000);
    return () => clearInterval(interval);
  }, []);

  return {
    isConnected: connectionStatus === 'connected',
    connectionStatus,
    lastUpdate,
    reconnect,
  };
}
