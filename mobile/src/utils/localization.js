export function isZhLanguage(i18nLanguage) {
  return !!i18nLanguage && i18nLanguage.startsWith('zh');
}

// For fields that must never silently fall back to English once Chinese is selected
// (title, body content). Returns null when zh is selected but untranslated.
export function localizedOrNull(obj, field, isZh) {
  if (!obj) return null;
  return isZh ? (obj[`${field}_zh`] || null) : (obj[field] || null);
}
