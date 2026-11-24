import { useEffect, useRef, useState } from 'react'
import {
  AlertCircle,
  Check,
  FileText,
  Loader2,
  UploadCloud,
  X,
} from 'lucide-react'
import { createCourse } from '../api'
import type { CourseSummary } from '../types'

const STEPS = [
  'Tekst lokaal uitlezen & opschonen (0 tokens)',
  'Kernconcepten bepalen (Laag 1)',
  'Verbanden & 80%-vragen genereren',
  'Interactieve graaf opbouwen',
]

interface CreateCourseModalProps {
  open: boolean
  onClose: () => void
  onCreated: (course: CourseSummary) => void
}

function isAllowedFile(file: File): boolean {
  const extension = file.name.toLowerCase().split('.').pop() ?? ''
  return extension === 'pdf' || extension === 'pptx'
}

export default function CreateCourseModal({
  open,
  onClose,
  onCreated,
}: CreateCourseModalProps) {
  const [title, setTitle] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [dragging, setDragging] = useState(false)
  const [busy, setBusy] = useState(false)
  const [step, setStep] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const timersRef = useRef<number[]>([])
  const inputRef = useRef<HTMLInputElement>(null)

  const clearTimers = () => {
    timersRef.current.forEach((timer) => window.clearTimeout(timer))
    timersRef.current = []
  }

  useEffect(() => {
    return () => {
      timersRef.current.forEach((timer) => window.clearTimeout(timer))
    }
  }, [])

  if (!open) return null

  const addFiles = (incoming: FileList | File[]) => {
    const accepted: File[] = []
    const rejected: string[] = []
    Array.from(incoming).forEach((file) => {
      if (isAllowedFile(file)) accepted.push(file)
      else rejected.push(file.name)
    })

    if (rejected.length > 0) {
      setError(
        `Alleen .pdf en .pptx worden ondersteund. Geweigerd: ${rejected.join(', ')}`,
      )
    } else {
      setError(null)
    }

    setFiles((current) => {
      const merged = [...current]
      accepted.forEach((file) => {
        const duplicate = merged.some(
          (existing) =>
            existing.name === file.name && existing.size === file.size,
        )
        if (!duplicate) merged.push(file)
      })
      return merged
    })
  }

  const removeFile = (index: number) => {
    setFiles((current) => current.filter((_, position) => position !== index))
  }

  const handleSubmit = async () => {
    const cleanTitle = title.trim()
    if (!cleanTitle) {
      setError('Vul een vaknaam in.')
      return
    }
    if (files.length === 0) {
      setError('Voeg minstens één PDF- of PPTX-bestand toe.')
      return
    }

    setBusy(true)
    setError(null)
    setStep(0)
    clearTimers()
    timersRef.current.push(window.setTimeout(() => setStep(1), 900))
    timersRef.current.push(window.setTimeout(() => setStep(2), 2800))
    timersRef.current.push(window.setTimeout(() => setStep(3), 5500))

    try {
      const course = await createCourse(cleanTitle, files)
      clearTimers()
      setStep(4)
      timersRef.current.push(
        window.setTimeout(() => {
          setBusy(false)
          setStep(0)
          setTitle('')
          setFiles([])
          onCreated(course)
        }, 450),
      )
    } catch (caught) {
      clearTimers()
      setBusy(false)
      setStep(0)
      setError(
        caught instanceof Error
          ? caught.message
          : 'Er ging iets mis bij het aanmaken van het vak.',
      )
    }
  }

  const handleClose = () => {
    if (busy) return
    setError(null)
    onClose()
  }

  return (
    <div
      className="fixed inset-0 z-40 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"
      onClick={(event) => {
        if (event.target === event.currentTarget) handleClose()
      }}
    >
      <div className="flex max-h-[90vh] w-full max-w-lg flex-col overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 text-slate-100 shadow-2xl">
        <div className="flex items-start justify-between gap-3 border-b border-slate-800 px-5 py-4">
          <div>
            <h2 className="text-base font-semibold text-slate-100">
              Nieuw vak aanmaken
            </h2>
            <p className="mt-0.5 text-[11px] text-slate-400">
              Upload je PDF of PPTX — KnoopPunt bouwt de knowledge graph.
            </p>
          </div>
          <button
            type="button"
            onClick={handleClose}
            disabled={busy}
            title="Sluiten"
            className="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-slate-400 transition hover:bg-slate-800 hover:text-slate-200 disabled:opacity-40"
          >
            <X size={18} />
          </button>
        </div>

        <div className="overflow-y-auto px-5 py-5 scrollbar-thin">
          {busy ? (
            <div className="py-2">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                Vak wordt opgebouwd
              </p>
              <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
                <div
                  className="h-full rounded-full bg-indigo-500 transition-all duration-500"
                  style={{ width: `${Math.min(step / 4, 1) * 100}%` }}
                />
              </div>
              <ul className="mt-4 space-y-3">
                {STEPS.map((label, index) => {
                  const done = step > index
                  const active = step === index
                  return (
                    <li key={label} className="flex items-center gap-3">
                      <span
                        className={`grid h-6 w-6 shrink-0 place-items-center rounded-full text-[10px] font-bold ${
                          done
                            ? 'bg-emerald-500 text-white'
                            : active
                              ? 'bg-indigo-500/20 text-indigo-300 ring-2 ring-indigo-500/30'
                              : 'bg-slate-800 text-slate-500'
                        }`}
                      >
                        {done ? (
                          <Check size={12} strokeWidth={3} />
                        ) : active ? (
                          <Loader2 size={12} className="animate-spin" />
                        ) : (
                          index + 1
                        )}
                      </span>
                      <span
                        className={`text-[12px] ${
                          active
                            ? 'font-semibold text-slate-100'
                            : done
                              ? 'text-slate-400'
                              : 'text-slate-500'
                        }`}
                      >
                        {label}
                      </span>
                    </li>
                  )
                })}
              </ul>
              <p className="mt-5 rounded-lg bg-slate-800/60 px-3 py-2 text-[11px] leading-relaxed text-slate-400">
                {title.trim() || 'Je nieuwe vak'} is bijna klaar. Dit venster
                sluit automatisch zodra de graaf klaar is.
              </p>
            </div>
          ) : (
            <>
              <label className="block">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  Vaknaam
                </span>
                <input
                  type="text"
                  value={title}
                  onChange={(event) => setTitle(event.target.value)}
                  placeholder="Bijvoorbeeld: Databanken"
                  maxLength={200}
                  autoFocus
                  className="mt-1.5 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2.5 text-sm text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/20"
                />
              </label>

              <div className="mt-4">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  Cursusmateriaal
                </span>
                <div
                  onDragOver={(event) => {
                    event.preventDefault()
                    setDragging(true)
                  }}
                  onDragLeave={() => setDragging(false)}
                  onDrop={(event) => {
                    event.preventDefault()
                    setDragging(false)
                    addFiles(event.dataTransfer.files)
                  }}
                  className={`mt-1.5 flex flex-col items-center justify-center rounded-xl border-2 border-dashed px-4 py-7 text-center transition ${
                    dragging
                      ? 'border-indigo-400 bg-indigo-500/10'
                      : 'border-slate-700 bg-slate-950/60'
                  }`}
                >
                  <UploadCloud
                    size={26}
                    className={dragging ? 'text-indigo-400' : 'text-slate-500'}
                  />
                  <p className="mt-2 text-[12px] font-medium text-slate-300">
                    Sleep je bestanden hierheen
                  </p>
                  <p className="mt-0.5 text-[10px] text-slate-500">
                    of selecteer een .pdf / .pptx
                  </p>
                  <button
                    type="button"
                    onClick={() => inputRef.current?.click()}
                    className="mt-3 rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-[11px] font-semibold text-slate-200 shadow-sm transition hover:bg-slate-700"
                  >
                    Bestanden kiezen
                  </button>
                  <input
                    ref={inputRef}
                    type="file"
                    accept=".pdf,.pptx"
                    multiple
                    className="hidden"
                    onChange={(event) => {
                      if (event.target.files) addFiles(event.target.files)
                      event.target.value = ''
                    }}
                  />
                </div>
              </div>

              {files.length > 0 && (
                <ul className="mt-3 space-y-1.5">
                  {files.map((file, index) => (
                    <li
                      key={`${file.name}-${file.size}`}
                      className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800/60 px-2.5 py-1.5"
                    >
                      <FileText size={14} className="shrink-0 text-indigo-400" />
                      <span className="min-w-0 flex-1 truncate text-[11px] text-slate-300">
                        {file.name}
                      </span>
                      <span className="shrink-0 text-[10px] text-slate-500">
                        {(file.size / 1024).toFixed(0)} kB
                      </span>
                      <button
                        type="button"
                        onClick={() => removeFile(index)}
                        title="Bestand verwijderen"
                        className="rounded p-0.5 text-slate-500 transition hover:bg-rose-500/10 hover:text-rose-400"
                      >
                        <X size={12} />
                      </button>
                    </li>
                  ))}
                </ul>
              )}

              {error && (
                <div className="mt-4 flex items-start gap-2 rounded-lg border border-rose-500/40 bg-rose-950/50 px-3 py-2.5 text-[11px] leading-relaxed text-rose-200">
                  <AlertCircle size={14} className="mt-0.5 shrink-0" />
                  <span>{error}</span>
                </div>
              )}
            </>
          )}
        </div>

        {!busy && (
          <div className="flex justify-end gap-2 border-t border-slate-800 px-5 py-3.5">
            <button
              type="button"
              onClick={handleClose}
              className="rounded-lg border border-slate-700 px-3.5 py-2 text-[12px] font-medium text-slate-300 transition hover:bg-slate-800"
            >
              Annuleren
            </button>
            <button
              type="button"
              onClick={handleSubmit}
              className="rounded-lg bg-indigo-600 px-4 py-2 text-[12px] font-semibold text-white shadow-sm transition hover:bg-indigo-500 active:scale-[0.99]"
            >
              Vak aanmaken
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
