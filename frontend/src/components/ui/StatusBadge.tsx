import { clsx } from 'clsx'
import type { TestStatus } from '../../types'

const STATUS_CLASSES: Record<string, string> = {
  Normal:        'badge-normal',
  High:          'badge-high',
  Low:           'badge-low',
  'Very High':   'badge-high',
  'Very Low':    'badge-low',
  'Critical Low':  'badge-critical',
  'Critical High': 'badge-critical',
  Borderline:    'bg-yellow-100 text-yellow-800',
  Positive:      'badge-high',
  Negative:      'badge-normal',
  Unknown:       'badge-unknown',
}

interface Props {
  status: TestStatus | string
  className?: string
}

export default function StatusBadge({ status, className }: Props) {
  const cls = STATUS_CLASSES[status] ?? 'badge-unknown'
  return (
    <span className={clsx('inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium', cls, className)}>
      {status}
    </span>
  )
}
