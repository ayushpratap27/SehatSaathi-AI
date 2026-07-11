import { clsx } from 'clsx'

interface Props extends React.HTMLAttributes<HTMLDivElement> {
  title?: string
  noPadding?: boolean
}

export default function Card({ title, noPadding, className, children, ...rest }: Props) {
  return (
    <div className={clsx('bg-white rounded-xl border border-slate-100 shadow-sm', className)} {...rest}>
      {title && (
        <div className="px-6 py-4 border-b border-slate-100">
          <h3 className="text-base font-semibold text-slate-800">{title}</h3>
        </div>
      )}
      <div className={noPadding ? '' : 'p-6'}>{children}</div>
    </div>
  )
}
