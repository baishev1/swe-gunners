import { useTranslation } from 'react-i18next'

import { LANGUAGES } from '@/shared/i18n'
import { ToggleGroup, ToggleGroupItem } from '@/shared/ui/toggle-group'

export function LanguageSwitcher() {
  const { t, i18n } = useTranslation()

  return (
    <ToggleGroup
      type="single"
      variant="outline"
      size="sm"
      spacing={0}
      aria-label={t('language.label')}
      value={i18n.language}
      onValueChange={(value) => value && void i18n.changeLanguage(value)}
    >
      {LANGUAGES.map((language) => (
        <ToggleGroupItem key={language} value={language}>
          {language.toUpperCase()}
        </ToggleGroupItem>
      ))}
    </ToggleGroup>
  )
}
