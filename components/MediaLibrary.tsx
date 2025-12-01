
import React, { useState } from 'react';
import { MediaItem } from '../types';
import { Image, FileText, MessageCircle, Mic, Trash2, Search, Filter, Copy, Edit3, ArrowLeft, Folder, FolderPlus, Save, X } from 'lucide-react';

interface MediaLibraryProps {
  items: MediaItem[];
  onUpdateItem: (item: MediaItem) => void;
  onDeleteItem: (id: string) => void;
  onClose: () => void;
}

const MediaLibrary: React.FC<MediaLibraryProps> = ({ items, onUpdateItem, onDeleteItem, onClose }) => {
  const [filterType, setFilterType] = useState<'All' | MediaItem['type']>('All');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [search, setSearch] = useState('');
  const [editingItem, setEditingItem] = useState<MediaItem | null>(null);

  // Extract unique categories
  const categories = ['All', ...Array.from(new Set(items.map(i => i.category || 'Uncategorized')))];

  const filteredItems = items.filter(item => {
    const matchesType = filterType === 'All' || item.type === filterType;
    const matchesCategory = selectedCategory === 'All' || (item.category || 'Uncategorized') === selectedCategory;
    const matchesSearch = item.title.toLowerCase().includes(search.toLowerCase()) || 
                          item.content.toLowerCase().includes(search.toLowerCase());
    return matchesType && matchesCategory && matchesSearch;
  });

  const getIcon = (type: MediaItem['type']) => {
    switch (type) {
        case 'Poster': return <Image size={20} className="text-purple-500" />;
        case 'Script': return <Mic size={20} className="text-pink-500" />;
        case 'WhatsApp': return <MessageCircle size={20} className="text-green-500" />;
        default: return <FileText size={20} className="text-blue-500" />;
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('Content copied!');
  };

  const handleSaveEdit = () => {
    if (editingItem) {
      onUpdateItem(editingItem);
      setEditingItem(null);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-xl p-6 md:p-8 max-w-6xl mx-auto border-t-4 border-indigo-500 min-h-[85vh] flex flex-col animate-in fade-in slide-in-from-bottom-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
           <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
            <Filter className="text-indigo-600" /> Media Library
           </h2>
           <p className="text-gray-500">Manage and reuse your generated content.</p>
        </div>
        <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-full text-gray-500">
          <ArrowLeft />
        </button>
      </div>

      <div className="flex flex-col lg:flex-row gap-6 h-full flex-grow">
        
        {/* Left Sidebar: Filters & Search */}
        <div className="w-full lg:w-1/4 space-y-6">
            <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <input 
                    type="text" 
                    placeholder="Search content..." 
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                />
            </div>

            <div>
                <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1">
                    <Folder size={14} /> Folders / Categories
                </h3>
                <div className="space-y-1 max-h-[200px] overflow-y-auto">
                    {categories.map(cat => (
                        <button
                            key={cat}
                            onClick={() => setSelectedCategory(cat)}
                            className={`w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition-colors flex justify-between items-center ${
                                selectedCategory === cat ? 'bg-indigo-100 text-indigo-700' : 'text-gray-600 hover:bg-gray-100'
                            }`}
                        >
                            <span className="truncate">{cat}</span>
                            {cat !== 'All' && <span className="text-xs bg-gray-200 text-gray-600 px-1.5 rounded-full">
                                {items.filter(i => (i.category || 'Uncategorized') === cat).length}
                            </span>}
                        </button>
                    ))}
                </div>
            </div>

            <div>
                <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Filter by Type</h3>
                <div className="flex flex-wrap gap-2">
                    {['All', 'Poster', 'Script', 'Caption', 'WhatsApp'].map(type => (
                        <button
                            key={type}
                            onClick={() => setFilterType(type as any)}
                            className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
                                filterType === type 
                                ? 'bg-indigo-600 text-white border-indigo-600' 
                                : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'
                            }`}
                        >
                            {type}
                        </button>
                    ))}
                </div>
            </div>
        </div>

        {/* Main Content: Grid */}
        <div className="w-full lg:w-3/4">
             {filteredItems.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-gray-400 border-2 border-dashed border-gray-200 rounded-xl p-12">
                    <FolderPlus size={48} className="mb-4 opacity-20" />
                    <p>No items found in this category.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 overflow-y-auto max-h-[70vh] pr-2">
                    {filteredItems.map(item => (
                        <div key={item.id} className="bg-gray-50 rounded-xl border border-gray-200 p-4 flex flex-col hover:shadow-md transition-shadow group relative">
                            {/* Type Badge */}
                            <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-2">
                                    {getIcon(item.type)}
                                    <span className="text-xs font-bold uppercase text-gray-500 tracking-wider">{item.type}</span>
                                </div>
                                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <button 
                                        onClick={() => setEditingItem(item)}
                                        className="p-1.5 text-gray-400 hover:text-indigo-600 rounded hover:bg-indigo-50"
                                        title="Edit"
                                    >
                                        <Edit3 size={16} />
                                    </button>
                                    <button 
                                        onClick={() => onDeleteItem(item.id)}
                                        className="p-1.5 text-gray-400 hover:text-red-500 rounded hover:bg-red-50"
                                        title="Delete"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </div>
                            </div>
                            
                            <h3 className="font-bold text-gray-800 mb-1 truncate">{item.title}</h3>
                            <div className="text-xs text-gray-400 mb-2 flex items-center gap-1">
                                <Folder size={10} /> {item.category || 'Uncategorized'}
                            </div>
                            
                            <div className="bg-white rounded border border-gray-100 p-3 text-sm text-gray-600 h-32 overflow-y-auto mb-3 whitespace-pre-wrap font-mono text-xs">
                                {item.content}
                            </div>
                            
                            <button 
                                onClick={() => copyToClipboard(item.content)}
                                className="mt-auto w-full py-2 flex items-center justify-center gap-2 text-sm font-medium text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                            >
                                <Copy size={14} /> Copy Content
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </div>

      </div>

      {/* Edit Modal */}
      {editingItem && (
        <div className="fixed inset-0 z-[70] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl p-6 animate-in fade-in zoom-in duration-200">
                <div className="flex justify-between items-center mb-4 border-b pb-4">
                    <h3 className="text-lg font-bold text-gray-800">Edit Media Item</h3>
                    <button onClick={() => setEditingItem(null)} className="text-gray-400 hover:text-gray-600">
                        <X />
                    </button>
                </div>
                
                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
                        <input 
                            type="text" 
                            value={editingItem.title}
                            onChange={(e) => setEditingItem({...editingItem, title: e.target.value})}
                            className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                        />
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Folder / Category</label>
                            <input 
                                type="text" 
                                value={editingItem.category || ''}
                                onChange={(e) => setEditingItem({...editingItem, category: e.target.value})}
                                placeholder="e.g. Easter 2024"
                                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                            />
                        </div>
                        <div>
                             <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                             <select 
                                value={editingItem.type}
                                onChange={(e) => setEditingItem({...editingItem, type: e.target.value})}
                                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none bg-white"
                             >
                                <option value="Poster">Poster</option>
                                <option value="Script">Script</option>
                                <option value="Caption">Caption</option>
                                <option value="WhatsApp">WhatsApp</option>
                             </select>
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Content</label>
                        <textarea 
                            value={editingItem.content}
                            onChange={(e) => setEditingItem({...editingItem, content: e.target.value})}
                            className="w-full h-48 p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none resize-none font-mono text-sm"
                        />
                    </div>
                </div>

                <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
                    <button onClick={() => setEditingItem(null)} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">Cancel</button>
                    <button onClick={handleSaveEdit} className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center gap-2">
                        <Save size={16} /> Save Changes
                    </button>
                </div>
            </div>
        </div>
      )}
    </div>
  );
};

export default MediaLibrary;
