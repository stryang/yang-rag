export type AdminLanguage = 'zh-CN' | 'en-US'

export interface AdminUiPreferences {
  darkMode: boolean
  notificationsEnabled: boolean
  language: AdminLanguage
}

export interface ProviderConfigStorage {
  llm_provider: string
  llm_model: string
  embedding_provider: string
  embedding_model: string
  vector_store: string
  api_endpoint: string
}

const UI_PREFERENCES_KEY = 'admin-ui-preferences'
const PROVIDER_CONFIG_KEY = 'admin-provider-config'

export const DEFAULT_UI_PREFERENCES: AdminUiPreferences = {
  darkMode: false,
  notificationsEnabled: true,
  language: 'zh-CN',
}

export function getStoredUiPreferences(): AdminUiPreferences {
  try {
    const raw = localStorage.getItem(UI_PREFERENCES_KEY)
    if (!raw) {
      return DEFAULT_UI_PREFERENCES
    }

    return {
      ...DEFAULT_UI_PREFERENCES,
      ...JSON.parse(raw),
    }
  } catch {
    return DEFAULT_UI_PREFERENCES
  }
}

export function applyUiPreferences(preferences: AdminUiPreferences): void {
  if (typeof document === 'undefined') {
    return
  }

  const root = document.documentElement
  root.dataset.theme = preferences.darkMode ? 'dark' : 'light'
  root.lang = preferences.language
  root.style.colorScheme = preferences.darkMode ? 'dark' : 'light'
}

export function saveUiPreferences(preferences: AdminUiPreferences): void {
  applyUiPreferences(preferences)

  try {
    localStorage.setItem(UI_PREFERENCES_KEY, JSON.stringify(preferences))
  } catch {
    // localStorage unavailable
  }

  window.dispatchEvent(new CustomEvent('admin-ui-preferences-changed', { detail: preferences }))
}

export function initializeUiPreferences(): void {
  applyUiPreferences(getStoredUiPreferences())
}

export function getStoredProviderConfig<T extends ProviderConfigStorage>(fallback: T): T {
  try {
    const raw = localStorage.getItem(PROVIDER_CONFIG_KEY)
    if (!raw) {
      return fallback
    }

    return {
      ...fallback,
      ...JSON.parse(raw),
    }
  } catch {
    return fallback
  }
}

export function saveProviderConfig(config: ProviderConfigStorage): void {
  try {
    localStorage.setItem(PROVIDER_CONFIG_KEY, JSON.stringify(config))
  } catch {
    // localStorage unavailable
  }
}
