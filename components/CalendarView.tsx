
import React, { useState, useEffect } from 'react';
import { PlanningItem } from '../types';
import { ChevronLeft, ChevronRight, Package, Repeat, Undo, CheckCircle, X, Share2 } from 'lucide-react';

interface CalendarViewProps {
  items: PlanningItem[];
  onMoveEvent: (item: PlanningItem, newDate: string) => void;
  onEditEvent: (item: PlanningItem) => void;
}

const CalendarView: React.FC<CalendarViewProps> = ({ items, onMoveEvent, onEditEvent }) => {
  const [currentDate, setCurrentDate] = useState(new Date());
  
  // Drag and Drop Visual State
  const [dragOverDate, setDragOverDate] = useState<string | null>(null);
  
  // Undo State
  const [undoData, setUndoData] = useState<{ itemId: string, originalDate: string, title: string } | null>(null);
  const [showUndo, setShowUndo] = useState(false);

  // Auto-hide undo toast
  useEffect(() => {
    if (showUndo) {
      const timer = setTimeout(() => setShowUndo(false), 5000);
      return () => clearTimeout(timer);
    }
  }, [showUndo]);

  // Navigation
  const prevMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
  };
  const nextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
  };
  const today = () => {
    setCurrentDate(new Date());
  };

  // Calendar Logic
  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();
  const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const firstDayOfMonth = new Date(year, month, 1).getDay(); // 0 = Sun

  const daysArray = [];
  // Empty slots for previous month
  for (let i = 0; i < firstDayOfMonth; i++) {
    daysArray.push(null);
  }
  // Days of current month
  for (let i = 1; i <= daysInMonth; i++) {
    daysArray.push(new Date(year, month, i));
  }

  const getEventsForDay = (date: Date) => {
    const dateStr = date.toISOString().split('T')[0];
    
    // 1. Exact matches
    const exactMatches = items.filter(item => item.assignedDate === dateStr);
    
    // 2. Recurrence matches
    const recurringMatches = items.filter(item => {
      // Must have a start date and recurrence set
      if (!item.assignedDate || !item.recurrence || item.recurrence === 'None') return false;
      
      const startDate = new Date(item.assignedDate);
      // If the recurring event started after this calendar date, don't show it yet
      if (startDate > date) return false;

      // Avoid duplicates if it's the exact start date (already covered by exactMatches)
      if (item.assignedDate === dateStr) return false;

      if (item.recurrence === 'Weekly') {
        // Same day of the week (0-6)
        return startDate.getUTCDay() === date.getUTCDay();
      }
      
      if (item.recurrence === 'Monthly') {
        // Same day of the month (1-31)
        return startDate.getUTCDate() === date.getUTCDate();
      }
      
      return false;
    });

    return [...exactMatches, ...recurringMatches];
  };

  const handleShare = async () => {
    let shareText = `YouthConnect Ministry Plan - ${monthNames[month]} ${year}\n\n`;
    let hasEvents = false;

    for (let i = 1; i <= daysInMonth; i++) {
        const date = new Date(year, month, i);
        const dayEvents = getEventsForDay(date);
        
        if (dayEvents.length > 0) {
            hasEvents = true;
            shareText += `📅 ${monthNames[month]} ${i} (${['Sun','Mon','Tue','Wed','Thu','Fri','Sat'][date.getDay()]}):\n`;
            dayEvents.forEach(e => {
                shareText += `   • ${e.title} (${e.suggestedDuration})\n`;
            });
            shareText += '\n';
        }
    }

    if (!hasEvents) {
        alert("No events scheduled for this month.");
        return;
    }

    if (navigator.share) {
      try {
        await navigator.share({
          title: `Ministry Schedule - ${monthNames[month]} ${year}`,
          text: shareText,
        });
      } catch (e) {
        // Ignore abort errors
      }
    } else {
      await navigator.clipboard.writeText(shareText);
      alert("Calendar schedule copied to clipboard!");
    }
  };

  const handleDragStart = (e: React.DragEvent, item: PlanningItem) => {
    if (item.id) {
        e.dataTransfer.setData('application/youthconnect-event-id', item.id);
        e.dataTransfer.effectAllowed = 'move';
    }
  };

  const handleDragEnd = () => {
    setDragOverDate(null);
  };

  const handleDragEnter = (e: React.DragEvent, date: Date) => {
    e.preventDefault();
    setDragOverDate(date.toISOString());
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (e: React.DragEvent, date: Date) => {
    e.preventDefault();
    setDragOverDate(null);
    const itemId = e.dataTransfer.getData('application/youthconnect-event-id');
    const item = items.find(i => i.id === itemId);
    
    if (item) {
        const newDateStr = date.toISOString().split('T')[0];
        const oldDateStr = item.assignedDate || '';

        // Only process if date actually changed
        if (newDateStr !== oldDateStr) {
            // Save state for undo
            setUndoData({
                itemId: item.id!,
                originalDate: oldDateStr,
                title: item.title
            });
            setShowUndo(true);

            // Execute move
            onMoveEvent(item, newDateStr);
        }
    }
  };

  const performUndo = () => {
      if (undoData) {
          const item = items.find(i => i.id === undoData.itemId);
          if (item) {
              onMoveEvent(item, undoData.originalDate);
              setShowUndo(false);
              setUndoData(null);
          }
      }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 relative">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-center mb-6 gap-4">
        <h2 className="text-3xl font-bold text-gray-800 flex items-center gap-2">
            <span className="text-emerald-600">{monthNames[month]}</span> {year}
        </h2>
        
        <div className="flex items-center gap-2">
            <button 
                onClick={handleShare} 
                className="p-2 bg-white border border-emerald-200 hover:bg-emerald-50 rounded-lg text-emerald-700 transition-colors shadow-sm"
                title="Share Monthly Schedule"
            >
                <Share2 size={20} />
            </button>
            <div className="flex items-center bg-white rounded-lg shadow-sm border border-gray-200 p-1">
            <button onClick={prevMonth} className="p-2 hover:bg-gray-100 rounded-lg text-gray-600"><ChevronLeft size={20} /></button>
            <button onClick={today} className="px-4 py-2 text-sm font-medium hover:bg-gray-100 rounded-lg text-gray-700">Today</button>
            <button onClick={nextMonth} className="p-2 hover:bg-gray-100 rounded-lg text-gray-600"><ChevronRight size={20} /></button>
            </div>
        </div>
      </div>

      {/* Grid */}
      <div className="bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden">
        {/* Days of Week Header */}
        <div className="grid grid-cols-7 bg-emerald-50 border-b border-gray-200">
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
            <div key={day} className="py-3 text-center text-sm font-semibold text-emerald-800 uppercase tracking-wider">
              {day}
            </div>
          ))}
        </div>

        {/* Calendar Body */}
        <div className="grid grid-cols-7 auto-rows-fr bg-gray-200 gap-px border-b border-gray-200">
            {daysArray.map((date, index) => {
                if (!date) {
                    return <div key={`empty-${index}`} className="bg-gray-50 min-h-[120px]"></div>;
                }

                const events = getEventsForDay(date);
                const isToday = new Date().toDateString() === date.toDateString();
                const isDragTarget = dragOverDate === date.toISOString();

                return (
                    <div 
                        key={date.toISOString()}
                        className={`
                          bg-white min-h-[120px] p-2 relative transition-all duration-200
                          ${isToday ? 'bg-emerald-50/50' : ''}
                          ${isDragTarget ? 'bg-emerald-100 ring-inset ring-2 ring-emerald-400' : ''}
                        `}
                        onDragEnter={(e) => handleDragEnter(e, date)}
                        onDragOver={handleDragOver}
                        onDrop={(e) => handleDrop(e, date)}
                    >
                        <span className={`text-sm font-medium block mb-1 ${isToday ? 'bg-emerald-600 text-white w-6 h-6 rounded-full flex items-center justify-center' : 'text-gray-700'}`}>
                            {date.getDate()}
                        </span>
                        
                        <div className="space-y-1.5">
                            {events.map((event, idx) => {
                                // Check if this is a ghost instance (recurring but not original date)
                                const isRecurringInstance = event.recurrence && event.recurrence !== 'None' && event.assignedDate !== date.toISOString().split('T')[0];

                                return (
                                <div 
                                    key={`${event.id}-${date.getDate()}-${idx}`}
                                    draggable={!isRecurringInstance} // Only allow dragging the original for now
                                    onDragStart={(e) => handleDragStart(e, event)}
                                    onDragEnd={handleDragEnd}
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      onEditEvent(event);
                                    }}
                                    className={`group border text-xs p-2 rounded-md cursor-pointer hover:shadow-md hover:scale-[1.02] active:scale-95 transition-all duration-200 shadow-sm
                                      ${isRecurringInstance 
                                        ? 'bg-emerald-50 border-emerald-100 text-emerald-800 border-dashed' 
                                        : 'bg-emerald-100 border-emerald-200 text-emerald-900'}
                                    `}
                                    title={isRecurringInstance ? "Recurring Event (Click to edit series)" : "Click to edit, Drag to reschedule"}
                                >
                                    <div className="font-semibold truncate pr-1 leading-tight flex items-center gap-1">
                                      {isRecurringInstance && <Repeat size={10} className="shrink-0 opacity-50" />}
                                      {event.title}
                                    </div>
                                    <div className="flex justify-between items-center mt-1">
                                      <div className="text-[10px] opacity-75 truncate">{event.suggestedDuration}</div>
                                      {event.materialsNeeded && event.materialsNeeded.length > 0 && (
                                        <div 
                                          className="text-emerald-700 hover:text-emerald-900"
                                          title={`Materials Needed:\n• ${event.materialsNeeded.join('\n• ')}`}
                                        >
                                          <Package size={12} strokeWidth={2.5} />
                                        </div>
                                      )}
                                    </div>
                                </div>
                            )})}
                        </div>
                    </div>
                );
            })}
        </div>
      </div>
       <div className="mt-4 text-center text-sm text-gray-500">
        <p>Tip: Drag events to reschedule, click to edit full plan details. Dashed items are recurring.</p>
      </div>

      {/* Undo Toast */}
      {showUndo && undoData && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[100] animate-in slide-in-from-bottom-5 fade-in duration-300">
          <div className="bg-gray-900 text-white px-4 py-3 rounded-lg shadow-xl flex items-center gap-4">
            <div className="flex items-center gap-2">
              <CheckCircle size={18} className="text-emerald-400" />
              <span className="text-sm truncate max-w-[200px]">Moved <strong>{undoData.title}</strong></span>
            </div>
            <div className="flex items-center gap-3 border-l border-gray-700 pl-4">
              <button 
                onClick={performUndo}
                className="text-sm font-medium text-emerald-400 hover:text-emerald-300 flex items-center gap-1 transition-colors"
              >
                <Undo size={14} /> Undo
              </button>
              <button 
                onClick={() => setShowUndo(false)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <X size={14} />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CalendarView;
