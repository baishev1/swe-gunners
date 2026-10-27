import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

import en from './locales/en.json'
import kk from './locales/kk.json'
import ru from './locales/ru.json'

export const LANGUAGES = ['kk', 'ru', 'en'] as const

type Language = (typeof LANGUAGES)[number]

const STORAGE_KEY = 'language'

function isLanguage(value: string | null): value is Language {
  return LANGUAGES.some((language) => language === value)
}

function readStoredLanguage(): Language {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (isLanguage(stored)) return stored
  } catch {
    return 'ru'
  }
  return 'ru'
}

void i18n.use(initReactI18next).init({
  resources: { kk: { translation: kk }, ru: { translation: ru }, en: { translation: en } },
  lng: readStoredLanguage(),
  fallbackLng: 'en',
  interpolation: { escapeValue: false },
})

document.documentElement.lang = i18n.language

i18n.on('languageChanged', (language) => {
  document.documentElement.lang = language
  try {
    localStorage.setItem(STORAGE_KEY, language)
  } catch {
    return
  }
})

export { i18n }
