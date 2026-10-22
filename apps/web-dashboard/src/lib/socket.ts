import { io, type ManagerOptions, type Socket, type SocketOptions } from "socket.io-client";

import { API_BASE_URL } from "./config";

let socket: Socket | null = null;

export function getSocket(): Socket {
  if (!socket) {
    // With no base URL, connect to the page's own origin and let the dev
    // proxy forward /socket.io. Deployed, connect straight to the API host.
    const options: Partial<ManagerOptions & SocketOptions> = {
      transports: ["websocket"],
      autoConnect: true,
    };
    socket = API_BASE_URL ? io(API_BASE_URL, options) : io(options);
  }
  return socket;
}

export function disconnectSocket() {
  socket?.disconnect();
  socket = null;
}
