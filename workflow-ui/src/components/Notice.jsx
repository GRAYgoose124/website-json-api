import React, { useState, useEffect } from 'react';
import { AlertCircle, CheckCircle, Info, AlertTriangle, X, Settings } from 'lucide-react';

const Notice = ({ notice, onDismiss }) => {
  const [progress, setProgress] = useState(100);
  const [isExiting, setIsExiting] = useState(false);
  
  useEffect(() => {
    if (notice.auto_dismiss_seconds) {
      const interval = setInterval(() => {
        setProgress(prev => {
          if (prev <= 0) {
            handleDismiss();
            return 0;
          }
          return prev - (100 / (notice.auto_dismiss_seconds * 10));
        });
      }, 100);
      return () => clearInterval(interval);
    }
  }, [notice.auto_dismiss_seconds]);

  const handleDismiss = () => {
    setIsExiting(true);
    setTimeout(() => onDismiss(notice.id), 200);
  };

  const icons = {
    error: <AlertCircle className="w-4 h-4" />,
    warning: <AlertTriangle className="w-4 h-4" />,
    info: <Info className="w-4 h-4" />,
    success: <CheckCircle className="w-4 h-4" />,
    debug: <Settings className="w-4 h-4" />
  };

  const colors = {
    error: 'from-red-500/20 to-red-600/20 border-red-500/50 text-red-200',
    warning: 'from-orange-500/20 to-orange-600/20 border-orange-500/50 text-orange-200',
    info: 'from-blue-500/20 to-blue-600/20 border-blue-500/50 text-blue-200',
    success: 'from-green-500/20 to-green-600/20 border-green-500/50 text-green-200',
    debug: 'from-purple-500/20 to-purple-600/20 border-purple-500/50 text-purple-200'
  };

  return (
    <div className={`relative overflow-hidden rounded-lg border backdrop-blur-md bg-gradient-to-br ${colors[notice.type]} p-3 transition-all duration-200 ${isExiting ? 'opacity-0 translate-x-full scale-95' : 'opacity-100 translate-x-0 scale-100'} shadow-lg`}>
      <div className="flex items-start space-x-2">
        <div className="flex-shrink-0 mt-0.5">{icons[notice.type]}</div>
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-sm truncate">{notice.title}</h4>
          <p className="text-xs opacity-90 mt-1 line-clamp-2">{notice.message}</p>
          {notice.step_id && (
            <span className="text-xs opacity-70 mt-1 inline-block bg-black/20 px-2 py-0.5 rounded">
              {notice.step_id.replace(/_/g, ' ')}
            </span>
          )}
        </div>
        {notice.dismissible && (
          <button 
            onClick={handleDismiss} 
            className="opacity-70 hover:opacity-100 transition-opacity p-1 rounded hover:bg-white/10"
          >
            <X className="w-3 h-3" />
          </button>
        )}
      </div>
      {notice.auto_dismiss_seconds && (
        <div className="absolute bottom-0 left-0 h-0.5 bg-white/30 transition-all duration-100 rounded-b-lg" style={{ width: `${progress}%` }} />
      )}
    </div>
  );
};

export default Notice; 