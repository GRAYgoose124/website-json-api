import React from 'react';
import { X } from 'lucide-react';

const Modal = ({ isOpen, onClose, title, children, size = "md" }) => {
  if (!isOpen) return null;

  const sizeClasses = {
    sm: "max-w-md",
    md: "max-w-2xl", 
    lg: "max-w-4xl",
    xl: "max-w-6xl"
  };

  return (
    <div className="fixed inset-0 bg-black flex items-center justify-center p-4 z-50">
      <div className={`bg-gray-900 border border-gray-600 shadow-2xl w-full ${sizeClasses[size]} max-h-[90vh] overflow-hidden rounded-xl`}>
        <div className="flex items-center justify-between p-4 border-b border-gray-600 bg-gray-800">
          <h2 className="text-lg font-semibold text-white">{title}</h2>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-700 transition-colors text-gray-300 hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-4 overflow-y-auto max-h-[calc(90vh-100px)] bg-gray-900">
          {children}
        </div>
      </div>
    </div>
  );
};

// Enhanced Overlay Popup Component
export const OverlayPopup = ({ isOpen, onClose, title, children, size = "md", position = "center" }) => {
  if (!isOpen) return null;

  const sizeClasses = {
    sm: "max-w-sm",
    md: "max-w-md", 
    lg: "max-w-lg",
    xl: "max-w-xl"
  };

  const positionClasses = {
    center: "items-center justify-center",
    top: "items-start justify-center pt-8",
    bottom: "items-end justify-center pb-8",
    left: "items-center justify-start pl-8",
    right: "items-center justify-end pr-8"
  };

  return (
    <div className={`fixed inset-0 bg-black/80 flex ${positionClasses[position]} p-4 z-50`}>
      <div className={`bg-gray-900 border border-gray-700 shadow-2xl w-full ${sizeClasses[size]} rounded-lg overflow-hidden animate-scale-in`}>
        <div className="flex items-center justify-between p-3 border-b border-gray-700 bg-gray-800">
          <h3 className="text-sm font-semibold text-white">{title}</h3>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-gray-700 transition-colors text-gray-300 hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="p-3 bg-gray-900">
          {children}
        </div>
      </div>
    </div>
  );
};

// Tooltip Component
export const Tooltip = ({ children, content, position = "top" }) => {
  const [isVisible, setIsVisible] = React.useState(false);

  const positionClasses = {
    top: "bottom-full left-1/2 transform -translate-x-1/2 mb-2",
    bottom: "top-full left-1/2 transform -translate-x-1/2 mt-2",
    left: "right-full top-1/2 transform -translate-y-1/2 mr-2",
    right: "left-full top-1/2 transform -translate-y-1/2 ml-2"
  };

  return (
    <div 
      className="relative inline-block"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      {children}
      {isVisible && (
        <div className={`absolute z-50 px-2 py-1 text-xs text-white bg-gray-900 border border-gray-700 rounded shadow-lg whitespace-nowrap ${positionClasses[position]}`}>
          {content}
          <div className={`absolute w-2 h-2 bg-gray-900 border border-gray-700 transform rotate-45 ${
            position === 'top' ? 'top-full left-1/2 -translate-x-1/2 -mt-1' :
            position === 'bottom' ? 'bottom-full left-1/2 -translate-x-1/2 -mb-1' :
            position === 'left' ? 'left-full top-1/2 -translate-y-1/2 -ml-1' :
            'right-full top-1/2 -translate-y-1/2 -mr-1'
          }`} />
        </div>
      )}
    </div>
  );
};

export default Modal; 