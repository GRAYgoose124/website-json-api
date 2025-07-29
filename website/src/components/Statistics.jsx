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
      total: 'from-blue-500 to-blue-600',
      running: 'from-green-500 to-green-600',
      completed: 'from-purple-500 to-purple-600',
      failed: 'from-red-500 to-red-600',
      notices: 'from-indigo-500 to-indigo-600'
    };
    return colors[status];
  };

  const getStatusIcon = (status) => {
    const icons = {
      total: <BarChart3 className="w-4 h-4" />,
      running: <Activity className="w-4 h-4" />,
      completed: <CheckCircle className="w-4 h-4" />,
      failed: <AlertCircle className="w-4 h-4" />,
      notices: <Info className="w-4 h-4" />
    };
    return icons[status];
  };

  return (
    <div className="grid grid-cols-5 gap-2 mb-4">
      {Object.entries(stats).map(([key, value]) => (
        <div key={key} className="bg-gray-800/30 backdrop-blur-sm rounded-md p-2 border border-gray-700/50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-400 capitalize">{key}</p>
              <p className="text-sm font-bold text-white">{value}</p>
            </div>
            <div className={`p-1.5 rounded-md bg-gradient-to-br ${getStatusColor(key)}`}>
              {getStatusIcon(key)}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default Statistics; 