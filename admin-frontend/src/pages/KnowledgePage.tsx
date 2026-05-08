import React, { useEffect, useMemo, useRef, useState } from 'react'
import {
  AlertCircle,
  CalendarClock,
  CheckCircle2,
  Database,
  Edit3,
  FileIcon,
  FileSearch,
  Files,
  Inbox,
  Loader2,
  Plus,
  RefreshCw,
  Search,
  SlidersHorizontal,
  Trash2,
  Upload,
  X,
} from 'lucide-react'
import Modal from '@/components/Modal'
import ConfirmDialog from '@/components/ConfirmDialog'
import { cn } from '@/lib/utils'
import { kbApi, type KnowledgeBase, type SearchResult } from '@/lib/api'

type FeedbackState = {
  tone: 'success' | 'error'
  message: string
} | null

type SearchFormState = {
  query: string
  top_k: number
  retrieval_mode: 'vector' | 'hybrid'
  use_reranker: boolean
}

const formatDateTime = (value?: string) => {
  if (!value) {
    return '--'
  }

  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

const formatFileSize = (size: number) => {
  if (size < 1024) {
    return `${size} B`
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`
  }
  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

const DEFAULT_SEARCH_FORM: SearchFormState = {
  query: '',
  top_k: 5,
  retrieval_mode: 'vector',
  use_reranker: false,
}

const KnowledgePage: React.FC = () => {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [feedback, setFeedback] = useState<FeedbackState>(null)
  const [listQuery, setListQuery] = useState('')
  const [selectedKbId, setSelectedKbId] = useState<string | null>(null)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingKb, setEditingKb] = useState<KnowledgeBase | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<KnowledgeBase | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [creating, setCreating] = useState(false)
  const [createForm, setCreateForm] = useState({ name: '', description: '' })
  const [uploadFiles, setUploadFiles] = useState<File[]>([])
  const [dragActive, setDragActive] = useState(false)
  const [searchForm, setSearchForm] = useState<SearchFormState>(DEFAULT_SEARCH_FORM)
  const [searching, setSearching] = useState(false)
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [searchExecuted, setSearchExecuted] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const fetchKnowledgeBases = async (silent = false) => {
    try {
      if (silent) {
        setRefreshing(true)
      } else {
        setLoading(true)
      }
      const data = await kbApi.list()
      setKnowledgeBases(data.knowledge_bases)
      setSelectedKbId((current) => {
        if (current && data.knowledge_bases.some((kb) => kb.id === current)) {
          return current
        }
        return data.knowledge_bases[0]?.id ?? null
      })
    } catch (err) {
      console.error('Failed to fetch knowledge bases:', err)
      setFeedback({ tone: 'error', message: '加载知识库失败，请确认管理后端与 RAG 服务都已启动。' })
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    void fetchKnowledgeBases()
  }, [])

  const filteredKnowledgeBases = useMemo(() => {
    const query = listQuery.trim().toLowerCase()
    if (!query) {
      return knowledgeBases
    }
    return knowledgeBases.filter((kb) =>
      kb.name.toLowerCase().includes(query) ||
      (kb.description || '').toLowerCase().includes(query) ||
      kb.embedding_model.toLowerCase().includes(query)
    )
  }, [knowledgeBases, listQuery])

  const selectedKb = useMemo(
    () => knowledgeBases.find((item) => item.id === selectedKbId) ?? null,
    [knowledgeBases, selectedKbId]
  )

  const totals = useMemo(() => ({
    knowledgeBases: knowledgeBases.length,
    documents: knowledgeBases.reduce((sum, kb) => sum + kb.document_count, 0),
    chunks: knowledgeBases.reduce((sum, kb) => sum + kb.chunk_count, 0),
  }), [knowledgeBases])

  const openCreateModal = () => {
    setEditingKb(null)
    setCreateForm({ name: '', description: '' })
    setShowCreateModal(true)
  }

  const openEditModal = (kb: KnowledgeBase) => {
    setEditingKb(kb)
    setCreateForm({ name: kb.name, description: kb.description || '' })
    setShowCreateModal(true)
  }

  const handleCreateKnowledgeBase = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!createForm.name.trim()) {
      setFeedback({ tone: 'error', message: '知识库名称不能为空。' })
      return
    }

    try {
      setCreating(true)
      const saved = editingKb
        ? await kbApi.update(editingKb.id, {
            name: createForm.name.trim(),
            description: createForm.description.trim(),
          })
        : await kbApi.create({
            name: createForm.name.trim(),
            description: createForm.description.trim(),
          })

      setFeedback({
        tone: 'success',
        message: editingKb ? `知识库 ${saved.name} 已更新` : `知识库 ${saved.name} 已创建`,
      })
      setShowCreateModal(false)
      setEditingKb(null)
      setCreateForm({ name: '', description: '' })
      await fetchKnowledgeBases(true)
      setSelectedKbId(saved.id)
    } catch (err) {
      console.error('Failed to save knowledge base:', err)
      setFeedback({ tone: 'error', message: editingKb ? '更新知识库失败。' : '创建知识库失败。' })
    } finally {
      setCreating(false)
    }
  }

  const handleDelete = async () => {
    if (!deleteTarget) {
      return
    }

    try {
      setDeleting(true)
      await kbApi.delete(deleteTarget.id)
      setFeedback({ tone: 'success', message: `知识库 ${deleteTarget.name} 已删除` })
      setDeleteTarget(null)
      setSearchResults([])
      setSearchExecuted(false)
      await fetchKnowledgeBases(true)
    } catch (err) {
      console.error('Delete failed:', err)
      setFeedback({ tone: 'error', message: '删除知识库失败。' })
    } finally {
      setDeleting(false)
    }
  }

  const openUploadModal = () => {
    setUploadFiles([])
    setDragActive(false)
    setShowUploadModal(true)
  }

  const closeUploadModal = (force = false) => {
    if (uploading && !force) {
      return
    }
    setUploadFiles([])
    setDragActive(false)
    setShowUploadModal(false)
  }

  const handleUploadSubmit = async () => {
    if (!selectedKb || uploadFiles.length === 0) {
      return
    }

    try {
      setUploading(true)
      for (const file of uploadFiles) {
        await kbApi.upload(selectedKb.id, file)
      }
      setFeedback({ tone: 'success', message: `已向 ${selectedKb.name} 上传 ${uploadFiles.length} 个文件` })
      closeUploadModal(true)
      await fetchKnowledgeBases(true)
    } catch (err) {
      console.error('Upload failed:', err)
      setFeedback({ tone: 'error', message: '文件上传失败，请检查文件类型或后端日志。' })
    } finally {
      setUploading(false)
    }
  }

  const handleSearchSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!selectedKb || !searchForm.query.trim()) {
      return
    }

    try {
      setSearching(true)
      const response = await kbApi.search(selectedKb.id, {
        query: searchForm.query.trim(),
        top_k: searchForm.top_k,
        retrieval_mode: searchForm.retrieval_mode,
        use_reranker: searchForm.use_reranker,
      })
      setSearchResults(response.results)
      setSearchExecuted(true)
    } catch (err) {
      console.error('Search failed:', err)
      setSearchResults([])
      setSearchExecuted(true)
      setFeedback({ tone: 'error', message: '检索失败，请稍后重试。' })
    } finally {
      setSearching(false)
    }
  }

  const addFiles = (files: FileList | File[]) => {
    const incoming = Array.from(files)
    setUploadFiles((current) => {
      const existingKeys = new Set(current.map((file) => `${file.name}-${file.size}`))
      return [
        ...current,
        ...incoming.filter((file) => !existingKeys.has(`${file.name}-${file.size}`)),
      ]
    })
  }

  const summaryCards = [
    { label: '知识库', value: totals.knowledgeBases, helper: '当前已接入' },
    { label: '文档', value: totals.documents, helper: '累计文档数' },
    { label: '切片', value: totals.chunks, helper: '已建立检索索引' },
    { label: '当前选择', value: selectedKb ? selectedKb.document_count : 0, helper: selectedKb ? `${selectedKb.name} 的文档数` : '请选择知识库' },
  ]

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

      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">知识库管理</h1>
          <p className="mt-1 text-gray-500">在统一管理后台中维护知识库、上传文档并验证检索质量。</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <button type="button" onClick={() => void fetchKnowledgeBases(true)} disabled={refreshing} className="btn-secondary">
            <RefreshCw className={cn('h-4 w-4', refreshing && 'animate-spin')} />
            {refreshing ? '刷新中...' : '刷新列表'}
          </button>
          <button type="button" onClick={openCreateModal} className="btn-primary">
            <Plus className="h-4 w-4" />
            新建知识库
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
        {summaryCards.map((card, index) => (
          <div
            key={card.label}
            className="rounded-2xl border border-gray-200 bg-white p-5 animate-rise-in"
            style={{ animationDelay: `${index * 60}ms` }}
          >
            <p className="text-sm text-gray-500">{card.label}</p>
            <p className="mt-2 text-3xl font-bold text-gray-900">{card.value}</p>
            <p className="mt-3 text-sm text-gray-500">{card.helper}</p>
          </div>
        ))}
      </div>

      {loading ? (
        <div className="flex min-h-[22rem] items-center justify-center rounded-2xl border border-gray-200 bg-white">
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="h-10 w-10 animate-spin text-primary-600" />
            <p className="text-sm text-gray-500">正在加载知识库数据...</p>
          </div>
        </div>
      ) : knowledgeBases.length === 0 ? (
        <div className="rounded-2xl border border-gray-200 bg-white px-6 py-16 text-center">
          <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-2xl bg-gray-100">
            <Database className="h-10 w-10 text-gray-400" />
          </div>
          <h2 className="mt-6 text-xl font-bold text-gray-900">还没有知识库</h2>
          <p className="mt-2 text-gray-500">先创建知识库，再上传文档并在右侧检索面板验证效果。</p>
          <button type="button" onClick={openCreateModal} className="btn-primary mt-6">
            <Plus className="h-4 w-4" />
            创建第一个知识库
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-[0.95fr_1.25fr] xl:items-start">
          <section className="flex min-h-0 flex-col overflow-hidden rounded-2xl border border-gray-200 bg-white xl:sticky xl:top-0 xl:h-[calc(100vh-8.5rem)]">
            <div className="border-b border-gray-100 px-6 py-5">
              <div className="flex items-center gap-2">
                <Search className="h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  value={listQuery}
                  onChange={(event) => setListQuery(event.target.value)}
                  placeholder="搜索名称、描述或 embedding 模型"
                  className="w-full border-none bg-transparent text-sm text-gray-800 outline-none placeholder:text-gray-400"
                />
              </div>
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto p-3">
              {filteredKnowledgeBases.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-gray-200 px-4 py-10 text-center text-sm text-gray-500">
                  没有匹配的知识库，换个关键词试试。
                </div>
              ) : (
                <div className="space-y-3">
                  {filteredKnowledgeBases.map((kb, index) => {
                    const active = kb.id === selectedKbId
                    return (
                      <button
                        key={kb.id}
                        type="button"
                        onClick={() => {
                          setSelectedKbId(kb.id)
                          setSearchResults([])
                          setSearchExecuted(false)
                        }}
                        className={cn(
                          'w-full rounded-2xl border p-4 text-left transition-all duration-200 animate-rise-in',
                          active
                            ? 'border-primary-300 bg-primary-50 shadow-md shadow-primary-600/10'
                            : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50'
                        )}
                        style={{ animationDelay: `${index * 40}ms` }}
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div className="min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="rounded-full bg-white px-2.5 py-1 text-xs font-semibold text-primary-700">
                                {kb.embedding_model}
                              </span>
                              <span className="text-xs text-gray-400">{formatDateTime(kb.updated_at)}</span>
                            </div>
                            <p className="mt-3 truncate text-base font-semibold text-gray-900">{kb.name}</p>
                            <p className="mt-1 text-sm leading-6 text-gray-500">{kb.description || '暂无描述'}</p>
                          </div>
                          <div className={cn(
                            'flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-2xl',
                            active ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600'
                          )}>
                            <Database className="h-5 w-5" />
                          </div>
                        </div>
                        <div className="mt-4 grid grid-cols-2 gap-3">
                          <div className="rounded-2xl bg-white/80 px-3 py-3">
                            <p className="text-xs text-gray-500">文档</p>
                            <p className="mt-1 text-lg font-bold text-gray-900">{kb.document_count}</p>
                          </div>
                          <div className="rounded-2xl bg-white/80 px-3 py-3">
                            <p className="text-xs text-gray-500">切片</p>
                            <p className="mt-1 text-lg font-bold text-gray-900">{kb.chunk_count}</p>
                          </div>
                        </div>
                      </button>
                    )
                  })}
                </div>
              )}
            </div>
          </section>

          <section className="space-y-6">
            {selectedKb && (
              <>
                <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white">
                  <div className="border-b border-gray-100 px-6 py-5">
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="rounded-full bg-primary-50 px-3 py-1 text-xs font-semibold text-primary-700">
                            {selectedKb.embedding_model}
                          </span>
                          <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-semibold text-gray-600">
                            最近更新 {formatDateTime(selectedKb.updated_at)}
                          </span>
                        </div>
                        <h2 className="mt-4 text-2xl font-bold text-gray-900">{selectedKb.name}</h2>
                        <p className="mt-2 max-w-3xl text-sm leading-7 text-gray-500">
                          {selectedKb.description || '这个知识库还没有描述，可以补充业务范围、文档来源或适用场景。'}
                        </p>
                      </div>
                      <div className="flex flex-wrap gap-3">
                        <button type="button" onClick={openUploadModal} className="btn-primary">
                          <Upload className="h-4 w-4" />
                          上传文档
                        </button>
                        <button type="button" onClick={() => openEditModal(selectedKb)} className="btn-secondary">
                          <Edit3 className="h-4 w-4" />
                          编辑信息
                        </button>
                        <button
                          type="button"
                          onClick={() => setDeleteTarget(selectedKb)}
                          className="inline-flex items-center justify-center gap-2 rounded-[1.1rem] border border-red-200 px-4 py-2 text-sm font-medium text-red-600 transition-colors hover:bg-red-50"
                        >
                          <Trash2 className="h-4 w-4" />
                          删除
                        </button>
                      </div>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4 p-6 xl:grid-cols-4">
                    <div className="rounded-2xl bg-gray-50 p-4">
                      <p className="text-xs text-gray-500">文档数</p>
                      <p className="mt-2 text-2xl font-bold text-gray-900">{selectedKb.document_count}</p>
                    </div>
                    <div className="rounded-2xl bg-gray-50 p-4">
                      <p className="text-xs text-gray-500">切片数</p>
                      <p className="mt-2 text-2xl font-bold text-gray-900">{selectedKb.chunk_count}</p>
                    </div>
                    <div className="rounded-2xl bg-gray-50 p-4">
                      <p className="text-xs text-gray-500">创建时间</p>
                      <p className="mt-2 text-sm font-semibold text-gray-900">{formatDateTime(selectedKb.created_at)}</p>
                    </div>
                    <div className="rounded-2xl bg-gray-50 p-4">
                      <p className="text-xs text-gray-500">最后更新时间</p>
                      <p className="mt-2 text-sm font-semibold text-gray-900">{formatDateTime(selectedKb.updated_at)}</p>
                    </div>
                  </div>
                </div>

                <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white">
                  <div className="flex flex-col gap-3 border-b border-gray-100 px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
                    <div>
                      <h3 className="flex items-center gap-2 text-lg font-bold text-gray-900">
                        <FileSearch className="h-5 w-5 text-primary-600" />
                        检索验证台
                      </h3>
                      <p className="mt-1 text-sm text-gray-500">上传完成后，直接对当前知识库做搜索验证，快速判断召回质量。</p>
                    </div>
                    <div className="rounded-full bg-gray-100 px-3 py-1 text-xs font-semibold text-gray-700">
                      当前模式：{searchForm.retrieval_mode === 'hybrid' ? '混合检索' : '向量检索'}
                    </div>
                  </div>

                  <div className="space-y-5 p-6">
                    <form onSubmit={handleSearchSubmit} className="space-y-4">
                      <div className="rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3">
                        <div className="flex items-center gap-3">
                          <Search className="h-4 w-4 text-gray-400" />
                          <input
                            type="text"
                            value={searchForm.query}
                            onChange={(event) => setSearchForm((current) => ({ ...current, query: event.target.value }))}
                            placeholder="输入一个问题，例如：系统如何配置向量数据库？"
                            className="w-full border-none bg-transparent text-sm text-gray-800 outline-none placeholder:text-gray-400"
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[0.9fr_0.9fr_0.8fr_auto]">
                        <label className="rounded-2xl border border-gray-200 bg-white px-4 py-3">
                          <p className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
                            <SlidersHorizontal className="h-3.5 w-3.5" />
                            检索模式
                          </p>
                          <select
                            value={searchForm.retrieval_mode}
                            onChange={(event) => setSearchForm((current) => ({
                              ...current,
                              retrieval_mode: event.target.value as SearchFormState['retrieval_mode'],
                            }))}
                            className="w-full border-none bg-transparent text-sm font-medium text-gray-900 outline-none"
                          >
                            <option value="vector">向量检索</option>
                            <option value="hybrid">混合检索</option>
                          </select>
                        </label>

                        <label className="rounded-2xl border border-gray-200 bg-white px-4 py-3">
                          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">返回条数</p>
                          <input
                            type="number"
                            min={1}
                            max={10}
                            value={searchForm.top_k}
                            onChange={(event) => setSearchForm((current) => ({
                              ...current,
                              top_k: Number(event.target.value || 1),
                            }))}
                            className="w-full border-none bg-transparent text-sm font-medium text-gray-900 outline-none"
                          />
                        </label>

                        <label className="flex items-center gap-3 rounded-2xl border border-gray-200 bg-white px-4 py-3">
                          <input
                            type="checkbox"
                            checked={searchForm.use_reranker}
                            onChange={(event) => setSearchForm((current) => ({
                              ...current,
                              use_reranker: event.target.checked,
                            }))}
                            className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                          />
                          <div>
                            <p className="text-sm font-semibold text-gray-900">启用重排</p>
                            <p className="text-xs text-gray-500">适合提高前几条结果质量</p>
                          </div>
                        </label>

                        <button type="submit" disabled={searching || !searchForm.query.trim()} className="btn-primary h-full min-h-[3.5rem]">
                          {searching ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                          {searching ? '检索中...' : '开始检索'}
                        </button>
                      </div>
                    </form>

                    <div className="space-y-3">
                      {searching ? (
                        <div className="rounded-2xl border border-gray-200 bg-gray-50 px-4 py-14 text-center">
                          <Loader2 className="mx-auto h-6 w-6 animate-spin text-primary-600" />
                          <p className="mt-4 text-sm text-gray-500">正在执行检索并整理结果...</p>
                        </div>
                      ) : searchResults.length > 0 ? (
                        searchResults.map((result, index) => {
                          const source =
                            typeof result.metadata.source === 'string'
                              ? result.metadata.source
                              : '未知来源'
                          return (
                            <div key={`${source}-${index}`} className="rounded-2xl border border-gray-200 bg-gray-50 p-5">
                              <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                                <div className="min-w-0">
                                  <div className="flex flex-wrap items-center gap-2">
                                    <span className="rounded-full bg-white px-2.5 py-1 text-xs font-semibold text-primary-700">
                                      命中 #{index + 1}
                                    </span>
                                    <span className="rounded-full bg-white px-2.5 py-1 text-xs font-semibold text-gray-600">
                                      {source}
                                    </span>
                                  </div>
                                  <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-gray-700">
                                    {result.content}
                                  </p>
                                </div>
                                <div className="rounded-2xl bg-white px-4 py-3 text-sm">
                                  <p className="text-xs text-gray-500">相关度</p>
                                  <p className="mt-1 text-lg font-bold text-gray-900">{result.score.toFixed(3)}</p>
                                </div>
                              </div>
                            </div>
                          )
                        })
                      ) : searchExecuted ? (
                        <div className="rounded-2xl border border-dashed border-gray-200 px-4 py-14 text-center">
                          <Inbox className="mx-auto h-8 w-8 text-gray-300" />
                          <p className="mt-4 text-sm font-medium text-gray-700">没有检索到结果</p>
                          <p className="mt-2 text-sm text-gray-500">尝试扩大返回条数、切换混合检索，或者先补充文档内容。</p>
                        </div>
                      ) : (
                        <div className="rounded-2xl border border-dashed border-gray-200 px-4 py-14 text-center">
                          <FileSearch className="mx-auto h-8 w-8 text-gray-300" />
                          <p className="mt-4 text-sm font-medium text-gray-700">还没有执行检索</p>
                          <p className="mt-2 text-sm text-gray-500">输入一个真实业务问题，直接查看当前知识库的召回结果。</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                <div className="rounded-2xl border border-gray-200 bg-white p-6">
                  <h3 className="flex items-center gap-2 text-lg font-bold text-gray-900">
                    <CalendarClock className="h-5 w-5 text-primary-600" />
                    使用提示
                  </h3>
                  <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">
                    <div className="rounded-2xl bg-gray-50 p-4">
                      <p className="text-sm font-semibold text-gray-900">先传文档再搜</p>
                      <p className="mt-2 text-sm leading-6 text-gray-500">上传后系统会自动分块与建立索引，右侧即可立即验证结果。</p>
                    </div>
                    <div className="rounded-2xl bg-gray-50 p-4">
                      <p className="text-sm font-semibold text-gray-900">问题尽量具体</p>
                      <p className="mt-2 text-sm leading-6 text-gray-500">使用真实业务问句更容易看出召回是否足够精准。</p>
                    </div>
                    <div className="rounded-2xl bg-gray-50 p-4">
                      <p className="text-sm font-semibold text-gray-900">重排适合精排</p>
                      <p className="mt-2 text-sm leading-6 text-gray-500">结果很多时启用重排，可以提升前几条命中的相关性。</p>
                    </div>
                  </div>
                </div>
              </>
            )}
          </section>
        </div>
      )}

      {showCreateModal && (
        <Modal onClose={!creating ? () => setShowCreateModal(false) : undefined} closeOnBackdropClick={!creating} panelClassName="max-w-xl">
          <div className="rounded-[1.75rem] bg-white p-6 shadow-2xl">
            <div className="mb-6 flex items-start justify-between gap-4">
              <div>
                <h3 className="text-xl font-bold text-gray-900">{editingKb ? '编辑知识库' : '新建知识库'}</h3>
                <p className="mt-1 text-sm text-gray-500">维护知识库名称和描述，方便团队识别用途。</p>
              </div>
              <button type="button" onClick={() => setShowCreateModal(false)} disabled={creating} className="rounded-2xl p-2 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600">
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleCreateKnowledgeBase} className="space-y-4">
              <label className="block">
                <span className="mb-2 block text-sm font-semibold text-gray-900">名称</span>
                <input
                  type="text"
                  value={createForm.name}
                  onChange={(event) => setCreateForm((current) => ({ ...current, name: event.target.value }))}
                  placeholder="例如：产品知识库"
                  className="input-modern"
                />
              </label>
              <label className="block">
                <span className="mb-2 block text-sm font-semibold text-gray-900">描述</span>
                <textarea
                  value={createForm.description}
                  onChange={(event) => setCreateForm((current) => ({ ...current, description: event.target.value }))}
                  placeholder="说明这个知识库的文档范围、负责人或适用场景"
                  rows={4}
                  className="input-modern resize-none"
                />
              </label>

              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowCreateModal(false)} disabled={creating} className="btn-secondary flex-1">
                  取消
                </button>
                <button type="submit" disabled={creating} className="btn-primary flex-1">
                  {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
                  {creating ? '保存中...' : editingKb ? '保存修改' : '创建知识库'}
                </button>
              </div>
            </form>
          </div>
        </Modal>
      )}

      {showUploadModal && selectedKb && (
        <Modal onClose={closeUploadModal} closeOnBackdropClick={!uploading} panelClassName="max-w-2xl">
          <div className="rounded-[1.75rem] bg-white p-6 shadow-2xl">
            <div className="mb-6 flex items-start justify-between gap-4">
              <div>
                <h3 className="text-xl font-bold text-gray-900">上传文档到 {selectedKb.name}</h3>
                <p className="mt-1 text-sm text-gray-500">支持多文件上传，提交后会自动分块并建立向量索引。</p>
              </div>
              <button type="button" onClick={() => closeUploadModal()} disabled={uploading} className="rounded-2xl p-2 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600">
                <X className="h-5 w-5" />
              </button>
            </div>

            <input
              ref={fileInputRef}
              type="file"
              multiple
              className="hidden"
              onChange={(event) => addFiles(event.target.files || [])}
            />

            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              onDragEnter={() => setDragActive(true)}
              onDragOver={(event) => {
                event.preventDefault()
                setDragActive(true)
              }}
              onDragLeave={() => setDragActive(false)}
              onDrop={(event) => {
                event.preventDefault()
                setDragActive(false)
                addFiles(event.dataTransfer.files)
              }}
              className={cn(
                'flex w-full flex-col items-center justify-center rounded-[1.6rem] border border-dashed px-6 py-12 text-center transition-all',
                dragActive
                  ? 'border-primary-400 bg-primary-50'
                  : 'border-gray-300 bg-gray-50 hover:border-primary-300 hover:bg-primary-50/60'
              )}
            >
              <Upload className="h-8 w-8 text-primary-600" />
              <p className="mt-4 text-base font-semibold text-gray-900">拖拽文件到这里，或点击选择文件</p>
              <p className="mt-2 text-sm text-gray-500">常见文档格式会自动解析并写入当前知识库。</p>
            </button>

            <div className="mt-5 space-y-3">
              {uploadFiles.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-gray-200 px-4 py-8 text-center text-sm text-gray-500">
                  还没有选择文件。
                </div>
              ) : (
                uploadFiles.map((file) => (
                  <div key={`${file.name}-${file.size}`} className="flex items-center justify-between rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3">
                    <div className="flex min-w-0 items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white text-gray-600">
                        <FileIcon className="h-4 w-4" />
                      </div>
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-gray-900">{file.name}</p>
                        <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => setUploadFiles((current) => current.filter((item) => item !== file))}
                      className="rounded-2xl p-2 text-gray-400 transition-colors hover:bg-white hover:text-gray-600"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                ))
              )}
            </div>

            <div className="mt-6 flex gap-3">
              <button type="button" onClick={() => closeUploadModal()} disabled={uploading} className="btn-secondary flex-1">
                取消
              </button>
              <button type="button" onClick={() => void handleUploadSubmit()} disabled={uploading || uploadFiles.length === 0} className="btn-primary flex-1">
                {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Files className="h-4 w-4" />}
                {uploading ? '上传中...' : `开始上传 (${uploadFiles.length})`}
              </button>
            </div>
          </div>
        </Modal>
      )}

      {deleteTarget && (
        <ConfirmDialog
          title="删除知识库"
          description={`确认删除 ${deleteTarget.name} 吗？该操作会移除知识库元数据与向量索引，且不可恢复。`}
          confirmText="确认删除"
          onConfirm={handleDelete}
          onClose={() => setDeleteTarget(null)}
          loading={deleting}
          tone="danger"
        />
      )}
    </div>
  )
}

export default KnowledgePage
