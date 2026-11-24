import { useTranslation } from 'react-i18next'

import { LANGUAGES } from '@/shared/i18n'
import { NativeSelect, NativeSelectOption } from '@/shared/ui/native-select'

export function LanguageSwitcher() {
  const { t, i18n } = useTranslation()

  return (
    <NativeSelect
      size="sm"
      aria-label={t('language.label')}
      value={i18n.language}
      onChange={(event) => void i18n.changeLanguage(event.target.value)}
    >
      {LANGUAGES.map((language) => (
        <NativeSelectOption key={language} value={language}>
          {language.toUpperCase()}
        </NativeSelectOption>
      ))}
    </NativeSelect>
  )
}
