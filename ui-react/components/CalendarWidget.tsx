import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { getMonthlyActivity } from '../services/mockData';
import { MonthlyActivity } from '../types';

interface CalendarWidgetProps {
  selectedDate: Date;
  onSelectDate: (date: Date) => void;
}

const CalendarWidget: React.FC<CalendarWidgetProps> = ({ selectedDate, onSelectDate }) => {
  const { t, language } = useLanguage();
  const [currentMonth, setCurrentMonth] = useState(new Date(selectedDate));
  const [activityData, setActivityData] = useState<MonthlyActivity>({});

  // Reset to selected date's month when opened or changed externally
  useEffect(() => {
    setCurrentMonth(new Date(selectedDate));
  }, []);

  // Fetch mock data when month changes
  useEffect(() => {
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();
    const data = getMonthlyActivity(year, month);
    setActivityData(data);
  }, [currentMonth]);

  const handlePrevMonth = () => {
    const newDate = new Date(currentMonth);
    newDate.setMonth(currentMonth.getMonth() - 1);
    setCurrentMonth(newDate);
  };

  const handleNextMonth = () => {
    const newDate = new Date(currentMonth);
    newDate.setMonth(currentMonth.getMonth() + 1);
    setCurrentMonth(newDate);
  };

  const handleDateClick = (day: number) => {
    const newDate = new Date(currentMonth);
    newDate.setDate(day);
    onSelectDate(newDate);
  };

  const getDaysInMonth = (date: Date) => {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (date: Date) => {
    return new Date(date.getFullYear(), date.getMonth(), 1).getDay();
  };

  const daysInMonth = getDaysInMonth(currentMonth);
  const firstDay = getFirstDayOfMonth(currentMonth);
  const daysArray = Array.from({ length: daysInMonth }, (_, i) => i + 1);
  const blanksArray = Array.from({ length: firstDay }, (_, i) => i);

  const monthYearString = currentMonth.toLocaleDateString(language === 'zh' ? 'zh-CN' : 'en-US', {
    month: 'long',
    year: 'numeric'
  });

  const isSelected = (day: number) => {
    return selectedDate.getDate() === day &&
           selectedDate.getMonth() === currentMonth.getMonth() &&
           selectedDate.getFullYear() === currentMonth.getFullYear();
  };

  const isToday = (day: number) => {
    const today = new Date();
    return today.getDate() === day &&
           today.getMonth() === currentMonth.getMonth() &&
           today.getFullYear() === currentMonth.getFullYear();
  };

  return (
    <div className="bg-slate-800 rounded-b-xl border-x border-b border-slate-700 p-4 animate-in slide-in-from-top-2 duration-200">
      
      {/* Calendar Header */}
      <div className="flex justify-between items-center mb-4">
        <button onClick={handlePrevMonth} className="p-1 hover:bg-slate-700 rounded text-slate-400">
          <ChevronLeft size={20} />
        </button>
        <span className="font-bold text-slate-200">{monthYearString}</span>
        <button onClick={handleNextMonth} className="p-1 hover:bg-slate-700 rounded text-slate-400">
          <ChevronRight size={20} />
        </button>
      </div>

      {/* Weekdays */}
      <div className="grid grid-cols-7 mb-2">
        {t.date.weekdays.map((day) => (
          <div key={day} className="text-center text-xs font-semibold text-slate-500 uppercase tracking-wide">
            {day}
          </div>
        ))}
      </div>

      {/* Days Grid */}
      <div className="grid grid-cols-7 gap-1">
        {blanksArray.map((i) => (
          <div key={`blank-${i}`} className="h-10"></div>
        ))}
        
        {daysArray.map((day) => {
          const dateStr = `${currentMonth.getFullYear()}-${String(currentMonth.getMonth() + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
          const count = activityData[dateStr] || 0;
          const selected = isSelected(day);
          const today = isToday(day);

          return (
            <button
              key={day}
              onClick={() => handleDateClick(day)}
              className={`h-10 md:h-12 rounded-lg flex flex-col items-center justify-center relative transition-all border border-transparent
                ${selected 
                  ? 'bg-indigo-600 text-white shadow-lg border-indigo-500' 
                  : 'hover:bg-slate-700 text-slate-300 hover:border-slate-600'}
                ${today && !selected ? 'bg-slate-700/50 text-indigo-300 border-slate-600' : ''}
              `}
            >
              <span className={`text-sm ${selected ? 'font-bold' : ''}`}>{day}</span>
              
              {count > 0 && (
                <div className="flex items-center justify-center mt-0.5">
                   {/* Badge for count */}
                   <span className={`text-[10px] px-1.5 rounded-full font-medium ${
                     selected 
                       ? 'bg-white/20 text-white' 
                       : 'bg-indigo-500/20 text-indigo-400'
                   }`}>
                     {count}
                   </span>
                </div>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default CalendarWidget;