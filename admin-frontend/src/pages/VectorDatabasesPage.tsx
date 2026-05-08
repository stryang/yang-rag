import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  Database,
  Edit2,
  HardDrive,
  Plus,
  RefreshCw,
  Search,
  Server,
  Shield,
  Star,
  Trash2,
  X,
} from 'lucide-react'
import Modal from '@/components/Modal'
import ConfirmDialog from '@/components/ConfirmDialog'
import {
  vectorDatabasesApi,
  VectorDatabaseProfile,
  VectorDatabaseProfileInput,
  VectorDatabaseRuntimeOverview,
  VectorDatabaseStatus,
  VectorStoreType,
} from '@/lib/api'
import { cn } from '@/lib/utils'
import { useAuthStore } from '@/stores/authStore'

type FeedbackState = {
  tone: 'success' | 'error'
  message: string
} | null

const DEFAULT_FORM: VectorDatabaseProfileInput = {
  name: '',
  store_type: 'chroma',
  description: '',
  persist_path: './data/vectorstore',
  host: 'localhost',
  port: 19530,
  collection_prefix: '',
  is_default: false,
  is_enabled: true,
}

const STATUS_STYLES: Record<VectorDatabaseStatus, string> = {
  online: 'bg-primary-50 text-primary-700',
  warning: 'bg-amber-50 text-amber-700',
  offline: 'bg-red-50 text-red-700',
  unknown: 'bg-gray-100 text-gray-700',
}

const STATUS_LABELS: Record<VectorDatabaseStatus, string> = {
  online: '在线',
  warning: '告警',
  offline: '离线',
  unknown: '未知',
}

const STORE_TYPE_LABELS: Record<VectorStoreType, string> = {
  chroma: 'Chroma',
  faiss: 'FAISS',
  milvus: 'Milvus',
}

const VectorDatabasesPage: React.FC = () => {
  const { user: currentUser } = useAuthStore()
  const navigate = useNavigate()

  const [runtime, setRuntime] = useState<VectorDatabaseRuntimeOverview | null>(null)
  const [profiles, setProfiles] = useState<VectorDatabaseProfile[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [testingId, setTestingId] = useState<number | null>(null)
  const [showModal, setShowModal] = useState(false)
  const [editingProfile, setEditingProfile] = useState<VectorDatabaseProfile | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<VectorDatabaseProfile | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [feedback, setFeedback] = useState<FeedbackState>(null)
  const [modalError, setModalError] = useState('')
  const [formData, setFormData] = useState<VectorDatabaseProfileInput>(DEFAULT_FORM)

  useEffect(() => {
    if (currentUser?.role !== 'admin') {
      navigate('/admin')
      return
    }
    void fetchPageData()
  }, [currentUser, navigate])

  const fetchPageData = async (silent = false) => {
    try {
      if (silent) {
        setRefreshing(true)
      } else {
        setLoading(true)
      }

      const [runtimeResponse, profilesResponse] = await Promise.all([
        vectorDatabasesApi.getRuntime(),
        vectorDatabasesApi.list(),
      ])

      setRuntime(runtimeResponse)
      setProfiles(profilesResponse.items)
    } catch (err) {
      console.error('Failed to fetch vector database data:', err)
      setFeedback({ tone: 'error', message: '加载向量数据库信息失败' })
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  const openCreateModal = () => {
    setEditingProfile(null)
    setFormData(DEFAULT_FORM)
    setModalError('')
    setShowModal(true)
  }

  const openEditModal = (profile: VectorDatabaseProfile) => {
    setEditingProfile(profile)
    setFormData({
      name: profile.name,
      store_type: profile.store_type,
      description: profile.description,
      persist_path: profile.persist_path,
      host: profile.host,
      port: profile.port,
      collection_prefix: profile.collection_prefix,
      is_default: profile.is_default,
      is_enabled: profile.is_enabled,
    })
    setModalError('')
    setShowModal(true)
  }

  const closeModal = () => {
    setShowModal(false)
    setEditingProfile(null)
    setFormData(DEFAULT_FORM)
    setModalError('')
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setSaving(true)
    setModalError('')

    try {
      const payload: VectorDatabaseProfileInput = {
        ...formData,
        persist_path: formData.store_type === 'milvus' ? null : formData.persist_path || '',
        host: formData.store_type === 'milvus' ? formData.host || 'localhost' : null,
        port: formData.store_type === 'milvus' ? Number(formData.port || 19530) : null,
        collection_prefix: formData.collection_prefix || null,
      }

      if (editingProfile) {
        await vectorDatabasesApi.update(editingProfile.id, payload)
        setFeedback({ tone: 'success', message: `向量数据库配置 ${formData.name} 已更新` })
      } else {
        await vectorDatabasesApi.create(payload)
        setFeedback({ tone: 'success', message: `向量数据库配置 ${formData.name} 已创建` })
      }

      closeModal()
      await fetchPageData(true)
    } catch (err: unknown) {
      const message =
        err && typeof err === 'object' && 'response' in err
          ? ((err as { response?: { data?: { detail?: string } } }).response?.data?.detail || '保存失败')
          : '保存失败'
      setModalError(message)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!deleteTarget) {
      return
    }

    try {
      setDeleting(true)
      await vectorDatabasesApi.delete(deleteTarget.id)
      await fetchPageData(true)
      setFeedback({ tone: 'success', message: `向量数据库配置 ${deleteTarget.name} 已删除` })
      setDeleteTarget(null)
    } catch (err) {
      console.error('Failed to delete vector database profile:', err)
      setFeedback({ tone: 'error', message: '删除向量数据库配置失败' })
    } finally {
      setDeleting(false)
    }
  }

  const handleTest = async (profile: VectorDatabaseProfile) => {
    try {
      setTestingId(profile.id)
      const result = await vectorDatabasesApi.test(profile.id)
      await fetchPageData(true)
      setFeedback({ tone: result.success ? 'success' : 'error', message: `${profile.name}：${result.message}` })
    } catch (err) {
      console.error('Failed to test vector database profile:', err)
      setFeedback({ tone: 'error', message: '检测连接失败' })
    } finally {
      setTestingId(null)
    }
  }

  const handleSetDefault = async (profile: VectorDatabaseProfile) => {
    try {
      await vectorDatabasesApi.setDefault(profile.id)
      await fetchPageData(true)
      setFeedback({ tone: 'success', message: `${profile.name} 已设为默认配置` })
    } catch (err) {
      console.error('Failed to set default vector database profile:', err)
      setFeedback({ tone: 'error', message: '设置默认配置失败' })
    }
  }

  const filteredProfiles = profiles.filter((profile) => {
    const query = searchQuery.toLowerCase()
    return (
      profile.name.toLowerCase().includes(query) ||
      profile.store_type.toLowerCase().includes(query) ||
      (profile.description || '').toLowerCase().includes(query) ||
      profile.target.toLowerCase().includes(query)
    )
  })

  const renderStatusBadge = (status: VectorDatabaseStatus) => (
    <span className={cn('inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold', STATUS_STYLES[status])}>
      {status === 'online' ? <CheckCircle2 className="h-3.5 w-3.5" /> : <AlertCircle className="h-3.5 w-3.5" />}
      {STATUS_LABELS[status]}
    </span>
  )

  if (loading) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 page-enter">
        <div className="relative">
          <div className="h-16 w-16 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600"></div>
          <HardDrive className="absolute inset-0 m-auto h-6 w-6 text-primary-600" />
        </div>
        <p className="text-gray-500">加载向量数据库管理信息...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6 page-enter">
      {feedback && (
        <div className={cn(
          'flex items-center gap-3 rounded-2xl border p-4',
          feedback.tone === 'success'
            ? 'border-primary-200 bg-primary-50 text-primary-700'
            : 'border-red-200 bg-red-50 text-red-700'
        )}>
          {feedback.tone === 'success' ? (
            <CheckCircle2 className="h-5 w-5 flex-shrink-0" />
          ) : (
            <AlertCircle className="h-5 w-5 flex-shrink-0" />
          )}
          <span className="flex-1">{feedback.message}</span>
          <button onClick={() => setFeedback(null)} className="rounded-xl p-1 transition-colors hover:bg-black/5">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">向量数据库管理</h1>
          <p className="mt-1 text-gray-500">管理运行时向量库配置和后台维护用的连接档案</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => void fetchPageData(true)}
            className={cn(
              'inline-flex items-center gap-2 rounded-[1.1rem] border border-gray-200 px-4 py-2.5 font-medium text-gray-700 transition-colors hover:bg-gray-50',
              refreshing && 'cursor-not-allowed opacity-70'
            )}
            disabled={refreshing}
          >
            <RefreshCw className={cn('h-4 w-4', refreshing && 'animate-spin')} />
            刷新
          </button>
          <button
            type="button"
            onClick={openCreateModal}
            className="inline-flex items-center gap-2 rounded-[1.1rem] bg-primary-600 px-5 py-2.5 font-semibold text-white shadow-md shadow-primary-600/15 transition-all duration-200 hover:-translate-y-0.5 hover:bg-primary-700 hover:shadow-lg"
          >
            <Plus className="h-5 w-5" />
            新建配置
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">运行时后端</p>
              <p className="mt-2 text-2xl font-bold text-gray-900">{runtime ? STORE_TYPE_LABELS[runtime.store_type] : '--'}</p>
            </div>
            <div className="rounded-2xl bg-primary-50 p-3">
              <Database className="h-6 w-6 text-primary-600" />
            </div>
          </div>
          <div className="mt-3">{runtime && renderStatusBadge(runtime.status)}</div>
        </div>

        <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">运行时目标</p>
              <p className="mt-2 line-clamp-2 text-sm font-semibold text-gray-900">{runtime?.target || '--'}</p>
            </div>
            <div className="rounded-2xl bg-gray-100 p-3">
              <Server className="h-6 w-6 text-gray-700" />
            </div>
          </div>
          <p className="mt-3 text-sm text-gray-500">存储占用 {runtime?.storage_usage_label || '0 B'}</p>
        </div>

        <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">知识库集合</p>
              <p className="mt-2 text-2xl font-bold text-gray-900">{runtime?.collection_count || 0}</p>
            </div>
            <div className="rounded-2xl bg-amber-50 p-3">
              <Activity className="h-6 w-6 text-amber-600" />
            </div>
          </div>
          <p className="mt-3 text-sm text-gray-500">文档 {runtime?.total_documents || 0} · 切片 {runtime?.total_chunks || 0}</p>
        </div>

        <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">托管配置</p>
              <p className="mt-2 text-2xl font-bold text-gray-900">{profiles.length}</p>
            </div>
            <div className="rounded-2xl bg-gray-100 p-3">
              <Shield className="h-6 w-6 text-gray-700" />
            </div>
          </div>
          <p className="mt-3 text-sm text-gray-500">默认配置 {profiles.find((item) => item.is_default)?.name || '未设置'}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.2fr,0.8fr]">
        <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">
          <div className="border-b border-gray-100 px-6 py-4">
            <h2 className="text-lg font-bold text-gray-900">托管配置列表</h2>
            <p className="mt-1 text-sm text-gray-500">用于记录和维护候选向量数据库连接，不直接修改 RAG 运行时配置</p>
          </div>
          <div className="space-y-5 p-6">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="搜索名称、类型或目标路径..."
                className="w-full rounded-2xl border border-gray-200 bg-gray-50 py-3.5 pl-12 pr-4 text-gray-800 outline-none transition-all placeholder-gray-400 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
              />
            </div>

            {filteredProfiles.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-gray-200 bg-gray-50 px-6 py-12 text-center">
                <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-white shadow-sm">
                  <HardDrive className="h-8 w-8 text-gray-400" />
                </div>
                <p className="text-lg font-semibold text-gray-900">还没有托管配置</p>
                <p className="mt-2 text-sm text-gray-500">可以先录入 Chroma、FAISS 或 Milvus 连接信息，便于运维检查和切换规划</p>
              </div>
            ) : (
              <div className="space-y-4">
                {filteredProfiles.map((profile) => (
                  <div key={profile.id} className="rounded-2xl border border-gray-200 bg-white p-5 transition-all duration-200 hover:border-primary-200 hover:shadow-sm">
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="text-lg font-bold text-gray-900">{profile.name}</h3>
                          <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-semibold text-gray-700">{STORE_TYPE_LABELS[profile.store_type]}</span>
                          {profile.is_default && (
                            <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">
                              <Star className="h-3.5 w-3.5" />
                              默认
                            </span>
                          )}
                          {!profile.is_enabled && (
                            <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-semibold text-gray-600">已禁用</span>
                          )}
                          {renderStatusBadge(profile.last_status)}
                        </div>
                        <p className="mt-2 text-sm text-gray-600">{profile.description || '暂无描述'}</p>
                        <div className="mt-4 grid grid-cols-1 gap-3 text-sm text-gray-500 md:grid-cols-2">
                          <div>
                            <span className="font-medium text-gray-700">目标：</span>
                            {profile.target}
                          </div>
                          <div>
                            <span className="font-medium text-gray-700">最后检测：</span>
                            {profile.last_checked_at ? new Date(profile.last_checked_at).toLocaleString('zh-CN') : '未检测'}
                          </div>
                        </div>
                        {profile.last_error && (
                          <div className="mt-3 rounded-xl bg-red-50 px-3 py-2 text-sm text-red-600">{profile.last_error}</div>
                        )}
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {!profile.is_default && (
                          <button
                            type="button"
                            onClick={() => void handleSetDefault(profile)}
                            className="rounded-[1.05rem] border border-amber-200 px-4 py-2 text-sm font-medium text-amber-700 transition-colors hover:bg-amber-50"
                          >
                            设为默认
                          </button>
                        )}
                        <button
                          type="button"
                          onClick={() => void handleTest(profile)}
                          disabled={testingId === profile.id}
                          className="rounded-[1.05rem] border border-gray-200 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 disabled:opacity-60"
                        >
                          {testingId === profile.id ? '检测中...' : '检测'}
                        </button>
                        <button
                          type="button"
                          onClick={() => openEditModal(profile)}
                          className="inline-flex items-center gap-2 rounded-[1.05rem] border border-gray-200 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
                        >
                          <Edit2 className="h-4 w-4" />
                          编辑
                        </button>
                        <button
                          type="button"
                          onClick={() => setDeleteTarget(profile)}
                          className="inline-flex items-center gap-2 rounded-[1.05rem] border border-red-200 px-4 py-2 text-sm font-medium text-red-600 transition-colors hover:bg-red-50"
                        >
                          <Trash2 className="h-4 w-4" />
                          删除
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="space-y-6">
          <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">
            <div className="border-b border-gray-100 px-6 py-4">
              <h2 className="text-lg font-bold text-gray-900">运行时概览</h2>
              <p className="mt-1 text-sm text-gray-500">当前 RAG 服务实际读取的向量存储设置</p>
            </div>
            <div className="space-y-4 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">存储类型</p>
                  <p className="mt-1 text-lg font-semibold text-gray-900">{runtime ? STORE_TYPE_LABELS[runtime.store_type] : '--'}</p>
                </div>
                {runtime && renderStatusBadge(runtime.status)}
              </div>
              <div className="rounded-2xl bg-gray-50 p-4">
                <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">运行时目标</p>
                <p className="mt-2 break-all font-medium text-gray-900">{runtime?.target || '--'}</p>
                <p className="mt-2 text-sm text-gray-500">{runtime?.message || '暂无信息'}</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-2xl bg-primary-50 p-4">
                  <p className="text-sm text-gray-500">集合数</p>
                  <p className="mt-1 text-2xl font-bold text-gray-900">{runtime?.collection_count || 0}</p>
                </div>
                <div className="rounded-2xl bg-primary-50 p-4">
                  <p className="text-sm text-gray-500">磁盘占用</p>
                  <p className="mt-1 text-2xl font-bold text-gray-900">{runtime?.storage_usage_label || '0 B'}</p>
                </div>
              </div>
            </div>
          </div>

          <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">
            <div className="border-b border-gray-100 px-6 py-4">
              <h2 className="text-lg font-bold text-gray-900">最近集合</h2>
              <p className="mt-1 text-sm text-gray-500">基于现有知识库元数据推导出的向量集合</p>
            </div>
            <div className="p-6">
              {runtime?.collections.length ? (
                <div className="space-y-3">
                  {runtime.collections.slice(0, 5).map((collection) => (
                    <div key={collection.id} className="rounded-2xl border border-gray-100 p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <p className="truncate font-semibold text-gray-900">{collection.name}</p>
                          <p className="mt-1 line-clamp-2 text-sm text-gray-500">{collection.description || '暂无描述'}</p>
                        </div>
                        <div className="rounded-xl bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600">
                          {collection.embedding_model || '未标记模型'}
                        </div>
                      </div>
                      <div className="mt-3 flex items-center gap-4 text-xs text-gray-500">
                        <span>文档 {collection.document_count}</span>
                        <span>切片 {collection.chunk_count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-2xl border border-dashed border-gray-200 bg-gray-50 px-5 py-10 text-center">
                  <Database className="mx-auto h-8 w-8 text-gray-400" />
                  <p className="mt-3 text-sm text-gray-500">当前还没有知识库集合写入向量存储</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {showModal && (
        <Modal onClose={closeModal} panelClassName="max-w-2xl">
          <div className="relative max-h-[inherit] overflow-y-auto rounded-[1.75rem] bg-white p-6 shadow-2xl">
            <div className="absolute left-0 right-0 top-0 h-1 rounded-t-[1.75rem] bg-gradient-to-r from-primary-500 via-primary-600 to-dark"></div>

            <div className="mb-6 mt-2 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary-600">
                  <HardDrive className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-900">{editingProfile ? '编辑向量数据库配置' : '新建向量数据库配置'}</h3>
                  <p className="text-sm text-gray-500">用于维护候选连接，不会直接改写运行时 .env 配置</p>
                </div>
              </div>
              <button type="button" onClick={closeModal} className="rounded-2xl p-2 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600">
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              {modalError && (
                <div className="flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-600">
                  <AlertCircle className="h-4 w-4 flex-shrink-0" />
                  {modalError}
                </div>
              )}

              <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
                <div>
                  <label className="mb-2 block text-sm font-semibold text-gray-700">配置名称</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(event) => setFormData({ ...formData, name: event.target.value })}
                    className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 outline-none transition-all focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
                    placeholder="例如：生产 Chroma"
                    required
                  />
                </div>
                <div>
                  <label className="mb-2 block text-sm font-semibold text-gray-700">存储类型</label>
                  <select
                    value={formData.store_type}
                    onChange={(event) => setFormData({
                      ...formData,
                      store_type: event.target.value as VectorStoreType,
                      persist_path: event.target.value === 'milvus' ? '' : formData.persist_path || './data/vectorstore',
                    })}
                    className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 outline-none transition-all focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
                  >
                    <option value="chroma">Chroma</option>
                    <option value="faiss">FAISS</option>
                    <option value="milvus">Milvus</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="mb-2 block text-sm font-semibold text-gray-700">描述</label>
                <textarea
                  value={formData.description}
                  onChange={(event) => setFormData({ ...formData, description: event.target.value })}
                  rows={3}
                  className="w-full resize-none rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 outline-none transition-all focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
                  placeholder="记录该配置的用途、环境或注意事项"
                />
              </div>

              {formData.store_type === 'milvus' ? (
                <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
                  <div>
                    <label className="mb-2 block text-sm font-semibold text-gray-700">主机地址</label>
                    <input
                      type="text"
                      value={formData.host || ''}
                      onChange={(event) => setFormData({ ...formData, host: event.target.value })}
                      className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 outline-none transition-all focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
                      placeholder="localhost"
                      required
                    />
                  </div>
                  <div>
                    <label className="mb-2 block text-sm font-semibold text-gray-700">端口</label>
                    <input
                      type="number"
                      value={formData.port || 19530}
                      onChange={(event) => setFormData({ ...formData, port: Number(event.target.value) })}
                      className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 outline-none transition-all focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
                      min={1}
                      max={65535}
                      required
                    />
                  </div>
                </div>
              ) : (
                <div>
                  <label className="mb-2 block text-sm font-semibold text-gray-700">持久化路径</label>
                  <input
                    type="text"
                    value={formData.persist_path || ''}
                    onChange={(event) => setFormData({ ...formData, persist_path: event.target.value })}
                    className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 outline-none transition-all focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
                    placeholder="./data/vectorstore"
                    required
                  />
                </div>
              )}

              <div>
                <label className="mb-2 block text-sm font-semibold text-gray-700">集合前缀</label>
                <input
                  type="text"
                  value={formData.collection_prefix || ''}
                  onChange={(event) => setFormData({ ...formData, collection_prefix: event.target.value })}
                  className="w-full rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 outline-none transition-all focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20"
                  placeholder="可选，用于标记环境或业务前缀"
                />
              </div>

              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <label className="flex items-center gap-3 rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3">
                  <input
                    type="checkbox"
                    checked={formData.is_default}
                    onChange={(event) => setFormData({ ...formData, is_default: event.target.checked })}
                    className="h-4 w-4 rounded border-gray-300 text-primary-600"
                  />
                  <span className="text-sm font-medium text-gray-700">设为默认配置</span>
                </label>
                <label className="flex items-center gap-3 rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3">
                  <input
                    type="checkbox"
                    checked={formData.is_enabled}
                    onChange={(event) => setFormData({ ...formData, is_enabled: event.target.checked })}
                    className="h-4 w-4 rounded border-gray-300 text-primary-600"
                  />
                  <span className="text-sm font-medium text-gray-700">启用该配置</span>
                </label>
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={closeModal}
                  className="flex-1 rounded-[1.1rem] border border-gray-200 px-4 py-3 font-medium text-gray-700 transition-colors hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 rounded-[1.1rem] bg-primary-600 px-4 py-3 font-semibold text-white shadow-md shadow-primary-600/15 transition-all hover:bg-primary-700 disabled:opacity-60"
                >
                  {saving ? '保存中...' : editingProfile ? '保存更改' : '创建配置'}
                </button>
              </div>
            </form>
          </div>
        </Modal>
      )}

      {deleteTarget && (
        <ConfirmDialog
          title="删除向量数据库配置"
          description={`确定要删除配置 “${deleteTarget.name}” 吗？这不会修改当前 RAG 运行时环境，但会移除后台维护档案。`}
          confirmText="确认删除"
          loading={deleting}
          tone="danger"
          onClose={() => setDeleteTarget(null)}
          onConfirm={handleDelete}
        />
      )}
    </div>
  )
}

export default VectorDatabasesPage
