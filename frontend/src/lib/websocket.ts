/**
 * WebSocket client for real-time signal and market updates.
 */

import { getWsUrl } from './constants';
import type { WSMessage } from './types';

export type ConnectionStatus = 'connecting' | 'connected' | 'reconnecting' | 'disconnected';

export class SignalWebSocket {
  private ws: WebSocket | null = null;
  private maxReconnectAttempts = 10;
  private reconnectAttempts = 0;
  private pingInterval: ReturnType<typeof setInterval> | null = null;
  private heartbeatInterval: ReturnType<typeof setInterval> | null = null;
  private lastMessageAt = 0;
  private currentMarkets: string[] = [];
  private onMessage: (msg: WSMessage) => void;
  private onStatusChange?: (status: ConnectionStatus) => void;

  constructor(onMessage: (msg: WSMessage) => void, onStatusChange?: (status: ConnectionStatus) => void) {
    this.onMessage = onMessage;
    this.onStatusChange = onStatusChange;
  }

  connect(markets: string[] = ['stock', 'crypto', 'forex']): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    this.onStatusChange?.('connecting');

    // Get auth token for WebSocket connection
    let wsUrl = `${getWsUrl()}/ws/signals`;
    if (typeof window !== 'undefined') {
      const token = sessionStorage.getItem('signalflow_access_token');
      if (token) {
        wsUrl += `?token=${encodeURIComponent(token)}`;
      }
    }
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.lastMessageAt = Date.now();
      this.currentMarkets = markets;
      this.onStatusChange?.('connected');
      // Subscribe to markets
      this.ws?.send(JSON.stringify({ type: 'subscribe', markets }));
      // Start pong responder
      this.startPingHandler();
      // Start heartbeat timeout detector
      this.startHeartbeatMonitor();
    };

    this.ws.onmessage = (event) => {
      this.lastMessageAt = Date.now();
      try {
        const msg = JSON.parse(event.data) as WSMessage;
        if (msg.type === 'ping') {
          this.ws?.send(JSON.stringify({ type: 'pong' }));
          return;
        }
        this.onMessage(msg);
      } catch {
        // Ignore malformed messages
      }
    };

    this.ws.onclose = () => {
      this.stopPingHandler();
      this.stopHeartbeatMonitor();
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.onStatusChange?.('reconnecting');
      } else {
        this.onStatusChange?.('disconnected');
      }
      this.scheduleReconnect(markets);
    };

    this.ws.onerror = () => {
      this.ws?.close();
    };
  }

  disconnect(): void {
    this.stopPingHandler();
    this.stopHeartbeatMonitor();
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent reconnect
    this.onStatusChange?.('disconnected');
    this.ws?.close();
    this.ws = null;
  }

  private scheduleReconnect(markets: string[]): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return;
    const backoffMs = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    this.reconnectAttempts++;
    setTimeout(() => this.connect(markets), backoffMs);
  }

  private startPingHandler(): void {
    // No-op: server sends pings, client responds in onmessage
  }

  private stopPingHandler(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  private startHeartbeatMonitor(): void {
    this.stopHeartbeatMonitor();
    this.heartbeatInterval = setInterval(() => {
      if (this.lastMessageAt > 0 && Date.now() - this.lastMessageAt > 45000) {
        // No message received for 45s (server pings every 30s) — force reconnect
        this.stopHeartbeatMonitor();
        this.ws?.close();
      }
    }, 15000);
  }

  private stopHeartbeatMonitor(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }
}
