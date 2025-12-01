
import React, { useState, useEffect, useRef } from 'react';
import { ChevronLeft, ChevronRight, Calendar as CalendarIcon, X } from 'lucide-react';

interface DatePickerProps {
  value?: string;
  onChange: (date: string) => void;
  placeholder?: string;
  className?: string;
  isDark?: boolean; // For white text on dark backgrounds
}

const DatePicker: React.FC<DatePickerProps> = ({ value, onChange, placeholder = "Select date", className = "", isDark = false }) => {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Parse initial value or default to today
  const initialDate = value ? new Date(value) : new Date();
  // Validate date
  const validDate = isNaN(initialDate.getTime()) ? new Date() : initialDate;

  const [viewDate, setViewDate] = useState(validDate);

  // Close on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // --- Holiday Logic ---
  const getJamaicanHolidays = (year: number) => {
    const holidays: Record<string, string> = {
      [`${year}-01-01`]: "New Year's Day",
      [`${year}-05-23`]: "Labour Day",
      [`${year}-08-01`]: "Emancipation Day",
      [`${year}-08-06`]: "Independence Day",
      [`${year}-12-25`]: "Christmas Day",
      [`${year}-12-26`]: "Boxing Day",
    };

    // Calculate Easter (Meeus/Jones/Butcher's algorithm)
    const a = year % 19;
    const b = Math.floor(year / 100);
    const c = year % 100;
    const d = Math.floor(b / 4);
    const e = b % 4;
    const f = Math.floor((b + 8) / 25);
    const g = Math.floor((b - f + 1) / 3);
    const h = (19 * a + b - d - g + 15) % 30;
    const i = Math.floor(c / 4);
    const k = c % 4;
    const l = (32 + 2 * e + 2 * i - h - k) % 7;
    const m = Math.floor((a + 11 * h + 22 * l) / 451);
    const month = Math.floor((h + l - 7 * m + 114) / 31);
    const day = ((h + l - 7 * m + 114) % 31) + 1;

    const easterDate = new Date(year, month - 1, day);
    
    // Format helper
    const fmt = (d: Date) => d.toISOString().split('T')[0];

    // Easter related
    const goodFriday = new Date(easterDate);
    goodFriday.setDate(easterDate.getDate() - 2);
    holidays[fmt(goodFriday)] = "Good Friday";

    const easterMonday = new Date(easterDate);
    easterMonday.setDate(easterDate.getDate() + 1);
    holidays[fmt(easterMonday)] = "Easter Monday";

    const ashWednesday = new Date(easterDate);
    ashWednesday.setDate(easterDate.getDate() - 46);
    holidays[fmt(ashWednesday)] = "Ash Wednesday";

    // National Heroes Day (3rd Monday in October)
    const oct1 = new Date(year, 9, 1); // Oct 1
    const dayOfWeek = oct1.getDay(); // 0 = Sun
    // Distance to first Monday. If Mon (1), dist 0. If Tue (2), dist 6.
    const daysToFirstMon = (8 - dayOfWeek) % 7; 
    const firstMon = 1 + daysToFirstMon;
    const thirdMon = firstMon + 14;
    holidays[`${year}-10-${String(thirdMon).padStart(2, '0')}`] = "National Heroes Day";

    return holidays;
  };

  const holidays = getJamaicanHolidays(viewDate.getFullYear());

  // --- Calendar Rendering ---
  const year = viewDate.getFullYear();
  const month = viewDate.getMonth();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const firstDayOfMonth = new Date(year, month, 1).getDay();

  const days = [];
  for (let i = 0; i < firstDayOfMonth; i++) days.push(null);
  for (let i = 1; i <= daysInMonth; i++) days.push(new Date(year, month, i));

  const handleSelectDate = (d: Date) => {
    // Adjust for timezone offset to ensure string is local YYYY-MM-DD
    const offset = d.getTimezoneOffset();
    const localDate = new Date(d.getTime() - (offset * 60 * 1000));
    onChange(localDate.toISOString().split('T')[0]);
    setIsOpen(false);
  };

  const changeMonth = (delta: number) => {
    setViewDate(new Date(year, month + delta, 1));
  };

  const changeYear = (newYear: number) => {
    setViewDate(new Date(newYear, month, 1));
  };

  const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  
  // Year selector range
  const years = [];
  const currentYear = new Date().getFullYear();
  for (let y = currentYear - 5; y <= currentYear + 5; y++) years.push(y);

  return (
    <div className={`relative ${className}`} ref={containerRef}>
      {/* Trigger Input */}
      <div 
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-2 cursor-pointer ${isDark ? 'text-emerald-50 hover:text-white' : 'text-gray-700 hover:text-emerald-700'}`}
      >
        <CalendarIcon size={16} />
        <span className={`text-sm ${!value ? 'opacity-75' : 'font-medium'}`}>
          {value ? new Date(value).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }) : placeholder}
        </span>
      </div>

      {/* Popover */}
      {isOpen && (
        <div className="absolute top-full mt-2 left-0 z-[60] bg-white rounded-lg shadow-xl border border-gray-200 p-4 w-[320px] animate-in fade-in zoom-in-95 duration-200">
          
          {/* Header */}
          <div className="flex justify-between items-center mb-4">
            <button onClick={() => changeMonth(-1)} className="p-1 hover:bg-gray-100 rounded text-gray-600"><ChevronLeft size={20} /></button>
            <div className="flex gap-2 items-center">
              <span className="font-semibold text-gray-800">{monthNames[month]}</span>
              <select 
                value={year} 
                onChange={(e) => changeYear(parseInt(e.target.value))}
                className="bg-transparent font-semibold text-emerald-700 outline-none cursor-pointer hover:bg-emerald-50 rounded px-1"
                onClick={(e) => e.stopPropagation()}
              >
                {years.map(y => <option key={y} value={y}>{y}</option>)}
              </select>
            </div>
            <button onClick={() => changeMonth(1)} className="p-1 hover:bg-gray-100 rounded text-gray-600"><ChevronRight size={20} /></button>
          </div>

          {/* Grid */}
          <div className="grid grid-cols-7 gap-1 mb-2">
            {['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'].map(d => (
              <div key={d} className="text-center text-xs font-semibold text-gray-400 py-1">{d}</div>
            ))}
            {days.map((d, i) => {
              if (!d) return <div key={`empty-${i}`} />;
              
              const dateStr = d.toISOString().split('T')[0];
              const isSelected = value === dateStr;
              const isToday = new Date().toISOString().split('T')[0] === dateStr;
              const holidayName = holidays[dateStr];

              return (
                <button
                  key={dateStr}
                  onClick={() => handleSelectDate(d)}
                  className={`
                    h-8 w-8 rounded-full flex items-center justify-center text-sm relative group
                    ${isSelected ? 'bg-emerald-600 text-white font-bold' : 'hover:bg-emerald-50 text-gray-700'}
                    ${isToday && !isSelected ? 'border border-emerald-300 font-medium' : ''}
                    ${holidayName ? 'font-semibold' : ''}
                  `}
                  title={holidayName}
                >
                  {d.getDate()}
                  {holidayName && (
                    <div className={`absolute -bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full ${isSelected ? 'bg-white' : 'bg-yellow-500'}`} />
                  )}
                  {holidayName && (
                     <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 hidden group-hover:block bg-gray-800 text-white text-[10px] px-2 py-1 rounded whitespace-nowrap z-10">
                       {holidayName}
                     </div>
                  )}
                </button>
              );
            })}
          </div>

          {/* Footer / Clear */}
          <div className="flex justify-between items-center border-t border-gray-100 pt-3 mt-2">
            <button 
              onClick={() => { onChange(''); setIsOpen(false); }}
              className="text-xs text-red-500 hover:text-red-700 font-medium"
            >
              Clear Date
            </button>
             <button 
              onClick={() => { handleSelectDate(new Date()); }}
              className="text-xs text-emerald-600 hover:text-emerald-800 font-medium"
            >
              Today
            </button>
          </div>

        </div>
      )}
    </div>
  );
};

export default DatePicker;
