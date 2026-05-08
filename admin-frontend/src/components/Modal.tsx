import React, { useEffect } from 'react'
import { createPortal } from 'react-dom'
import { cn } from '@/lib/utils'

interface ModalProps {
  children: React.ReactNode
  onClose?: () => void
  closeOnBackdropClick?: boolean
  panelClassName?: string
}

const Modal: React.FC<ModalProps> = ({
  children,
  onClose,
  closeOnBackdropClick = true,
  panelClassName,
}) => {
  useEffect(() => {
    const previousOverflow = document.body.style.overflow
    const previousHtmlOverflow = document.documentElement.style.overflow
    document.body.style.overflow = 'hidden'
    document.documentElement.style.overflow = 'hidden'

    return () => {
      document.body.style.overflow = previousOverflow
      document.documentElement.style.overflow = previousHtmlOverflow
    }
  }, [])

  useEffect(() => {
    if (!onClose) return undefined

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose()
      }
    }

    window.addEventListener('keydown', handleKeyDown)

    return () => {
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [onClose])

  if (typeof document === 'undefined') {
    return null
  }

  return createPortal(
    <div className="fixed inset-0 z-[100] overflow-y-auto overscroll-contain">
      <div className="flex min-h-[100dvh] items-start justify-center p-4 sm:items-center sm:p-6">
        <div
          className="fixed inset-0 bg-black/40 backdrop-blur-sm"
          onClick={closeOnBackdropClick ? onClose : undefined}
        />
        <div
          className={cn('relative z-10 my-auto w-full max-h-[calc(100dvh-2rem)] sm:max-h-[calc(100dvh-3rem)]', panelClassName)}
          onClick={(event) => event.stopPropagation()}
        >
          {children}
        </div>
      </div>
    </div>,
    document.body
  )
}

export default Modal
