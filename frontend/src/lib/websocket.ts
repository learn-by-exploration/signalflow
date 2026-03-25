/**
 * WebSocket client for real-time signal and market updates.
 */

import { WS_URL } from './constants';
import type { WSMessage } from './types';

export type ConnectionStatus = 'connecting' | 'connected' | 'reconnecting' | 'disconnected';

export class SignalWebSocket {
  private ws: WebSocket | null = null;
  private reconnectInterval = 3000;
  private maxReconnectAttempts = 10;
  private reconnectAttempts = 0;
  private pingInterval: ReturnType<typeof setInterval> | null = null;
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
    let wsUrl = `${WS_URL}/ws/signals`;
    if (typeof window !== 'undefined') {
      const token = sessionStorage.getItem('signalflow_access_token');
      if (token) {
        wsUrl += `?token=${encodeURIComponent(token)}`;
      }
    }
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.onStatusChange?.('connected');
      // Subscribe to markets
      this.ws?.send(JSON.stringify({ type: 'subscribe', markets }));
      // Start pong responder
      this.startPingHandler();
    };

    this.ws.onmessage = (event) => {
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
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent reconnect
    this.onStatusChange?.('disconnected');
    this.ws?.close();
    this.ws = null;
  }

  private scheduleReconnect(markets: string[]): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return;
    this.reconnectAttempts++;
    setTimeout(() => this.connect(markets), this.reconnectInterval);
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
}
