import React, { useState, useEffect } from 'react';
import { 
  Calendar, Lightbulb, Zap, Heart, CheckSquare, Users, 
  ArrowLeft, Home, Menu, X, Coffee, Sparkles, BookOpen, Bookmark, AlertTriangle, CalendarDays, ArrowUpDown, Megaphone, FolderOpen
} from 'lucide-react';
import { generateContent, generateTextContent } from './services/geminiService'; // Ensure generateTextContent is exported in geminiService
import { AppView, PlanningItem, MediaItem } from './types';
import OutputCard from './components/OutputCard';
import Loader from './components/Loader';
import PlanEditor from './components/PlanEditor';
import CalendarView from './components/CalendarView';
import PromotionHub from './components/PromotionHub';
import MediaLibrary from './components/MediaLibrary';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<AppView>(AppView.DASHBOARD);
  const [results, setResults] = useState<PlanningItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [userInput, setUserInput] = useState('');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  // Specific inputs for different tools
  const [selectedCategory, setSelectedCategory] = useState('General');
  
  // Planning Horizon (Single, Monthly, Quarterly)
  const [planningHorizon, setPlanningHorizon] = useState<'Single' | 'Monthly' | 'Quarterly'>('Single');

  // Persistence State
  const [savedItems, setSavedItems] = useState<PlanningItem[]>(() => {
    try {
      const saved = localStorage.getItem('youthconnect_saved_plans');
      return saved ? JSON.parse(saved) : [];
    } catch (e) { return []; }
  });

  const [mediaItems, setMediaItems] = useState<MediaItem[]>(() => {
    try {
      const saved = localStorage.getItem('youthconnect_media');
      return saved ? JSON.parse(saved) : [];
    } catch (e) { return []; }
  });

  // Sorting State for Saved Items
  const [sortOption, setSortOption] = useState<string>('newest');

  // Deletion Confirmation State
  const [itemToDelete, setItemToDelete] = useState<PlanningItem | null>(null);

  // Editor State
  const [editingItem, setEditingItem] = useState<PlanningItem | null>(null);

  // Active Context
  const [activeContextTitle, setActiveContextTitle] = useState('');

  // --- Persistence Handlers ---

  const toggleSaveItem = (item: PlanningItem) => {
    const exists = savedItems.find(i => 
      (item.id && i.id === item.id) || 
      (!item.id && i.title === item.title && i.description === item.description)
    );
    
    if (exists) {
      setItemToDelete(exists);
    } else {
      const itemToSave = { 
        ...item, 
        id: item.id || crypto.randomUUID(),
        savedAt: Date.now() 
      };
      
      const newSavedItems = [itemToSave, ...savedItems];
      setSavedItems(newSavedItems);
      localStorage.setItem('youthconnect_saved_plans', JSON.stringify(newSavedItems));
      setResults(prev => prev.map(r => r === item ? itemToSave : r));
    }
  };

  const handleUpdateItem = (updatedItem: PlanningItem) => {
    setResults(prev => prev.map(i => 
      (i.id === updatedItem.id) || (i.title === updatedItem.title && i.description === updatedItem.description) 
        ? updatedItem : i
    ));

    const savedIndex = savedItems.findIndex(i => 
      (updatedItem.id && i.id === updatedItem.id) || 
      (!updatedItem.id && i.title === updatedItem.title && i.description === updatedItem.description)
    );

    if (savedIndex !== -1) {
      const newSaved = [...savedItems];
      newSaved[savedIndex] = updatedItem;
      setSavedItems(newSaved);
      localStorage.setItem('youthconnect_saved_plans', JSON.stringify(newSaved));
    }
  };

  const handleSaveEditedItem = (editedItem: PlanningItem) => {
    const itemWithId = { ...editedItem, id: editedItem.id || crypto.randomUUID() };
    const existingIndex = savedItems.findIndex(i => i.id === itemWithId.id);

    if (existingIndex !== -1) {
      const newSaved = [...savedItems];
      newSaved[existingIndex] = itemWithId;
      setSavedItems(newSaved);
      localStorage.setItem('youthconnect_saved_plans', JSON.stringify(newSaved));
    } else {
      const newSaved = [{ ...itemWithId, savedAt: Date.now() }, ...savedItems];
      setSavedItems(newSaved);
      localStorage.setItem('youthconnect_saved_plans', JSON.stringify(newSaved));
    }

    setResults(prev => prev.map(i => 
      (i.id === itemWithId.id) || (i.title === editedItem.title && i.description === editedItem.description) 
        ? itemWithId : i
    ));

    setEditingItem(null); 
  };

  const handleSaveMedia = (item: MediaItem) => {
    // Determine category based on context if not set
    const itemWithCat = { ...item, category: item.category || activeContextTitle || 'Uncategorized' };
    const newMedia = [itemWithCat, ...mediaItems];
    setMediaItems(newMedia);
    localStorage.setItem('youthconnect_media', JSON.stringify(newMedia));
  };

  const handleUpdateMedia = (updatedItem: MediaItem) => {
    const newMedia = mediaItems.map(i => i.id === updatedItem.id ? updatedItem : i);
    setMediaItems(newMedia);
    localStorage.setItem('youthconnect_media', JSON.stringify(newMedia));
  };

  const handleDeleteMedia = (id: string) => {
    const newMedia = mediaItems.filter(i => i.id !== id);
    setMediaItems(newMedia);
    localStorage.setItem('youthconnect_media', JSON.stringify(newMedia));
  };

  const confirmDelete = () => {
    if (itemToDelete) {
      const newSavedItems = savedItems.filter(i => 
        (itemToDelete.id && i.id !== itemToDelete.id) ||
        (!itemToDelete.id && (i.title !== itemToDelete.title || i.description !== itemToDelete.description))
      );
      setSavedItems(newSavedItems);
      localStorage.setItem('youthconnect_saved_plans', JSON.stringify(newSavedItems));
      setItemToDelete(null);
    }
  };

  const cancelDelete = () => {
    setItemToDelete(null);
  };

  const isSaved = (item: PlanningItem) => {
    return savedItems.some(i => 
      (item.id && i.id === item.id) ||
      (!item.id && i.title === item.title && i.description === item.description)
    );
  };

  const handleMoveEvent = (item: PlanningItem, newDate: string) => {
      const updatedItem = { ...item, assignedDate: newDate };
      handleUpdateItem(updatedItem);
  };
  
  const handleGenerate = async (promptContext: string) => {
    setLoading(true);
    setResults([]);
    try {
      const data = await generateContent(promptContext);
      const dataWithIds = data.map(d => ({...d, id: crypto.randomUUID()}));
      setResults(dataWithIds);
    } catch (error) {
      console.error(error);
      alert("Something went wrong. Please check your connection and try again.");
    } finally {
      setLoading(false);
    }
  };

  // Generic text generator wrapper for features like Promotion Hub
  const handleTextGenerate = async (prompt: string): Promise<string> => {
      try {
          return await generateTextContent(prompt);
      } catch (e) {
          console.error(e);
          return "Error generating text. Please try again.";
      }
  };

  const navTo = (view: AppView) => {
    setCurrentView(view);
    if (view === AppView.DASHBOARD) {
        setResults([]);
        setUserInput('');
        setPlanningHorizon('Single');
        setActiveContextTitle('');
    }
    setMobileMenuOpen(false);
  };

  // --- UI Components ---

  const renderHeader = () => (
    <header className="bg-emerald-700 text-white shadow-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2 cursor-pointer" onClick={() => navTo(AppView.DASHBOARD)}>
          <div className="bg-yellow-400 p-1.5 rounded-lg">
            <Zap className="text-emerald-800" size={20} fill="currentColor" />
          </div>
          <span className="text-xl font-bold tracking-tight">YouthConnect</span>
        </div>
        
        <nav className="hidden md:flex space-x-4 items-center">
          <button onClick={() => navTo(AppView.DASHBOARD)} className="hover:text-yellow-300 transition-colors">Home</button>
          <button onClick={() => navTo(AppView.PLANNING)} className="hover:text-yellow-300 transition-colors">Plan</button>
          <button onClick={() => navTo(AppView.IDEAS)} className="hover:text-yellow-300 transition-colors">Ideas</button>
          <button onClick={() => navTo(AppView.PROMOTION)} className="hover:text-yellow-300 transition-colors">Promotion</button>
          <button onClick={() => navTo(AppView.MEDIA)} className="hover:text-yellow-300 transition-colors">Library</button>
          <button onClick={() => navTo(AppView.CALENDAR)} className="hover:text-yellow-300 transition-colors flex items-center gap-1">
             <Calendar size={16} /> Calendar
          </button>
          <button onClick={() => navTo(AppView.SAVED)} className="flex items-center gap-1 bg-emerald-800 px-3 py-1.5 rounded-full hover:bg-emerald-900 transition-colors border border-emerald-600 ml-2">
             <Bookmark size={14} /> Saved ({savedItems.length})
          </button>
        </nav>

        <button className="md:hidden" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
          {mobileMenuOpen ? <X /> : <Menu />}
        </button>
      </div>

      {mobileMenuOpen && (
        <div className="md:hidden bg-emerald-800 p-4 space-y-4">
           <button onClick={() => navTo(AppView.DASHBOARD)} className="block w-full text-left py-2 hover:bg-emerald-700 rounded px-2">Home</button>
           <button onClick={() => navTo(AppView.PLANNING)} className="block w-full text-left py-2 hover:bg-emerald-700 rounded px-2">Plan Event</button>
           <button onClick={() => navTo(AppView.IDEAS)} className="block w-full text-left py-2 hover:bg-emerald-700 rounded px-2">Generator</button>
           <button onClick={() => navTo(AppView.PROMOTION)} className="block w-full text-left py-2 hover:bg-emerald-700 rounded px-2">Promotion Hub</button>
           <button onClick={() => navTo(AppView.MEDIA)} className="block w-full text-left py-2 hover:bg-emerald-700 rounded px-2">Media Library</button>
           <button onClick={() => navTo(AppView.CALENDAR)} className="block w-full text-left py-2 hover:bg-emerald-700 rounded px-2 flex items-center gap-2"><Calendar size={16} /> Calendar</button>
           <button onClick={() => navTo(AppView.SAVED)} className="flex items-center gap-2 w-full text-left py-2 hover:bg-emerald-700 rounded px-2 font-semibold">
              <Bookmark size={16} /> Saved Plans ({savedItems.length})
           </button>
        </div>
      )}
    </header>
  );

  const renderDashboard = () => (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">Welcome, Leader!</h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Equipping your ministry with culturally relevant ideas, structured plans, and spiritual depth.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <DashboardCard 
          icon={<Calendar size={32} />} 
          title="Plan Events" 
          desc="Monthly planners, templates, and seasonal guides."
          color="bg-blue-500"
          onClick={() => navTo(AppView.PLANNING)}
        />
        <DashboardCard 
          icon={<Lightbulb size={32} />} 
          title="Idea Generator" 
          desc="Games, fundraisers, and fresh outreach ideas."
          color="bg-yellow-500"
          onClick={() => navTo(AppView.IDEAS)}
        />
        <DashboardCard 
          icon={<Megaphone size={32} />} 
          title="Content & Promotion" 
          desc="Posters, scripts, and social media tools."
          color="bg-purple-500"
          onClick={() => navTo(AppView.PROMOTION)}
        />
        <DashboardCard 
          icon={<CalendarDays size={32} />} 
          title="Calendar" 
          desc="Manage schedule, drag & drop events."
          color="bg-teal-500"
          onClick={() => navTo(AppView.CALENDAR)}
        />
         <DashboardCard 
          icon={<FolderOpen size={32} />} 
          title="Media Library" 
          desc="Access saved scripts, captions, and posters."
          color="bg-pink-500"
          onClick={() => navTo(AppView.MEDIA)}
        />
        <DashboardCard 
          icon={<CheckSquare size={32} />} 
          title="Execution Coach" 
          desc="Turn big ideas into step-by-step task lists."
          color="bg-red-500"
          onClick={() => navTo(AppView.EXECUTION)}
        />
      </div>
    </div>
  );

  const renderInputSection = (title: string, subtitle: string, placeholder: string, onSubmit: () => void, options?: { label: string, value: string }[], showCategory = true, showPlanningHorizon = false) => (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <button onClick={() => navTo(AppView.DASHBOARD)} className="flex items-center text-gray-500 hover:text-emerald-700 mb-6 transition-colors">
        <ArrowLeft size={18} className="mr-1" /> Back to Dashboard
      </button>
      <div className="bg-white rounded-2xl shadow-xl p-6 md:p-8 mb-8 border-t-4 border-emerald-500">
        <div className="flex items-start justify-between flex-wrap gap-4 mb-2">
          <div><h2 className="text-2xl font-bold text-gray-900">{title}</h2><p className="text-gray-600 mt-1">{subtitle}</p></div>
          {showPlanningHorizon && (
            <div className="bg-gray-100 p-1 rounded-lg flex text-sm font-medium">
              <button onClick={() => { setPlanningHorizon('Single'); setResults([]); }} className={`px-3 py-1.5 rounded-md transition-all ${planningHorizon === 'Single' ? 'bg-white text-emerald-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}>Single Event</button>
              <button onClick={() => { setPlanningHorizon('Monthly'); setResults([]); }} className={`px-3 py-1.5 rounded-md transition-all ${planningHorizon === 'Monthly' ? 'bg-white text-emerald-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}>Monthly</button>
              <button onClick={() => { setPlanningHorizon('Quarterly'); setResults([]); }} className={`px-3 py-1.5 rounded-md transition-all ${planningHorizon === 'Quarterly' ? 'bg-white text-emerald-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}>Quarterly</button>
            </div>
          )}
        </div>
        <div className="space-y-5 mt-6">
          {showCategory && options && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Category / Type</label>
              <select value={selectedCategory} onChange={(e) => setSelectedCategory(e.target.value)} className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none">
                {options.map((opt) => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
              </select>
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{showPlanningHorizon && planningHorizon !== 'Single' ? `Specific Focus for this ${planningHorizon} Plan` : 'Specific Details (Optional)'}</label>
            <textarea value={userInput} onChange={(e) => setUserInput(e.target.value)} placeholder={placeholder} className="w-full p-3 border border-gray-300 rounded-lg h-24 focus:ring-2 focus:ring-emerald-500 outline-none resize-none" />
          </div>
          <button onClick={onSubmit} disabled={loading} className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-3 px-6 rounded-lg shadow transition-all flex items-center justify-center gap-2 disabled:opacity-70">
            {loading ? 'Generating...' : 'Generate'} <Zap size={18} />
          </button>
        </div>
      </div>
      {loading ? <Loader text={`Designing your ${planningHorizon.toLowerCase()} plan...`} /> : renderResults()}
    </div>
  );

  const renderResults = () => {
    if (results.length === 0) return null;
    if (currentView === AppView.PLANNING && planningHorizon !== 'Single') {
      const isQuarterly = planningHorizon === 'Quarterly';
      return (
        <div className="pb-12">
          <div className="flex items-center justify-between mb-6 border-b pb-2 border-emerald-200">
             <div className="flex items-center gap-2 text-emerald-800 font-bold text-xl"><CalendarDays size={24} /> {isQuarterly ? 'Quarterly Strategic Plan' : 'Monthly Activity Calendar'}</div>
             <div className="text-sm text-gray-500 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-100 shadow-sm">{isQuarterly ? '3-Month View' : '4-Week View'}</div>
          </div>
          <div className={`grid gap-4 ${isQuarterly ? 'grid-cols-1 md:grid-cols-3' : 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4'}`}>
            {results.map((item, index) => (
                <div key={index} className="flex flex-col h-full animate-in fade-in slide-in-from-bottom-4 duration-500" style={{ animationDelay: `${index * 100}ms` }}>
                  <OutputCard item={item} isSaved={isSaved(item)} onToggleSave={() => toggleSaveItem(item)} onUpdate={handleUpdateItem} onEdit={() => setEditingItem(item)} compact={true} label={isQuarterly ? `Month ${index + 1}` : `Week ${index + 1}`} />
                </div>
            ))}
          </div>
        </div>
      );
    }
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pb-12">
        {results.map((item, index) => (
          <OutputCard key={index} item={item} isSaved={isSaved(item)} onToggleSave={() => toggleSaveItem(item)} onUpdate={handleUpdateItem} onEdit={() => setEditingItem(item)}
            onOpenPromotion={() => { setActiveContextTitle(item.title); navTo(AppView.PROMOTION); }}
          />
        ))}
      </div>
    );
  };

  const renderSavedView = () => (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-8 gap-4">
        <div className="flex items-center">
          <button onClick={() => navTo(AppView.DASHBOARD)} className="flex items-center text-gray-500 hover:text-emerald-700 transition-colors mr-4"><ArrowLeft size={18} className="mr-1" /> Back</button>
          <div className="flex items-center gap-2 text-emerald-800 font-bold text-xl"><Bookmark fill="currentColor" /> Saved Plans</div>
        </div>
      </div>
      {savedItems.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-2xl shadow-sm border border-dashed border-gray-300">
          <Bookmark size={48} className="mx-auto text-gray-300 mb-4" />
          <h3 className="text-xl font-medium text-gray-900 mb-2">No saved plans yet</h3>
          <button onClick={() => navTo(AppView.PLANNING)} className="bg-emerald-600 text-white px-6 py-2 rounded-lg hover:bg-emerald-700 transition-colors">Start Planning</button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pb-12">
          {savedItems.map((item, index) => (
            <OutputCard key={index} item={item} isSaved={true} onToggleSave={() => toggleSaveItem(item)} onUpdate={handleUpdateItem} onEdit={() => setEditingItem(item)} 
                onOpenPromotion={() => { setActiveContextTitle(item.title); navTo(AppView.PROMOTION); }}
            />
          ))}
        </div>
      )}
    </div>
  );

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      {renderHeader()}
      <main className="flex-grow pt-4">
        {currentView === AppView.DASHBOARD && renderDashboard()}
        {currentView === AppView.SAVED && renderSavedView()}
        {currentView === AppView.CALENDAR && <CalendarView items={savedItems} onMoveEvent={handleMoveEvent} onEditEvent={(item) => setEditingItem(item)} />}
        {currentView === AppView.PLANNING && renderInputSection("Event & Seasonal Planner", "Create structured plans.", "e.g., 'Planning for Easter Sunday'...", () => {
             // Logic repeated for brevity - handled in handlePlanningSubmit
             let prompt = "";
             const baseContext = `Context: ${userInput || 'General activities'}. `;
             if (planningHorizon === 'Monthly') {
               prompt = `Generate a 4-week schedule for ${selectedCategory}. ${baseContext} Return 4 items titled 'Week 1...', etc.`;
             } else if (planningHorizon === 'Quarterly') {
               prompt = `Generate a 3-month plan for ${selectedCategory}. ${baseContext} Return 3 items titled 'Month 1...', etc.`;
             } else {
               prompt = `Generate a single plan for ${selectedCategory}. ${baseContext}`;
             }
             handleGenerate(prompt);
        }, [{ label: 'General Meeting', value: 'General Meeting' }, { label: 'Bible Study', value: 'Bible Study' }, { label: 'Prayer Meeting', value: 'Prayer Meeting' }, { label: 'Outreach', value: 'Outreach' }, { label: 'Camp', value: 'Camp' }, { label: 'Seasonal', value: 'Seasonal' }], true, true)}
        
        {currentView === AppView.IDEAS && renderInputSection("Idea Generator", "Fresh, culturally relevant ideas.", "e.g., 'Rainy Friday night'...", () => {
             const prompt = `Generate 3 ideas for: ${selectedCategory}. Context: Jamaican youth ministry. Preference: ${userInput || 'Any'}.`;
             handleGenerate(prompt);
        }, [{ label: 'General Fun', value: 'General' }, { label: 'Fundraiser', value: 'Fundraiser' }, { label: 'Game', value: 'Game' }, { label: 'Outreach', value: 'Outreach' }])}
        
        {[AppView.SPIRITUAL, AppView.EXECUTION, AppView.COMMUNITY].includes(currentView) && renderInputSection(
            currentView === AppView.SPIRITUAL ? "Spiritual Growth" : currentView === AppView.EXECUTION ? "Execution Coach" : "Community Builder",
            currentView === AppView.SPIRITUAL ? "Interactive teaching tools." : currentView === AppView.EXECUTION ? "Action plans." : "Foster connection.",
            "Describe details...",
            () => {
                 if (currentView === AppView.SPIRITUAL) handleGenerate(`3 spiritual ideas for: "${selectedCategory}". Relatable for Jamaican teens.`);
                 if (currentView === AppView.EXECUTION) handleGenerate(`Execution plan for: "${userInput}". Steps, roles, timeline.`);
                 if (currentView === AppView.COMMUNITY) handleGenerate(`3 community building ideas for: ${selectedCategory}.`);
            },
            currentView !== AppView.EXECUTION ? [{ label: 'Option 1', value: '1' }] : [], 
            currentView !== AppView.EXECUTION
        )}

        {currentView === AppView.PROMOTION && (
            <div className="p-4">
                <PromotionHub 
                    initialContext={activeContextTitle}
                    onGenerate={handleTextGenerate}
                    onSaveToLibrary={handleSaveMedia}
                    onClose={() => navTo(AppView.DASHBOARD)}
                />
            </div>
        )}

        {currentView === AppView.MEDIA && (
            <div className="p-4">
                <MediaLibrary 
                    items={mediaItems}
                    onUpdateItem={handleUpdateMedia}
                    onDeleteItem={handleDeleteMedia}
                    onClose={() => navTo(AppView.DASHBOARD)}
                />
            </div>
        )}
      </main>
      <footer className="bg-emerald-900 text-emerald-200 py-6 text-center"><p className="text-sm">© {new Date().getFullYear()} YouthConnect Jamaica.</p></footer>
      {itemToDelete && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
            <h3 className="text-xl font-bold mb-2">Remove Plan?</h3>
            <p className="mb-6">Are you sure?</p>
            <div className="flex gap-3"><button onClick={cancelDelete} className="flex-1 px-4 py-2 bg-gray-100 rounded-lg">Cancel</button><button onClick={confirmDelete} className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg">Remove</button></div>
          </div>
        </div>
      )}
      {editingItem && <PlanEditor item={editingItem} onSave={handleSaveEditedItem} onCancel={() => setEditingItem(null)} />}
    </div>
  );
};

const DashboardCard: React.FC<{ icon: React.ReactNode; title: string; desc: string; color: string; onClick: () => void; }> = ({ icon, title, desc, color, onClick }) => (
  <button onClick={onClick} className="bg-white p-6 rounded-2xl shadow-md hover:shadow-xl transition-all duration-300 border border-gray-100 flex flex-col items-start text-left group hover:-translate-y-1">
    <div className={`${color} text-white p-3 rounded-xl mb-4 shadow-sm group-hover:scale-110 transition-transform`}>{icon}</div>
    <h3 className="text-xl font-bold text-gray-900 mb-2">{title}</h3>
    <p className="text-gray-600 leading-relaxed">{desc}</p>
  </button>
);

export default App;
