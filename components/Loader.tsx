import React from 'react';
import { Loader2 } from 'lucide-react';

const Loader: React.FC<{ text?: string }> = ({ text = "Thinking..." }) => {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-emerald-600">
      <Loader2 size={48} className="animate-spin mb-4" />
      <p className="text-lg font-medium text-gray-600 animate-pulse">{text}</p>
    </div>
  );
};

export default Loader;