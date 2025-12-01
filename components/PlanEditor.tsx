
import React, { useState, useEffect } from 'react';
import { PlanningItem } from '../types';
import { X, Save, Plus, Trash2, Calendar, Users, UserCheck, Repeat } from 'lucide-react';
import DatePicker from './DatePicker';

interface PlanEditorProps {
  item: PlanningItem;
  onSave: (item: PlanningItem) => void;
  onCancel: () => void;
}

const PlanEditor: React.FC<PlanEditorProps> = ({ item, onSave, onCancel }) => {
  // Initialize state with item properties or defaults
  const [formData, setFormData] = useState<PlanningItem>({
    ...item,
    id: item.id || crypto.randomUUID(),
    materialsNeeded: item.materialsNeeded || [],
    steps: item.steps || [],
    roles: item.roles || [],
    assignedTeamMembers: item.assignedTeamMembers || [],
    notes: item.notes || '',
    recurrence: item.recurrence || 'None'
  });

  const handleChange = (field: keyof PlanningItem, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleArrayChange = (field: 'materialsNeeded' | 'steps' | 'roles' | 'assignedTeamMembers', index: number, value: string) => {
    const newArray = [...(formData[field] || [])];
    newArray[index] = value;
    setFormData(prev => ({ ...prev, [field]: newArray }));
  };

  const addArrayItem = (field: 'materialsNeeded' | 'steps' | 'roles' | 'assignedTeamMembers') => {
    setFormData(prev => ({ ...prev, [field]: [...(prev[field] || []), ''] }));
  };

  const removeArrayItem = (field: 'materialsNeeded' | 'steps' | 'roles' | 'assignedTeamMembers', index: number) => {
    setFormData(prev => ({
      ...prev,
      [field]: (prev[field] || []).filter((_, i) => i !== index)
    }));
  };

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center p-4 bg-gray-900/50 backdrop-blur-sm overflow-y-auto">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col animate-in fade-in zoom-in duration-200">
        
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-100 sticky top-0 bg-white z-10 rounded-t-2xl">
          <h2 className="text-2xl font-bold text-gray-800">Edit Plan</h2>
          <button onClick={onCancel} className="text-gray-400 hover:text-gray-600 p-1 rounded-full hover:bg-gray-100">
            <X size={24} />
          </button>
        </div>

        {/* Form Content */}
        <div className="p-6 overflow-y-auto space-y-6">
          
          {/* Title & Description */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => handleChange('title', e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => handleChange('description', e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-lg h-24 focus:ring-2 focus:ring-emerald-500 outline-none resize-y"
              />
            </div>
          </div>

          {/* Meta Data Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Duration</label>
              <input
                type="text"
                value={formData.suggestedDuration}
                onChange={(e) => handleChange('suggestedDuration', e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none"
              />
            </div>
             <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Assigned Date</label>
              <div className="w-full p-2 border border-gray-300 rounded-lg focus-within:ring-2 focus-within:ring-emerald-500">
                <DatePicker
                    value={formData.assignedDate || ''}
                    onChange={(date) => handleChange('assignedDate', date)}
                    className="w-full"
                />
              </div>
            </div>
             <div>
              <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
                <Repeat size={14} /> Recurrence
              </label>
              <select
                value={formData.recurrence || 'None'}
                onChange={(e) => handleChange('recurrence', e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none"
              >
                <option value="None">None</option>
                <option value="Weekly">Weekly</option>
                <option value="Monthly">Monthly</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Difficulty</label>
              <select
                value={formData.difficultyLevel}
                onChange={(e) => handleChange('difficultyLevel', e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none"
              >
                <option value="Low">Low</option>
                <option value="Medium">Medium</option>
                <option value="High">High</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Estimated Cost</label>
              <select
                value={formData.estimatedCost}
                onChange={(e) => handleChange('estimatedCost', e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none"
              >
                <option value="Free">Free</option>
                <option value="Low">Low</option>
                <option value="Medium">Medium</option>
                <option value="High">High</option>
              </select>
            </div>
          </div>

          <div>
             <label className="block text-sm font-medium text-gray-700 mb-1">Scripture Reference</label>
              <input
                type="text"
                value={formData.scriptureReference}
                onChange={(e) => handleChange('scriptureReference', e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none"
              />
          </div>

          {/* Dynamic Lists */}
          <div className="space-y-6">
            <DynamicList 
              title="Action Steps" 
              items={formData.steps} 
              onChange={(idx, val) => handleArrayChange('steps', idx, val)}
              onAdd={() => addArrayItem('steps')}
              onRemove={(idx) => removeArrayItem('steps', idx)}
            />
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <DynamicList 
                  title="Team Roles" 
                  items={formData.roles || []} 
                  onChange={(idx, val) => handleArrayChange('roles', idx, val)}
                  onAdd={() => addArrayItem('roles')}
                  onRemove={(idx) => removeArrayItem('roles', idx)}
                  icon={<Users size={14} className="mr-1" />}
                />

                <DynamicList 
                  title="Assigned Team Members" 
                  items={formData.assignedTeamMembers || []} 
                  onChange={(idx, val) => handleArrayChange('assignedTeamMembers', idx, val)}
                  onAdd={() => addArrayItem('assignedTeamMembers')}
                  onRemove={(idx) => removeArrayItem('assignedTeamMembers', idx)}
                  icon={<UserCheck size={14} className="mr-1" />}
                />
            </div>

            <DynamicList 
              title="Materials Needed" 
              items={formData.materialsNeeded} 
              onChange={(idx, val) => handleArrayChange('materialsNeeded', idx, val)}
              onAdd={() => addArrayItem('materialsNeeded')}
              onRemove={(idx) => removeArrayItem('materialsNeeded', idx)}
            />
          </div>

          {/* Notes */}
          <div>
             <label className="block text-sm font-medium text-gray-700 mb-1">Notes / Checklist</label>
             <textarea
                value={formData.notes}
                onChange={(e) => handleChange('notes', e.target.value)}
                placeholder="Add extra notes, reminders, or specific checklist items here..."
                className="w-full p-2 border border-gray-300 rounded-lg h-24 focus:ring-2 focus:ring-emerald-500 outline-none resize-y"
              />
          </div>

        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-100 bg-gray-50 rounded-b-2xl flex justify-end gap-3">
          <button 
            onClick={onCancel}
            className="px-6 py-2.5 rounded-lg text-gray-600 hover:bg-gray-200 font-medium transition-colors"
          >
            Cancel
          </button>
          <button 
            onClick={() => onSave(formData)}
            className="px-6 py-2.5 rounded-lg bg-emerald-600 text-white font-semibold hover:bg-emerald-700 shadow-lg transition-colors flex items-center gap-2"
          >
            <Save size={18} /> Save Changes
          </button>
        </div>

      </div>
    </div>
  );
};

// Helper for dynamic inputs
const DynamicList: React.FC<{
  title: string;
  items: string[];
  onChange: (index: number, value: string) => void;
  onAdd: () => void;
  onRemove: (index: number) => void;
  icon?: React.ReactNode;
  placeholder?: string;
}> = ({ title, items, onChange, onAdd, onRemove, icon, placeholder }) => (
  <div>
    <div className="flex items-center justify-between mb-2">
      <div className="flex items-center gap-1">
        {icon}
        <label className="text-sm font-medium text-gray-700">{title}</label>
      </div>
      <button onClick={onAdd} className="text-xs text-emerald-600 hover:text-emerald-700 flex items-center font-medium">
        <Plus size={14} className="mr-1" /> Add Item
      </button>
    </div>
    <div className="space-y-2">
      {items.map((item, idx) => (
        <div key={idx} className="flex gap-2">
          <input
            type="text"
            value={item}
            onChange={(e) => onChange(idx, e.target.value)}
            className="flex-grow p-2 text-sm border border-gray-300 rounded-lg focus:ring-1 focus:ring-emerald-500 outline-none"
            placeholder={placeholder}
          />
          <button 
            onClick={() => onRemove(idx)}
            className="text-gray-400 hover:text-red-500 p-2"
            title="Remove item"
          >
            <Trash2 size={16} />
          </button>
        </div>
      ))}
      {items.length === 0 && (
        <p className="text-xs text-gray-400 italic">No items added.</p>
      )}
    </div>
  </div>
);

export default PlanEditor;
