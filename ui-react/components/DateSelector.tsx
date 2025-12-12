import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, Calendar as CalendarIcon, ChevronDown, ChevronUp } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import CalendarWidget from './CalendarWidget';

interface DateSelectorProps {
  selectedDate: Date;
  onChange: (date: Date) => void;
}

const DateSelector: React.FC<DateSelectorProps> = ({ selectedDate, onChange }) => {
  const { t, language } = useLanguage();
  const [isCalendarOpen, setIsCalendarOpen] = useState(false);
  
  const handlePrevDay = (e: React.MouseEvent) => {
    e.stopPropagation();
    const newDate = new Date(selectedDate);
    newDate.setDate(selectedDate.getDate() - 1);
    onChange(newDate);
  };

  const handleNextDay = (e: React.MouseEvent) => {
    e.stopPropagation();
    const newDate = new Date(selectedDate);
    newDate.setDate(selectedDate.getDate() + 1);
    onChange(newDate);
  };

  const toggleCalendar = () => {
    setIsCalendarOpen(!isCalendarOpen);
  };

  const isToday = new Date().toDateString() === selectedDate.toDateString();
  const locale = language === 'zh' ? 'zh-CN' : 'en-US';

  return (
    <div className="mb-6 relative z-10">
      {/* Main Bar */}
      <div 
        className={`flex items-center justify-between bg-slate-800/80 backdrop-blur rounded-xl p-4 border border-slate-700 shadow-lg transition-all cursor-pointer hover:border-slate-600 ${isCalendarOpen ? 'rounded-b-none border-b-0' : ''}`}
        onClick={toggleCalendar}
      >
        <div className="flex items-center gap-4">
          <div className={`p-2 rounded-lg transition-colors ${isCalendarOpen ? 'bg-indigo-500 text-white' : 'bg-indigo-500/20 text-indigo-400'}`}>
            <CalendarIcon size={24} />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
              {selectedDate.toLocaleDateString(locale, { month: 'long', day: 'numeric', year: 'numeric' })}
              {isCalendarOpen ? <ChevronUp size={16} className="text-slate-500"/> : <ChevronDown size={16} className="text-slate-500"/>}
            </h2>
            <p className="text-sm text-slate-400">
              {isToday ? t.date.tonight : selectedDate.toLocaleDateString(locale, { weekday: 'long' })}
            </p>
          </div>
        </div>

        {/* Mini Navigation (only show if calendar is closed for quick access) */}
        {!isCalendarOpen && (
          <div className="flex items-center gap-2">
            <button 
              onClick={handlePrevDay}
              className="p-2 hover:bg-slate-700 rounded-lg text-slate-300 transition-colors"
            >
              <ChevronLeft size={20} />
            </button>
            <button 
              onClick={handleNextDay}
              disabled={isToday}
              className={`p-2 rounded-lg transition-colors ${
                isToday 
                  ? 'text-slate-600 cursor-not-allowed' 
                  : 'hover:bg-slate-700 text-slate-300'
              }`}
            >
              <ChevronRight size={20} />
            </button>
          </div>
        )}
      </div>

      {/* Expanded Calendar */}
      {isCalendarOpen && (
        <CalendarWidget 
          selectedDate={selectedDate} 
          onSelectDate={(date) => {
            onChange(date);
            // Optional: close on select, but keeping open is often better for exploration
            // setIsCalendarOpen(false); 
          }} 
        />
      )}
    </div>
  );
};

export default DateSelector;