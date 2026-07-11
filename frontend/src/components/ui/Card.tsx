import { clsx } from 'clsx'

interface Props extends React.HTMLAttributes<HTMLDivElement> {
  title?: string
  noPadding?: boolean
}

export default function Card({ title, noPadding, className, children, ...rest }: Props) {
  return (
    <div
      className={clsx(
        'bg-white rounded-[18px] border border-[#E5E7EB]',
        'shadow-[0_8px_30px_rgba(15,23,42,.05)] hover:shadow-[0_16px_40px_rgba(15,23,42,.08)] hover:-translate-y-0.5',
        'transition-all duration-[250ms] ease',
        className,
      )}
      {...rest}
    >
      {title && (
        <div className="px-8 border-b border-[#E5E7EB]" style={{ height: '72px', display: 'flex', alignItems: 'center' }}>
          <h3 className="font-bold text-[#0F172A]" style={{ fontSize: '22px' }}>{title}</h3>
        </div>
      )}
      <div className={noPadding ? '' : 'p-8'}>{children}</div>
    </div>
  )
}
