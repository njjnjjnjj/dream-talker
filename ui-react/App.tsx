import React, { useState, useEffect } from 'react';
import { Moon, BarChart2, Mic, Activity, Globe } from 'lucide-react';
import DateSelector from './components/DateSelector';
import RecordCard from './components/RecordCard';
import StatisticsPanel from './components/StatisticsPanel';
import SearchBar from './components/SearchBar';
import { generateMockRecords, getKeywordStats, getWeeklyStats, getHourlyStats, getTagStats } from './services/mockData';
import { SleepRecord, KeywordStat, DailyStats, HourlyStat, TagStat } from './types';
import { useLanguage } from './contexts/LanguageContext';

const App: React.FC = () => {
  const { t, language, setLanguage } = useLanguage();
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [records, setRecords] = useState<SleepRecord[]>([]);
  const [activeTab, setActiveTab] = useState<'daily' | 'stats'>('daily');
  
  // Stats Data State
  const [keywordData, setKeywordData] = useState<KeywordStat[]>([]);
  const [dailyStats, setDailyStats] = useState<DailyStats[]>([]);
  const [hourlyStats, setHourlyStats] = useState<HourlyStat[]>([]);
  const [tagStats, setTagStats] = useState<TagStat[]>([]);
  
  // Search and Filter State
  const [searchTerm, setSearchTerm] = useState('');
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);

  // Load data on date or language change
  useEffect(() => {
    // Simulate API fetch lag
    const timer = setTimeout(() => {
      setRecords(generateMockRecords(selectedDate, language));
      setSearchTerm(''); // Reset search on date change
    }, 300);
    return () => clearTimeout(timer);
  }, [selectedDate, language]);

  // Load static stats data
  useEffect(() => {
    setKeywordData(getKeywordStats(language));
    setDailyStats(getWeeklyStats(language));
    setHourlyStats(getHourlyStats());
    setTagStats(getTagStats(language));
  }, [language]);

  const toggleLanguage = () => {
    setLanguage(language === 'en' ? 'zh' : 'en');
  };

  const handleUpdateRecord = (id: string, updates: Partial<SleepRecord>) => {
    setRecords(prev => prev.map(rec => rec.id === id ? { ...rec, ...updates } : rec));
  };

  // Filter records based on search and favorites
  const filteredRecords = records.filter(record => {
    const matchesSearch = record.transcription.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFav = showFavoritesOnly ? record.isFavorite : true;
    return matchesSearch && matchesFav;
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950/20">
      
      {/* Header */}
      <header className="sticky top-0 z-50 bg-slate-950/80 backdrop-blur-lg border-b border-slate-800">
        <div className="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-indigo-600 p-2 rounded-lg text-white shadow-[0_0_15px_rgba(79,70,229,0.5)]">
              <Moon size={20} fill="currentColor" />
            </div>
            <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-200 to-slate-100">
              {t.appTitle}
            </h1>
          </div>
          
          <div className="flex items-center gap-4">
            <nav className="flex bg-slate-900/50 p-1 rounded-lg border border-slate-800">
              <button 
                onClick={() => setActiveTab('daily')}
                className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${
                  activeTab === 'daily' 
                    ? 'bg-indigo-600 text-white shadow-sm' 
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Mic size={16} />
                <span className="hidden sm:inline">{t.tabs.recordings}</span>
              </button>
              <button 
                onClick={() => setActiveTab('stats')}
                className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${
                  activeTab === 'stats' 
                    ? 'bg-indigo-600 text-white shadow-sm' 
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <BarChart2 size={16} />
                <span className="hidden sm:inline">{t.tabs.insights}</span>
              </button>
            </nav>

            <button
              onClick={toggleLanguage}
              className="p-2 text-slate-400 hover:text-indigo-400 hover:bg-slate-900 rounded-lg transition-colors border border-transparent hover:border-slate-800"
              title="Switch Language"
            >
              <Globe size={20} />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-4 py-8">
        
        {activeTab === 'daily' && (
          <div className="animate-in slide-in-from-bottom-4 duration-500">
            <DateSelector selectedDate={selectedDate} onChange={setSelectedDate} />
            
            <SearchBar 
              searchTerm={searchTerm} 
              onSearchChange={setSearchTerm}
              showFavoritesOnly={showFavoritesOnly}
              onToggleFavorites={() => setShowFavoritesOnly(!showFavoritesOnly)}
            />

            <div className="mb-6 flex items-center justify-between">
              <h3 className="text-slate-300 font-medium uppercase tracking-wider text-sm">
                {t.timeline.title}
              </h3>
              <span className="text-xs font-mono text-slate-500 bg-slate-900 px-2 py-1 rounded border border-slate-800">
                {filteredRecords.length} / {records.length} {t.timeline.eventsDetected}
              </span>
            </div>

            <div className="grid gap-6">
              {filteredRecords.length > 0 ? (
                filteredRecords.map(record => (
                  <RecordCard 
                    key={record.id} 
                    record={record} 
                    onUpdateRecord={handleUpdateRecord}
                  />
                ))
              ) : (
                <div className="text-center py-20 bg-slate-900/30 rounded-2xl border border-dashed border-slate-800">
                  <Activity className="mx-auto text-slate-600 mb-4 opacity-50" size={48} />
                  <p className="text-slate-500 text-lg">
                    {records.length === 0 ? t.timeline.noEvents : t.timeline.noResults}
                  </p>
                  {records.length === 0 && (
                    <p className="text-slate-600 text-sm mt-1">{t.timeline.silence}</p>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'stats' && (
          <div className="animate-in slide-in-from-bottom-4 duration-500">
            <StatisticsPanel 
              dailyStats={dailyStats} 
              hourlyStats={hourlyStats}
              tagStats={tagStats}
              keywordData={keywordData}
            />
          </div>
        )}

      </main>
    </div>
  );
};

export default App;