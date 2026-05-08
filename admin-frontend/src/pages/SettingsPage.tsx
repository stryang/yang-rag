import React, { useEffect, useRef, useState } from 'react'
import {
  Moon,
  Bell,
  Globe,
  Key,
  Eye,
  EyeOff,
  Sparkles,
  Shield,
  RefreshCw,
  Check,
  AlertCircle,
  Palette,
  Save,
  Database,
} from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'
import { applyTheme, getStoredThemeColor, DEFAULT_THEME_COLOR, THEME_PRESETS, isValidHex } from '@/lib/theme'
import {
  getStoredUiPreferences,
  saveUiPreferences,
  type AdminUiPreferences,
} from '@/lib/preferences'
import {
  runtimeSettingsApi,
  type RuntimeSettings,
  type RuntimeSettingsUpdate,
} from '@/lib/api'
import { cn } from '@/lib/utils'

const LLM_PROVIDERS = [
  { id: 'openai', name: 'OpenAI', models: ['gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo'], price: '付费' },
  { id: 'siliconflow', name: '硅基流动', models: ['Qwen/Qwen2.5-7B-Instruct', 'deepseek-ai/DeepSeek-V2.5', 'THUDM/glm-4-9b-chat'], price: '免费额度' },
  { id: 'qwen', name: '阿里通义千问', models: ['qwen-turbo', 'qwen-plus', 'qwen-max'], price: '免费额度' },
  { id: 'ollama', name: 'Ollama (本地)', models: ['llama3.2', 'qwen2.5', 'deepseek-r1'], price: '本地运行' },
] as const

const EMBEDDING_PROVIDERS = [
  { id: 'openai', name: 'OpenAI', models: ['text-embedding-3-small', 'text-embedding-3-large'], price: '付费' },
  { id: 'siliconflow', name: '硅基流动', models: ['BAAI/bge-large-zh-v1.5', 'BAAI/bge-small-zh-v1.5'], price: '免费额度' },
  { id: 'huggingface', name: 'HuggingFace (本地)', models: ['bge-large-zh-v1.5', 'bge-small-zh-v1.5', 'bge-base-zh-v1.5'], price: '本地/离线' },
  { id: 'ollama', name: 'Ollama (本地)', models: ['nomic-embed-text'], price: '本地运行' },
] as const

const QUICK_START_OPTIONS = [
  {
    id: 'siliconflow',
    name: '硅基流动 (推荐)',
    description: '国内可用，有免费额度',
    badge: 'Embedding + LLM 均可配置为云端',
    config: {
      llm_provider: 'siliconflow',
      llm_model: 'Qwen/Qwen2.5-7B-Instruct',
      embedding_provider: 'siliconflow',
      embedding_model: 'BAAI/bge-large-zh-v1.5',
    },
  },
  {
    id: 'ollama',
    name: 'Ollama (本地)',
    description: '完全本地化，适合离线环境',
    badge: '需要本地先启动 Ollama',
    config: {
      llm_provider: 'ollama',
      llm_model: 'llama3.2',
      embedding_provider: 'ollama',
      embedding_model: 'nomic-embed-text',
    },
  },
  {
    id: 'openai',
    name: 'OpenAI',
    description: '效果稳定，适合英文与通用场景',
    badge: '需要有效 OpenAI Key',
    config: {
      llm_provider: 'openai',
      llm_model: 'gpt-4o-mini',
      embedding_provider: 'openai',
      embedding_model: 'text-embedding-3-small',
    },
  },
] as const

const DEFAULT_RUNTIME_SETTINGS: RuntimeSettings = {
  llm_provider: 'openai',
  llm_model: 'gpt-4o-mini',
  llm_api_key: '',
  llm_base_url: null,
  llm_temperature: 0.7,
  llm_max_tokens: 2000,
  embedding_provider: 'openai',
  embedding_model: 'text-embedding-3-small',
  embedding_api_key: '',
  embedding_base_url: null,
  embedding_dimension: 1536,
  vector_store_type: 'chroma',
  vector_store_persist_dir: './data/vectorstore',
  milvus_host: 'localhost',
  milvus_port: 19530,
  milvus_collection: 'yang_rag',
  api_endpoint: 'http://localhost:8000',
  uses_placeholder_llm_key: false,
  uses_placeholder_embedding_key: false,
}

const LANGUAGE_OPTIONS = [
  { value: 'zh-CN', label: '简体中文', description: '默认管理台语言' },
  { value: 'en-US', label: 'English', description: '切换浏览器语言标记与偏好' },
] as const

function getMatchingQuickStartId(config: RuntimeSettings): string | null {
  return QUICK_START_OPTIONS.find((option) =>
    option.config.llm_provider === config.llm_provider &&
    option.config.embedding_provider === config.embedding_provider &&
    option.config.llm_model === config.llm_model &&
    option.config.embedding_model === config.embedding_model
  )?.id || null
}

const SettingsPage: React.FC = () => {
  const { user } = useAuthStore()
  const [config, setConfig] = useState<RuntimeSettings>(DEFAULT_RUNTIME_SETTINGS)
  const [preferences, setPreferences] = useState<AdminUiPreferences>(() => getStoredUiPreferences())
  const [themeColor, setThemeColor] = useState(() => getStoredThemeColor() || DEFAULT_THEME_COLOR)
  const [hexInput, setHexInput] = useState(() => getStoredThemeColor() || DEFAULT_THEME_COLOR)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [showLlmApiKey, setShowLlmApiKey] = useState(false)
  const [showEmbeddingApiKey, setShowEmbeddingApiKey] = useState(false)
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  const colorInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    saveUiPreferences(preferences)
  }, [preferences])

  useEffect(() => {
    const loadRuntimeSettings = async () => {
      try {
        const response = await runtimeSettingsApi.get()
        setConfig(response)
      } catch (error) {
        console.error('Failed to load runtime settings:', error)
        setFeedback({ type: 'error', message: '运行时配置加载失败，当前展示的是默认值。' })
      } finally {
        setLoading(false)
      }
    }

    void loadRuntimeSettings()
  }, [])

  const handleThemeChange = (hex: string) => {
    applyTheme(hex)
    setThemeColor(hex)
    setHexInput(hex)
  }

  const handleHexInputChange = (value: string) => {
    setHexInput(value)
    if (isValidHex(value)) {
      applyTheme(value)
      setThemeColor(value)
    }
  }

  const updateConfig = (partial: Partial<RuntimeSettings>) => {
    setConfig((current) => ({
      ...current,
      ...partial,
    }))
  }

  const togglePreference = (key: 'darkMode' | 'notificationsEnabled') => {
    setPreferences((current) => ({
      ...current,
      [key]: !current[key],
    }))
  }

  const handleSave = async () => {
    setSaving(true)
    setFeedback(null)

    try {
      const payload: RuntimeSettingsUpdate = {
        llm_provider: config.llm_provider,
        llm_model: config.llm_model,
        llm_api_key: config.llm_api_key,
        llm_base_url: config.llm_base_url,
        llm_temperature: config.llm_temperature,
        llm_max_tokens: config.llm_max_tokens,
        embedding_provider: config.embedding_provider,
        embedding_model: config.embedding_model,
        embedding_api_key: config.embedding_api_key,
        embedding_base_url: config.embedding_base_url,
        embedding_dimension: config.embedding_dimension,
        vector_store_type: config.vector_store_type,
        vector_store_persist_dir: config.vector_store_persist_dir,
        milvus_host: config.milvus_host,
        milvus_port: config.milvus_port,
        milvus_collection: config.milvus_collection,
        api_endpoint: config.api_endpoint,
      }

      const saved = await runtimeSettingsApi.update(payload)
      setConfig(saved)

      try {
        await runtimeSettingsApi.reload()
        setFeedback({ type: 'success', message: '配置已保存并应用到当前 RAG 服务。空知识库会自动使用新的 embedding 配置。' })
      } catch (error) {
        console.error('Failed to reload RAG runtime settings:', error)
        setFeedback({ type: 'error', message: '配置已保存到 .env，但当前 RAG 服务热重载失败，请手动重启 8000 后端。' })
      }
    } catch (error: any) {
      const message = error?.response?.data?.detail || error?.message || '保存失败'
      setFeedback({ type: 'error', message })
    } finally {
      setSaving(false)
    }
  }

  const selectedLLMProvider = LLM_PROVIDERS.find((provider) => provider.id === config.llm_provider)
  const selectedEmbeddingProvider = EMBEDDING_PROVIDERS.find((provider) => provider.id === config.embedding_provider)
  const selectedQuickStartId = getMatchingQuickStartId(config)
  const selectedLanguage = LANGUAGE_OPTIONS.find((option) => option.value === preferences.language)

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-40 animate-pulse rounded-xl bg-gray-200" />
        <div className="h-32 animate-pulse rounded-2xl bg-white" />
        <div className="h-72 animate-pulse rounded-2xl bg-white" />
      </div>
    )
  }

  return (
    <div className="space-y-6 page-enter">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">系统设置</h1>
          <p className="mt-1 text-gray-500">管理运行时模型配置、密钥和控制台外观</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-semibold text-gray-700">
            RAG API：{config.api_endpoint}
          </span>
          <button
            type="button"
            onClick={() => void handleSave()}
            disabled={saving}
            className="inline-flex items-center gap-2 rounded-[1.15rem] bg-primary-600 px-5 py-3 font-semibold text-white shadow-md shadow-primary-600/15 transition-all hover:bg-primary-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {saving ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            {saving ? '保存中...' : '保存并应用'}
          </button>
        </div>
      </div>

      {feedback && (
        <div
          className={cn(
            'flex items-start gap-3 rounded-2xl border p-4 text-sm',
            feedback.type === 'success'
              ? 'border-primary-200 bg-primary-50 text-primary-700'
              : 'border-red-200 bg-red-50 text-red-600'
          )}
        >
          {feedback.type === 'success' ? <Check className="mt-0.5 h-5 w-5 flex-shrink-0" /> : <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0" />}
          <p>{feedback.message}</p>
        </div>
      )}

      <div className="space-y-6">
        <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white">
          <div className="border-b border-gray-100 px-6 py-4">
            <h2 className="flex items-center gap-2 text-lg font-bold text-gray-900">
              <Shield className="h-5 w-5 text-gray-700" />
              账户信息
            </h2>
          </div>
          <div className="space-y-4 p-6">
            <div className="flex items-center justify-between border-b border-gray-50 py-3">
              <div>
                <p className="font-medium text-gray-900">用户名</p>
                <p className="text-sm text-gray-500">登录系统使用的名称</p>
              </div>
              <span className="rounded-2xl bg-gray-100 px-4 py-2 font-medium text-gray-700">{user?.username}</span>
            </div>
            <div className="flex items-center justify-between border-b border-gray-50 py-3">
              <div>
                <p className="font-medium text-gray-900">邮箱</p>
                <p className="text-sm text-gray-500">账户绑定的邮箱地址</p>
              </div>
              <span className="rounded-2xl bg-gray-100 px-4 py-2 font-medium text-gray-700">{user?.email}</span>
            </div>
            <div className="flex items-center justify-between py-3">
              <div>
                <p className="font-medium text-gray-900">账户角色</p>
                <p className="text-sm text-gray-500">当前账户的权限级别</p>
              </div>
              <span
                className={cn(
                  'rounded-2xl px-4 py-2 text-sm font-semibold',
                  user?.role === 'admin' ? 'bg-gray-100 text-gray-800' : 'bg-primary-50 text-primary-700'
                )}
              >
                {user?.role === 'admin' ? '管理员' : '普通用户'}
              </span>
            </div>
          </div>
        </div>

        <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white">
          <div className="border-b border-gray-100 px-6 py-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-dark">
                <Sparkles className="h-5 w-5 text-primary-400" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-gray-900">快速开始</h2>
                <p className="text-sm text-gray-500">选择推荐方案后再保存，真正写入 RAG 运行时配置</p>
              </div>
            </div>
          </div>
          <div className="p-6">
            <div className="mb-4 flex flex-wrap items-center gap-2">
              <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-semibold text-gray-700">
                当前方案：{selectedQuickStartId ? QUICK_START_OPTIONS.find((option) => option.id === selectedQuickStartId)?.name : '自定义组合'}
              </span>
              <span className="rounded-full bg-primary-50 px-3 py-1 text-xs font-semibold text-primary-700">
                保存后立即热重载
              </span>
            </div>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              {QUICK_START_OPTIONS.map((option) => {
                const isSelected = selectedQuickStartId === option.id
                return (
                  <button
                    key={option.id}
                    type="button"
                    onClick={() => updateConfig(option.config)}
                    className={cn(
                      'relative rounded-[1.4rem] border-2 p-4 text-left transition-all duration-200',
                      isSelected
                        ? 'border-primary-500 bg-primary-50 shadow-lg shadow-primary-600/10'
                        : 'border-gray-200 bg-gray-50 hover:border-gray-400'
                    )}
                  >
                    {isSelected && (
                      <div className="absolute right-3 top-3 flex h-6 w-6 items-center justify-center rounded-full bg-primary-600 shadow-sm shadow-primary-600/20">
                        <Check className="h-3.5 w-3.5 text-white" />
                      </div>
                    )}
                    <p className="font-semibold text-gray-900">{option.name}</p>
                    <p className="mt-1 text-sm text-gray-500">{option.description}</p>
                    <p className={cn('mt-2 text-xs font-medium', isSelected ? 'text-primary-600' : 'text-gray-500')}>
                      {option.badge}
                    </p>
                  </button>
                )
              })}
            </div>
          </div>
        </div>

        <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white">
          <div className="border-b border-gray-100 px-6 py-4">
            <h2 className="flex items-center gap-2 text-lg font-bold text-gray-900">
              <Sparkles className="h-5 w-5 text-primary-600" />
              LLM 模型配置
            </h2>
          </div>
          <div className="space-y-5 p-6">
            <div>
              <label className="mb-3 block text-sm font-semibold text-gray-700">选择提供商</label>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {LLM_PROVIDERS.map((provider) => (
                  <button
                    key={provider.id}
                    type="button"
                    onClick={() => updateConfig({ llm_provider: provider.id, llm_model: provider.models[0] })}
                    className={cn(
                      'relative rounded-[1.35rem] border-2 p-4 text-left transition-all duration-200',
                      config.llm_provider === provider.id
                        ? 'border-primary-500 bg-primary-50 shadow-md shadow-primary-600/10'
                        : 'border-gray-200 bg-white hover:border-gray-300'
                    )}
                  >
                    {config.llm_provider === provider.id && (
                      <div className="absolute right-3 top-3 flex h-6 w-6 items-center justify-center rounded-full bg-primary-600">
                        <Check className="h-3.5 w-3.5 text-white" />
                      </div>
                    )}
                    <p className="font-semibold text-gray-900">{provider.name}</p>
                    <p className="mt-1 text-sm text-gray-500">{provider.price}</p>
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
              <div>
                <label className="mb-2 block text-sm font-semibold text-gray-700">模型 ({selectedLLMProvider?.name})</label>
                <select
                  value={config.llm_model}
                  onChange={(event) => updateConfig({ llm_model: event.target.value })}
                  className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 outline-none transition-all focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
                >
                  {selectedLLMProvider?.models.map((model) => (
                    <option key={model} value={model}>{model}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-2 block text-sm font-semibold text-gray-700">Base URL（可选）</label>
                <input
                  type="text"
                  value={config.llm_base_url ?? ''}
                  onChange={(event) => updateConfig({ llm_base_url: event.target.value || null })}
                  placeholder={config.llm_provider === 'ollama' ? 'http://localhost:11434' : '留空使用默认地址'}
                  className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 outline-none transition-all focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
              <div>
                <label className="mb-2 block text-sm font-semibold text-gray-700">LLM API Key</label>
                <div className="relative">
                  <input
                    type={showLlmApiKey ? 'text' : 'password'}
                    value={config.llm_api_key}
                    onChange={(event) => updateConfig({ llm_api_key: event.target.value })}
                    placeholder={config.llm_provider === 'ollama' ? '本地模式可留空' : '请输入有效 API Key'}
                    className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 pr-12 outline-none transition-all focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
                  />
                  <button
                    type="button"
                    onClick={() => setShowLlmApiKey((current) => !current)}
                    className="absolute inset-y-0 right-3 flex items-center text-gray-400 transition-colors hover:text-gray-600"
                    aria-label={showLlmApiKey ? '隐藏 LLM API Key' : '显示 LLM API Key'}
                  >
                    {showLlmApiKey ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                </div>
                {(config.uses_placeholder_llm_key || (!config.llm_api_key && config.llm_provider !== 'ollama')) && (
                  <p className="mt-2 text-xs text-amber-600">当前运行时没有有效的 LLM Key，聊天能力会报错。</p>
                )}
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-2 block text-sm font-semibold text-gray-700">温度</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="2"
                    value={config.llm_temperature}
                    onChange={(event) => updateConfig({ llm_temperature: Number(event.target.value) })}
                    className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 outline-none transition-all focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-sm font-semibold text-gray-700">最大 Token</label>
                  <input
                    type="number"
                    min="1"
                    max="16000"
                    value={config.llm_max_tokens}
                    onChange={(event) => updateConfig({ llm_max_tokens: Number(event.target.value) })}
                    className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 outline-none transition-all focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
                  />
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-amber-100 bg-amber-50 p-4">
              <div className="flex items-start gap-3">
                <Key className="mt-0.5 h-5 w-5 text-amber-600" />
                <div className="flex-1 text-sm text-amber-800">
                  <p className="font-medium">这里保存的是 RAG 运行时配置</p>
                  <p className="mt-1">修改后会写入项目根目录 <code className="rounded bg-amber-100 px-1 py-0.5">.env</code>，并尝试热重载当前 8000 服务。</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white">
          <div className="border-b border-gray-100 px-6 py-4">
            <h2 className="flex items-center gap-2 text-lg font-bold text-gray-900">
              <RefreshCw className="h-5 w-5 text-gray-700" />
              Embedding 模型配置
            </h2>
          </div>
          <div className="space-y-5 p-6">
            <div>
              <label className="mb-3 block text-sm font-semibold text-gray-700">选择提供商</label>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {EMBEDDING_PROVIDERS.map((provider) => (
                  <button
                    key={provider.id}
                    type="button"
                    onClick={() => updateConfig({ embedding_provider: provider.id, embedding_model: provider.models[0] })}
                    className={cn(
                      'relative rounded-[1.35rem] border-2 p-4 text-left transition-all duration-200',
                      config.embedding_provider === provider.id
                        ? 'border-primary-500 bg-primary-50 shadow-md shadow-primary-600/10'
                        : 'border-gray-200 bg-white hover:border-gray-300'
                    )}
                  >
                    {config.embedding_provider === provider.id && (
                      <div className="absolute right-3 top-3 flex h-6 w-6 items-center justify-center rounded-full bg-primary-600">
                        <Check className="h-3.5 w-3.5 text-white" />
                      </div>
                    )}
                    <p className="font-semibold text-gray-900">{provider.name}</p>
                    <p className="mt-1 text-sm text-gray-500">{provider.price}</p>
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
              <div>
                <label className="mb-2 block text-sm font-semibold text-gray-700">模型 ({selectedEmbeddingProvider?.name})</label>
                <select
                  value={config.embedding_model}
                  onChange={(event) => updateConfig({ embedding_model: event.target.value })}
                  className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 outline-none transition-all focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
                >
                  {selectedEmbeddingProvider?.models.map((model) => (
                    <option key={model} value={model}>{model}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-2 block text-sm font-semibold text-gray-700">Base URL（可选）</label>
                <input
                  type="text"
                  value={config.embedding_base_url ?? ''}
                  onChange={(event) => updateConfig({ embedding_base_url: event.target.value || null })}
                  placeholder={config.embedding_provider === 'ollama' ? 'http://localhost:11434' : '留空使用默认地址'}
                  className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 outline-none transition-all focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
              <div>
                <label className="mb-2 block text-sm font-semibold text-gray-700">Embedding API Key</label>
                <div className="relative">
                  <input
                    type={showEmbeddingApiKey ? 'text' : 'password'}
                    value={config.embedding_api_key}
                    onChange={(event) => updateConfig({ embedding_api_key: event.target.value })}
                    placeholder={config.embedding_provider === 'ollama' || config.embedding_provider === 'huggingface' || config.embedding_provider === 'local' ? '本地模式可留空' : '请输入有效 API Key'}
                    className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 pr-12 outline-none transition-all focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
                  />
                  <button
                    type="button"
                    onClick={() => setShowEmbeddingApiKey((current) => !current)}
                    className="absolute inset-y-0 right-3 flex items-center text-gray-400 transition-colors hover:text-gray-600"
                    aria-label={showEmbeddingApiKey ? '隐藏 Embedding API Key' : '显示 Embedding API Key'}
                  >
                    {showEmbeddingApiKey ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                </div>
                {(config.uses_placeholder_embedding_key || (!config.embedding_api_key && !['ollama', 'huggingface', 'local'].includes(config.embedding_provider))) && (
                  <p className="mt-2 text-xs text-amber-600">当前运行时没有有效的 Embedding Key，知识库上传会失败。</p>
                )}
              </div>
              <div>
                <label className="mb-2 block text-sm font-semibold text-gray-700">向量维度</label>
                <input
                  type="number"
                  min="1"
                  max="16384"
                  value={config.embedding_dimension}
                  onChange={(event) => updateConfig({ embedding_dimension: Number(event.target.value) })}
                  className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 outline-none transition-all focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
                />
              </div>
            </div>

            <div className="rounded-2xl border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600">
              说明：已有数据的知识库会保持创建时的 embedding 配置；空知识库在首次上传前会自动同步当前运行时 embedding 设置。
            </div>
          </div>
        </div>

        <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white">
          <div className="border-b border-gray-100 px-6 py-4">
            <h2 className="flex items-center gap-2 text-lg font-bold text-gray-900">
              <Database className="h-5 w-5 text-gray-700" />
              向量存储运行时配置
            </h2>
          </div>
          <div className="space-y-5 p-6">
            <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
              <div>
                <label className="mb-2 block text-sm font-semibold text-gray-700">存储类型</label>
                <select
                  value={config.vector_store_type}
                  onChange={(event) => updateConfig({ vector_store_type: event.target.value as RuntimeSettings['vector_store_type'] })}
                  className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 outline-none transition-all focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
                >
                  <option value="chroma">Chroma</option>
                  <option value="faiss">FAISS</option>
                  <option value="milvus">Milvus</option>
                </select>
              </div>
              <div>
                <label className="mb-2 block text-sm font-semibold text-gray-700">持久化路径</label>
                <input
                  type="text"
                  value={config.vector_store_persist_dir}
                  onChange={(event) => updateConfig({ vector_store_persist_dir: event.target.value })}
                  className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 outline-none transition-all focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
                />
              </div>
            </div>

            {config.vector_store_type === 'milvus' && (
              <div className="grid grid-cols-1 gap-5 md:grid-cols-3">
                <div>
                  <label className="mb-2 block text-sm font-semibold text-gray-700">Milvus Host</label>
                  <input
                    type="text"
                    value={config.milvus_host}
                    onChange={(event) => updateConfig({ milvus_host: event.target.value })}
                    className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 outline-none transition-all focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-sm font-semibold text-gray-700">Milvus Port</label>
                  <input
                    type="number"
                    value={config.milvus_port}
                    onChange={(event) => updateConfig({ milvus_port: Number(event.target.value) })}
                    className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 outline-none transition-all focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-sm font-semibold text-gray-700">Collection</label>
                  <input
                    type="text"
                    value={config.milvus_collection}
                    onChange={(event) => updateConfig({ milvus_collection: event.target.value })}
                    className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 outline-none transition-all focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white">
          <div className="border-b border-gray-100 px-6 py-4">
            <h2 className="flex items-center gap-2 text-lg font-bold text-gray-900">
              <Palette className="h-5 w-5 text-primary-600" />
              主题颜色
            </h2>
          </div>
          <div className="space-y-5 p-6">
            <div>
              <label className="mb-3 block text-sm font-semibold text-gray-700">预设颜色</label>
              <div className="flex flex-wrap gap-3">
                {THEME_PRESETS.map((preset) => (
                  <button
                    key={preset.hex}
                    type="button"
                    onClick={() => handleThemeChange(preset.hex)}
                    className={cn(
                      'group relative h-10 w-10 rounded-[1.05rem] transition-all duration-200 hover:scale-110',
                      themeColor === preset.hex && 'scale-110 ring-2 ring-gray-400 ring-offset-2'
                    )}
                    style={{ backgroundColor: preset.hex }}
                    aria-label={preset.name}
                  >
                    {themeColor === preset.hex && (
                      <Check className="absolute inset-0 m-auto h-4 w-4 text-white drop-shadow" />
                    )}
                  </button>
                ))}
                <button
                  type="button"
                  onClick={() => colorInputRef.current?.click()}
                  className="inline-flex h-10 items-center gap-2 rounded-[1.05rem] border border-dashed border-gray-300 px-4 text-sm font-medium text-gray-600 transition-colors hover:border-primary-400 hover:text-primary-600"
                >
                  自定义
                </button>
                <input
                  ref={colorInputRef}
                  type="color"
                  value={themeColor}
                  onChange={(event) => handleThemeChange(event.target.value)}
                  className="sr-only"
                />
              </div>
            </div>

            <div>
              <label className="mb-2 block text-sm font-semibold text-gray-700">HEX 颜色值</label>
              <input
                type="text"
                value={hexInput}
                onChange={(event) => handleHexInputChange(event.target.value)}
                className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 font-mono outline-none transition-all focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
              />
            </div>
          </div>
        </div>

        <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white">
          <div className="border-b border-gray-100 px-6 py-4">
            <h2 className="flex items-center gap-2 text-lg font-bold text-gray-900">
              <Bell className="h-5 w-5 text-gray-700" />
              控制台偏好
            </h2>
          </div>
          <div className="space-y-4 p-6">
            <div className="flex items-center justify-between gap-6 py-3">
              <div className="flex items-center gap-3">
                <div className="rounded-xl bg-gray-100 p-2">
                  <Moon className="h-5 w-5 text-gray-500" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">深色模式标记</p>
                  <p className="text-sm text-gray-500">影响浏览器主题标记和系统配色提示</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => togglePreference('darkMode')}
                className={cn(
                  'relative inline-flex h-7 w-12 items-center rounded-full transition-colors',
                  preferences.darkMode ? 'bg-primary-600' : 'bg-gray-200'
                )}
              >
                <span
                  className={cn(
                    'inline-flex h-5 w-5 items-center justify-center rounded-full bg-white shadow-sm transition-transform',
                    preferences.darkMode ? 'translate-x-6' : 'translate-x-1'
                  )}
                >
                  <Moon className={cn('h-3 w-3', preferences.darkMode ? 'text-primary-600' : 'text-gray-400')} />
                </span>
              </button>
            </div>

            <div className="flex items-center justify-between gap-6 py-3">
              <div className="flex items-center gap-3">
                <div className="rounded-xl bg-gray-100 p-2">
                  <Bell className="h-5 w-5 text-gray-500" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">通知推送</p>
                  <p className="text-sm text-gray-500">控制右上角通知提示和提醒状态</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => togglePreference('notificationsEnabled')}
                className={cn(
                  'relative inline-flex h-7 w-12 items-center rounded-full transition-colors',
                  preferences.notificationsEnabled ? 'bg-primary-600' : 'bg-gray-200'
                )}
              >
                <span
                  className={cn(
                    'inline-flex h-5 w-5 items-center justify-center rounded-full bg-white shadow-sm transition-transform',
                    preferences.notificationsEnabled ? 'translate-x-6' : 'translate-x-1'
                  )}
                >
                  <Bell className={cn('h-3 w-3', preferences.notificationsEnabled ? 'text-primary-600' : 'text-gray-400')} />
                </span>
              </button>
            </div>

            <div className="flex items-center justify-between gap-6 py-3">
              <div className="flex items-center gap-3">
                <div className="rounded-xl bg-gray-100 p-2">
                  <Globe className="h-5 w-5 text-gray-500" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">语言设置</p>
                  <p className="text-sm text-gray-500">保存控制台语言偏好与浏览器语言标记</p>
                </div>
              </div>
              <div className="min-w-[220px]">
                <select
                  value={preferences.language}
                  onChange={(event) => setPreferences((current) => ({ ...current, language: event.target.value as AdminUiPreferences['language'] }))}
                  className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 outline-none transition-all focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
                >
                  {LANGUAGE_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
                <p className="mt-2 text-xs text-gray-500">{selectedLanguage?.description}</p>
              </div>
            </div>

            <div className="flex flex-wrap gap-2 border-t border-gray-100 pt-4">
              <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-semibold text-gray-700">
                配色：{preferences.darkMode ? '深色' : '浅色'}
              </span>
              <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-semibold text-gray-700">
                通知：{preferences.notificationsEnabled ? '开启' : '关闭'}
              </span>
              <span className="rounded-full bg-primary-50 px-3 py-1 text-xs font-semibold text-primary-700">
                语言：{selectedLanguage?.label}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SettingsPage
