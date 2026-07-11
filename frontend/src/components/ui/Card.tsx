import { clsx } from 'clsx'

interface Props extends React.HTMLAttributes<HTMLDivElement> {
  title?: string
  noPadding?: boolean
}

export default function Card({ title, noPadding, className, children, ...rest }: Props) {
  return (
    <div
      className={clsx(
        'bg-white rounded-[12px] border border-[#e1e5e8]',
        'shadow-[0_1px_3px_0_rgba(0,30,43,0.08)] hover:shadow-[0_4px_12px_0_rgba(0,30,43,0.12)]',
        'transition-shadow duration-200',
        className,
      )}
      {...rest}
    >
      {title && (
        <div className="px-6 py-4 border-b border-[#e1e5e8]">
          <h3 className="text-base font-semibold text-[#001e2b]">{title}</h3>
        </div>
      )}
      <div className={noPadding ? '' : 'p-6'}>{children}</div>
    </div>
  )
}
