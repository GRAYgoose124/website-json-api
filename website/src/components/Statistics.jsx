import React from 'react';
import { BarChart3, Activity, CheckCircle, AlertCircle, Info } from 'lucide-react';

const Statistics = ({ workflows, notices }) => {
  const stats = {
    total: workflows.length,
    running: workflows.filter(w => w.status === 'running').length,
    completed: workflows.filter(w => w.status === 'completed').length,
    failed: workflows.filter(w => w.status === 'failed').length,
    notices: notices.length
  };

  const getStatusColor = (status) => {
    const colors = {
      total: 'text-blue-400 bg-blue-600/20 border-blue-500/30',
      running: 'text-green-400 bg-green-600/20 border-green-500/30',
      completed: 'text-purple-400 bg-purple-600/20 border-purple-500/30',
      failed: 'text-red-400 bg-red-600/20 border-red-500/30',
      notices: 'text-indigo-400 bg-indigo-600/20 border-indigo-500/30'
    };
    return colors[status];
  };

  const getStatusIcon = (status) => {
    const icons = {
      total: <BarChart3 className="w-3 h-3" />,
      running: <Activity className="w-3 h-3" />,
      completed: <CheckCircle className="w-3 h-3" />,
      failed: <AlertCircle className="w-3 h-3" />,
      notices: <Info className="w-3 h-3" />
    };
    return icons[status];
  };

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-2 mb-3">
      {Object.entries(stats).map(([key, value]) => (
        <div key={key} className="glass-light rounded-md p-1.5 border border-gray-700/50 card-mini">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-400 capitalize">{key}</p>
              <p className="text-sm font-bold text-white">{value}</p>
            </div>
            <div className={`p-1 rounded-md border ${getStatusColor(key)}`}>
              {getStatusIcon(key)}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default Statistics; 