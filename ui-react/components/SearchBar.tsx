import React from 'react';
import { Search, Star } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';

interface SearchBarProps {
  searchTerm: string;
  onSearchChange: (term: string) => void;
  showFavoritesOnly: boolean;
  onToggleFavorites: () => void;
}

const SearchBar: React.FC<SearchBarProps> = ({ 
  searchTerm, 
  onSearchChange, 
  showFavoritesOnly, 
  onToggleFavorites 
}) => {
  const { t } = useLanguage();

  return (
    <div className="flex gap-3 mb-6 bg-slate-900/50 p-2 rounded-xl border border-slate-800">
      <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
        <input 
          type="text" 
          value={searchTerm}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder={t.search.placeholder}
          className="w-full bg-slate-800 text-slate-200 pl-10 pr-4 py-2 rounded-lg border border-transparent focus:border-indigo-500 focus:outline-none transition-all placeholder:text-slate-600"
        />
      </div>
      <button 
        onClick={onToggleFavorites}
        className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-all border ${
          showFavoritesOnly 
            ? 'bg-amber-500/10 text-amber-400 border-amber-500/50' 
            : 'bg-slate-800 text-slate-400 border-transparent hover:text-slate-200'
        }`}
        title={t.search.onlyFavorites}
      >
        <Star size={18} fill={showFavoritesOnly ? "currentColor" : "none"} />
        <span className="hidden sm:inline text-sm font-medium">{t.search.onlyFavorites}</span>
      </button>
    </div>
  );
};

export default SearchBar;