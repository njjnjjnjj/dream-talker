import { ref, provide, inject, readonly, computed, type Ref } from 'vue'
import { translations } from '../utils/translations'
import { type Language } from '../types'

interface LanguageContextType {
  language: Readonly<Ref<Language>>
  setLanguage: (lang: Language) => void
  t: Readonly<Ref<typeof translations.en>>
}

const LanguageSymbol = Symbol('LanguageContext')

export const provideLanguage = () => {
  const language = ref<Language>('zh')

  const setLanguage = (lang: Language) => {
    language.value = lang
  }

  const t = computed(() => translations[language.value])

  const value: LanguageContextType = {
    language: readonly(language),
    setLanguage,
    t: readonly(t),
  }

  provide(LanguageSymbol, value)
}

export const useLanguage = () => {
  debugger
  const context = inject<LanguageContextType>(LanguageSymbol)
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider')
  }
  return context
}
