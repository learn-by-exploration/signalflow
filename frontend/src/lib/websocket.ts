/**
 * WebSocket client for real-time signal and market updates.
 */

import { WS_URL } from './constants';
import type { WSMessage } from './types';

export class SignalWebSocket {
  private ws: WebSocket | null = null;
  private reconnectInterval = 3000;
  private maxReconnectAttempts = 10;
  private reconnectAttempts = 0;
  private pingInterval: ReturnType<typeof setInterval> | null = null;
  private onMessage: (msg: WSMessage) => void;

  constructor(onMessage: (msg: WSMessage) => void) {
    this.onMessage = onMessage;
  }

  connect(markets: string[] = ['stock', 'crypto', 'forex']): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    this.ws = new WebSocket(`${WS_URL}/ws/signals`);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
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
      this.scheduleReconnect(markets);
    };

    this.ws.onerror = () => {
      this.ws?.close();
    };
  }

  disconnect(): void {
    this.stopPingHandler();
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent reconnect
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
