import { Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Activity, Loader2 } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const schema = z.object({
  email:     z.string().email('Enter a valid email'),
  username:  z.string().min(3, 'At least 3 characters').max(50).regex(/^[a-zA-Z0-9_.-]+$/, 'Letters, digits, _ . - only'),
  full_name: z.string().max(255).optional(),
  password:  z.string().min(8, 'At least 8 characters')
    .regex(/[A-Z]/, 'Must contain an uppercase letter')
    .regex(/\d/,   'Must contain a digit'),
  confirm:   z.string(),
}).refine((d) => d.password === d.confirm, { message: 'Passwords do not match', path: ['confirm'] })

type Form = z.infer<typeof schema>

export default function RegisterPage() {
  const { register: authRegister } = useAuth()
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<Form>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async ({ confirm: _c, ...data }: Form) => {
    try { await authRegister(data) } catch { /* handled by interceptor */ }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-sky-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-green-600 flex items-center justify-center mx-auto mb-4 shadow-lg">
            <Activity className="w-9 h-9 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-slate-900">SehatSaathi-AI</h1>
          <p className="text-slate-500 mt-1 text-sm">Create your free account</p>
        </div>

        <div className="bg-white rounded-2xl shadow-md border border-slate-100 p-8">
          <h2 className="text-xl font-semibold text-slate-800 mb-6">Get started</h2>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {([
              { name: 'email',     label: 'Email', type: 'email',    placeholder: 'you@example.com' },
              { name: 'username',  label: 'Username', type: 'text',  placeholder: 'john_doe' },
              { name: 'full_name', label: 'Full name (optional)', type: 'text', placeholder: 'John Doe' },
              { name: 'password',  label: 'Password', type: 'password', placeholder: '••••••••' },
              { name: 'confirm',   label: 'Confirm password', type: 'password', placeholder: '••••••••' },
            ] as const).map(({ name, label, type, placeholder }) => (
              <div key={name}>
                <label className="block text-sm font-medium text-slate-700 mb-1">{label}</label>
                <input {...register(name)} type={type} placeholder={placeholder} className="input-field" />
                {errors[name] && <p className="mt-1 text-xs text-red-600">{errors[name]?.message}</p>}
              </div>
            ))}

            <button type="submit" disabled={isSubmitting} className="w-full btn-primary py-2.5 flex items-center justify-center gap-2 mt-2">
              {isSubmitting ? <><Loader2 className="w-4 h-4 animate-spin" />Creating account…</> : 'Create account'}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-500">
            Already have an account?{' '}
            <Link to="/login" className="text-green-600 hover:text-green-700 font-medium">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
