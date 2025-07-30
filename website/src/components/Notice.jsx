import React, { useState, useEffect } from 'react';
import { AlertCircle, CheckCircle, Info, AlertTriangle, X, Settings, Clock, Activity, ChevronDown, ChevronRight } from 'lucide-react';

const Notice = ({ notice, onDismiss, isCompact = false }) => {
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
    error: <AlertCircle className="w-3 h-3" />,
    warning: <AlertTriangle className="w-3 h-3" />,
    info: <Info className="w-3 h-3" />,
    success: <CheckCircle className="w-3 h-3" />,
    debug: <Settings className="w-3 h-3" />
  };

  const colors = {
    error: 'from-red-500/20 to-red-600/20 border-red-500/50 text-red-200',
    warning: 'from-orange-500/20 to-orange-600/20 border-orange-500/50 text-orange-200',
    info: 'from-blue-500/20 to-blue-600/20 border-blue-500/50 text-blue-200',
    success: 'from-green-500/20 to-green-600/20 border-green-500/50 text-green-200',
    debug: 'from-purple-500/20 to-purple-600/20 border-purple-500/50 text-purple-200'
  };

  // Compact version for grouped notices
  if (isCompact) {
    return (
      <div className={`relative overflow-hidden rounded border backdrop-blur-md bg-gradient-to-br ${colors[notice.type]} p-1.5 transition-all duration-200 ${isExiting ? 'opacity-0 translate-x-full scale-95' : 'opacity-100 translate-x-0 scale-100'} shadow-sm`}>
        <div className="flex items-center space-x-1.5">
          <div className="flex-shrink-0">{icons[notice.type]}</div>
          <div className="flex-1 min-w-0">
            <div className="font-medium text-xs truncate">{notice.title}</div>
            {notice.step_id && (
              <span className="text-xs opacity-70 inline-block bg-black/20 px-1 py-0.5 rounded text-xs">
                {notice.step_id.replace(/_/g, ' ')}
              </span>
            )}
          </div>
          {notice.dismissible && (
            <button 
              onClick={handleDismiss} 
              className="opacity-70 hover:opacity-100 transition-opacity p-0.5 rounded hover:bg-white/10"
            >
              <X className="w-2.5 h-2.5" />
            </button>
          )}
        </div>
        {notice.auto_dismiss_seconds && (
          <div className="absolute bottom-0 left-0 h-0.5 bg-white/30 transition-all duration-100 rounded-b" style={{ width: `${progress}%` }} />
        )}
      </div>
    );
  }

  // Full version for individual notices
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

// Enhanced Notice Group Component with Collapsible Sections
export const NoticeGroup = ({ notices, onDismiss }) => {
  const [collapsedGroups, setCollapsedGroups] = useState({});

  const groupNoticesByType = () => {
    const groups = {};
    notices.forEach(notice => {
      if (!groups[notice.type]) {
        groups[notice.type] = [];
      }
      groups[notice.type].push(notice);
    });
    return groups;
  };

  const getTypeIcon = (type) => {
    const icons = {
      error: <AlertCircle className="w-4 h-4" />,
      warning: <AlertTriangle className="w-4 h-4" />,
      info: <Info className="w-4 h-4" />,
      success: <CheckCircle className="w-4 h-4" />,
      debug: <Settings className="w-4 h-4" />
    };
    return icons[type];
  };

  const getTypeColor = (type) => {
    const colors = {
      error: 'text-red-400 bg-red-600/20 border-red-500/30',
      warning: 'text-orange-400 bg-orange-600/20 border-orange-500/30',
      info: 'text-blue-400 bg-blue-600/20 border-blue-500/30',
      success: 'text-green-400 bg-green-600/20 border-green-500/30',
      debug: 'text-purple-400 bg-purple-600/20 border-purple-500/30'
    };
    return colors[type];
  };

  const getTypeLabel = (type) => {
    const labels = {
      error: 'Errors',
      warning: 'Warnings', 
      info: 'Info',
      success: 'Success',
      debug: 'Debug'
    };
    return labels[type];
  };

  const toggleGroup = (type) => {
    setCollapsedGroups(prev => ({
      ...prev,
      [type]: !prev[type]
    }));
  };

  const groupedNotices = groupNoticesByType();

  if (notices.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <Info className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <h3 className="text-sm font-medium mb-1">No notices</h3>
        <p className="text-gray-400 text-xs">System notices will appear here</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-2 p-2">
      {Object.entries(groupedNotices).map(([type, typeNotices]) => (
        <div key={type} className="bg-gray-800/50 rounded-lg border border-gray-700/50 overflow-hidden">
          <button
            onClick={() => toggleGroup(type)}
            className={`w-full flex items-center justify-between px-2 py-1.5 border-b border-gray-700/50 ${getTypeColor(type)} hover:bg-gray-700/30 transition-colors`}
          >
            <div className="flex items-center gap-1.5">
              {getTypeIcon(type)}
              <span className="font-medium text-xs">{getTypeLabel(type)}</span>
              <span className="text-xs opacity-70">({typeNotices.length})</span>
            </div>
            {collapsedGroups[type] ? (
              <ChevronRight className="w-3 h-3" />
            ) : (
              <ChevronDown className="w-3 h-3" />
            )}
          </button>
          {!collapsedGroups[type] && (
            <div className="p-1.5 space-y-1 max-h-48 overflow-y-auto">
              {typeNotices.map((notice, index) => (
                <Notice 
                  key={`${notice.id}-${index}`} 
                  notice={notice} 
                  onDismiss={onDismiss}
                  isCompact={true}
                />
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default Notice; 