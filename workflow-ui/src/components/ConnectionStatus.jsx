import React from 'react';
import { RefreshCw, Loader2 } from 'lucide-react';

const ConnectionStatus = ({ isConnected, isReconnecting, error, isAutoUpdating }) => (
  <div className={`fixed top-4 right-4 px-3 py-2 rounded-full text-xs font-medium flex items-center gap-2 backdrop-blur-md border ${
    isConnected 
      ? 'bg-green-500/20 text-green-400 border-green-500/50' 
      : isReconnecting
      ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50'
      : 'bg-red-500/20 text-red-400 border-red-500/50'
  } shadow-lg`}>
    {isReconnecting && <RefreshCw className="w-3 h-3 animate-spin" />}
    {isConnected ? (
      <>
        <div className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
        Connected
        {isAutoUpdating && (
          <span className="text-xs opacity-70">• Auto</span>
        )}
      </>
    ) : isReconnecting ? (
      <>
        <Loader2 className="w-3 h-3 animate-spin" />
        Reconnecting...
      </>
    ) : (
      <>
        <div className="w-1.5 h-1.5 bg-red-400 rounded-full" />
        Disconnected
      </>
    )}
  </div>
);

export default ConnectionStatus; 