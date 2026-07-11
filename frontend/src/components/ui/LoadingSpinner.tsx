import { clsx } from 'clsx'

type Size  = 'sm' | 'md' | 'lg'
type Color = 'primary' | 'white' | 'slate'

const SIZES:  Record<Size,  string> = { sm: 'h-4 w-4', md: 'h-6 w-6', lg: 'h-10 w-10' }
const COLORS: Record<Color, string> = {
  primary: 'text-[#00ed64]',
  white:   'text-white',
  slate:   'text-[#a8b3bc]',
}

interface Props { size?: Size; color?: Color; className?: string }

export default function LoadingSpinner({ size = 'md', color = 'primary', className }: Props) {
  return (
    <div
      className={clsx(
        'animate-spin rounded-full border-2 border-current border-t-transparent',
        SIZES[size], COLORS[color], className,
      )}
      role="status"
      aria-label="Loading"
    >
      <span className="sr-only">Loading…</span>
    </div>
  )
}
