
import React, { useState } from 'react';
import { MediaItem } from '../types';
import { Image, Video, Hash, MessageCircle, Send, Save, ArrowLeft, Wand2 } from 'lucide-react';
import Loader from './Loader';

interface PromotionHubProps {
  initialContext?: string; // Pre-filled event name/context
  onGenerate: (prompt: string) => Promise<string>;
  onSaveToLibrary: (item: MediaItem) => void;
  onClose: () => void;
}

type PromotionTab = 'Poster' | 'Script' | 'Caption' | 'WhatsApp';

const PromotionHub: React.FC<PromotionHubProps> = ({ initialContext = '', onGenerate, onSaveToLibrary, onClose }) => {
  const [activeTab, setActiveTab] = useState<PromotionTab>('Poster');
  const [context, setContext] = useState(initialContext);
  const [tone, setTone] = useState('Fun & Youthful');
  const [platform, setPlatform] = useState('Instagram'); // For scripts/captions
  const [messageType, setMessageType] = useState('Event Invite'); // For WhatsApp
  
  const [generatedContent, setGeneratedContent] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerate = async () => {
    if (!context) {
        alert("Please describe the event or topic first.");
        return;
    }

    setIsGenerating(true);
    let prompt = '';

    const baseInstruction = `Context: A Christian youth event in Jamaica called "${context}". Target audience: Gen Z (13-25). Tone: ${tone}. `;

    switch (activeTab) {
        case 'Poster':
            prompt = `${baseInstruction} 
            Generate a detailed design strategy for a poster/flyer. 
            Include: 1. Visual Theme/Metaphor 2. Color Palette (hex codes if possible) 3. Headline Suggestion 4. Font Style Recommendations 5. Key Iconography. 
            Make it trendy and culturally relevant to Jamaica. Format clearly.`;
            break;
        case 'Script':
            prompt = `${baseInstruction} 
            Write a short, high-energy video script for ${platform} (Reels/TikTok). 
            Include: 1. A Scroll-Stopping Hook 2. Visual/Audio cues 3. The Core Message 4. A Clear CTA. 
            Use clean Jamaican slang if appropriate. Keep it under 30 seconds.`;
            break;
        case 'Caption':
            prompt = `${baseInstruction} 
            Generate 3 caption options for social media:
            1. Short & Punchy
            2. Story/Testimonial style
            3. Engaging Question style
            Include relevant hashtags for Jamaican Christian youth.`;
            break;
        case 'WhatsApp':
            prompt = `${baseInstruction} 
            Write a ${messageType} for a WhatsApp Broadcast List.
            
            Requirements:
            - Format specifically for WhatsApp (use *bold* for emphasis, _italics_, and emojis).
            - Keep it scannable and mobile-friendly.
            - Tone: ${tone}.
            - Structure: Attention-grabbing header, Key details (Date/Time/Location), and a clear Call to Action.
            - Do not use placeholders like "Hi [Name]" as this is for a broadcast list.
            
            Provide 2 slight variations of the message.`;
            break;
    }

    const result = await onGenerate(prompt);
    setGeneratedContent(result);
    setIsGenerating(false);
  };

  const handleSave = () => {
      if (!generatedContent) return;
      onSaveToLibrary({
          id: crypto.randomUUID(),
          title: `${activeTab}: ${context.substring(0, 20)}...`,
          content: generatedContent,
          type: activeTab,
          createdAt: Date.now()
      });
      alert('Saved to Media Library!');
  };

  const tabs: { id: PromotionTab, icon: React.ReactNode, label: string, color: string }[] = [
    { id: 'Poster', icon: <Image size={18} />, label: 'Poster Strategy', color: 'bg-purple-500' },
    { id: 'Script', icon: <Video size={18} />, label: 'Social Script', color: 'bg-pink-500' },
    { id: 'Caption', icon: <Hash size={18} />, label: 'Captions', color: 'bg-blue-500' },
    { id: 'WhatsApp', icon: <MessageCircle size={18} />, label: 'WhatsApp', color: 'bg-green-500' },
  ];

  return (
    <div className="bg-white rounded-2xl shadow-xl max-w-5xl mx-auto border border-gray-200 overflow-hidden flex flex-col md:flex-row min-h-[600px] animate-in fade-in slide-in-from-bottom-4">
      
      {/* Sidebar / Controls */}
      <div className="w-full md:w-1/3 bg-gray-50 border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
             <h2 className="font-bold text-gray-800 flex items-center gap-2">
                <Wand2 className="text-purple-600" size={20} /> Promotion Hub
             </h2>
             <button onClick={onClose} className="md:hidden p-1 text-gray-500"><ArrowLeft /></button>
        </div>
        
        <div className="p-4 space-y-6 flex-grow overflow-y-auto">
             {/* Tabs */}
             <div className="grid grid-cols-2 gap-2">
                {tabs.map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`p-3 rounded-lg text-sm font-medium flex flex-col items-center gap-1 transition-all ${
                            activeTab === tab.id 
                            ? 'bg-white shadow-md text-gray-900 ring-2 ring-emerald-500' 
                            : 'hover:bg-gray-200 text-gray-600'
                        }`}
                    >
                        <div className={`${tab.color} text-white p-1.5 rounded-full`}>
                            {tab.icon}
                        </div>
                        {tab.label}
                    </button>
                ))}
             </div>

             {/* Inputs */}
             <div className="space-y-4">
                <div>
                    <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Event / Context</label>
                    <input 
                        type="text" 
                        value={context}
                        onChange={(e) => setContext(e.target.value)}
                        placeholder="e.g., Friday Night Lyme"
                        className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none"
                    />
                </div>
                
                <div>
                    <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Tone / Vibe</label>
                    <select 
                        value={tone}
                        onChange={(e) => setTone(e.target.value)}
                        className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none bg-white"
                    >
                        <option>Friendly & Welcoming</option>
                        <option>Fun & Youthful</option>
                        <option>Professional & Clear</option>
                        <option>Clean Jamaican Slang</option>
                        <option>Pastoral & Spiritual</option>
                        <option>Hype & Energetic</option>
                    </select>
                </div>

                {(activeTab === 'Script' || activeTab === 'Caption') && (
                     <div>
                        <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Platform</label>
                        <select 
                            value={platform}
                            onChange={(e) => setPlatform(e.target.value)}
                            className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none bg-white"
                        >
                            <option>Instagram</option>
                            <option>TikTok</option>
                            <option>Facebook</option>
                            <option>YouTube Shorts</option>
                        </select>
                    </div>
                )}

                {activeTab === 'WhatsApp' && (
                     <div>
                        <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Message Type</label>
                        <select 
                            value={messageType}
                            onChange={(e) => setMessageType(e.target.value)}
                            className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none bg-white"
                        >
                            <option>Event Invite</option>
                            <option>Reminder</option>
                            <option>Follow-up</option>
                            <option>Motivational Note</option>
                            <option>Broadcast Announcement</option>
                        </select>
                    </div>
                )}
             </div>

             <button 
                onClick={handleGenerate}
                disabled={isGenerating}
                className="w-full py-3 bg-purple-600 text-white font-bold rounded-xl shadow-lg hover:bg-purple-700 transition-transform active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
             >
                {isGenerating ? 'Creating Magic...' : 'Generate Content'} <Send size={16} />
             </button>
        </div>
        
        <div className="p-4 border-t border-gray-200 hidden md:block">
            <button onClick={onClose} className="w-full py-2 text-gray-500 hover:bg-gray-100 rounded-lg">Exit Hub</button>
        </div>
      </div>

      {/* Output Area */}
      <div className="w-full md:w-2/3 bg-white flex flex-col h-[500px] md:h-auto">
        <div className="p-4 border-b border-gray-200 flex justify-between items-center bg-gray-50/50">
            <h3 className="font-semibold text-gray-700">Generated Result</h3>
            {generatedContent && (
                <button 
                    onClick={handleSave}
                    className="text-sm flex items-center gap-1 bg-indigo-50 text-indigo-700 px-3 py-1.5 rounded-lg hover:bg-indigo-100 font-medium"
                >
                    <Save size={16} /> Save to Library
                </button>
            )}
        </div>
        
        <div className="flex-grow p-6 overflow-y-auto">
            {isGenerating ? (
                <div className="h-full flex items-center justify-center">
                    <Loader text="Brewing creative ideas..." />
                </div>
            ) : generatedContent ? (
                <textarea 
                    value={generatedContent}
                    onChange={(e) => setGeneratedContent(e.target.value)}
                    className="w-full h-full resize-none outline-none text-gray-800 leading-relaxed bg-transparent"
                    placeholder="Result will appear here..."
                />
            ) : (
                <div className="h-full flex flex-col items-center justify-center text-gray-400">
                    <Wand2 size={48} className="mb-4 opacity-20" />
                    <p>Select a tool and hit Generate to start.</p>
                </div>
            )}
        </div>
      </div>

    </div>
  );
};

export default PromotionHub;
