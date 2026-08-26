import { WebSocketMessage, ConnectionState } from '../types/market';
import { getWsBaseUrl } from './api';

export type MessageHandler = (msg: WebSocketMessage) => void;
export type StatusHandler = (status: ConnectionState, message?: string) => void;

export class MarketWebSocketClient {
  private ws: WebSocket | null = null;
  private symbol: string;
  private timeframe: string;
  private onMessageCallback: MessageHandler;
  private onStatusCallback: StatusHandler;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 50;
  private reconnectTimer: number | null = null;
  private isIntentionallyClosed = false;
  private wsBaseUrl: string;

  constructor(
    symbol: string,
    timeframe: string,
    onMessage: MessageHandler,
    onStatus: StatusHandler
  ) {
    this.symbol = symbol.toUpperCase();
    this.timeframe = timeframe;
    this.onMessageCallback = onMessage;
    this.onStatusCallback = onStatus;
    this.wsBaseUrl = getWsBaseUrl();
  }

  public connect() {
    this.isIntentionallyClosed = false;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    const endpoint = `${this.wsBaseUrl}/market/${this.symbol}/${this.timeframe}`;
    console.log(`[MarketWebSocketClient] Connecting to ${endpoint} (attempt ${this.reconnectAttempts + 1})`);
    this.onStatusCallback(this.reconnectAttempts > 0 ? 'RECONNECTING' : 'OFFLINE', 'Connecting to backend...');

    try {
      this.ws = new WebSocket(endpoint);

      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
        this.onStatusCallback('LIVE', 'Connected to real-time feed');
      };

      this.ws.onmessage = (event) => {
        try {
          const data: WebSocketMessage = JSON.parse(event.data);
          this.onMessageCallback(data);
          if (data.status?.state) {
            this.onStatusCallback(data.status.state, data.status.message);
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      this.ws.onerror = (event) => {
        console.warn('WebSocket encountered error:', event);
      };

      this.ws.onclose = (event) => {
        if (this.isIntentionallyClosed) {
          this.onStatusCallback('OFFLINE', 'Disconnected');
          return;
        }

        this.onStatusCallback('RECONNECTING', `Connection lost (${event.code}). Retrying...`);
        this.scheduleReconnect();
      };
    } catch (err) {
      console.error('WebSocket connection initialization error:', err);
      this.scheduleReconnect();
    }
  }

  public updateSubscription(symbol: string, timeframe: string) {
    if (this.symbol === symbol.toUpperCase() && this.timeframe === timeframe) {
      return;
    }
    this.symbol = symbol.toUpperCase();
    this.timeframe = timeframe;
    this.disconnect();
    this.connect();
  }

  private scheduleReconnect() {
    if (this.isIntentionallyClosed) return;
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.onStatusCallback('OFFLINE', 'Max reconnect attempts reached. Please refresh.');
      return;
    }

    const backoff = Math.min(1000 * Math.pow(1.5, this.reconnectAttempts), 15000);
    this.reconnectAttempts++;
    this.onStatusCallback('RECONNECTING', `Reconnecting in ${(backoff / 1000).toFixed(1)}s (attempt ${this.reconnectAttempts})...`);

    this.reconnectTimer = window.setTimeout(() => {
      this.connect();
    }, backoff);
  }

  public disconnect() {
    this.isIntentionallyClosed = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.onStatusCallback('OFFLINE', 'Disconnected');
  }
}
