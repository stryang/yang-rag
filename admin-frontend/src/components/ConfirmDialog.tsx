import React from 'react'
import { AlertTriangle, Trash2, X } from 'lucide-react'
import Modal from '@/components/Modal'
import { cn } from '@/lib/utils'

interface ConfirmDialogProps {
  title: string
  description: string
  confirmText: string
  onConfirm: () => void | Promise<void>
  onClose: () => void
  loading?: boolean
  tone?: 'danger' | 'default'
}

const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  title,
  description,
  confirmText,
  onConfirm,
  onClose,
  loading = false,
  tone = 'default',
}) => {
  const isDanger = tone === 'danger'

  return (
    <Modal onClose={!loading ? onClose : undefined} closeOnBackdropClick={!loading} panelClassName="max-w-md">
      <div className="relative max-h-[inherit] overflow-y-auto rounded-[1.75rem] bg-white p-6 shadow-2xl">
        <div className={cn(
          'absolute left-0 right-0 top-0 h-1 rounded-t-[1.75rem]',
          isDanger
            ? 'bg-gradient-to-r from-red-500 via-orange-500 to-amber-500'
            : 'bg-gradient-to-r from-primary-500 via-primary-600 to-dark'
        )}></div>

        <div className="mb-6 mt-2 flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className={cn(
              'flex h-11 w-11 items-center justify-center rounded-2xl',
              isDanger ? 'bg-red-50 text-red-600' : 'bg-primary-50 text-primary-600'
            )}>
              {isDanger ? <Trash2 className="h-5 w-5" /> : <AlertTriangle className="h-5 w-5" />}
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900">{title}</h3>
              <p className="mt-1 text-sm leading-6 text-gray-500">{description}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="rounded-2xl p-2 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex gap-3">
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="flex-1 rounded-[1.1rem] border border-gray-200 px-4 py-3 font-medium text-gray-700 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            取消
          </button>
          <button
            type="button"
            onClick={() => void onConfirm()}
            disabled={loading}
            className={cn(
              'flex-1 rounded-[1.1rem] px-4 py-3 font-semibold text-white transition-all disabled:cursor-not-allowed disabled:opacity-50',
              isDanger
                ? 'bg-red-600 shadow-md shadow-red-600/15 hover:bg-red-700'
                : 'bg-primary-600 shadow-md shadow-primary-600/15 hover:bg-primary-700'
            )}
          >
            {loading ? '处理中...' : confirmText}
          </button>
        </div>
      </div>
    </Modal>
  )
}

export default ConfirmDialog
