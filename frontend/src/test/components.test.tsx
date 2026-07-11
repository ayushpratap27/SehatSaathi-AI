import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import NotFoundPage from '../pages/NotFoundPage'
import StatusBadge from '../components/ui/StatusBadge'
import LoadingSpinner from '../components/ui/LoadingSpinner'

describe('NotFoundPage', () => {
  it('renders 404 heading', () => {
    render(<MemoryRouter><NotFoundPage /></MemoryRouter>)
    expect(screen.getByText('404')).toBeInTheDocument()
    expect(screen.getByText('Page not found')).toBeInTheDocument()
  })
})

describe('StatusBadge', () => {
  it('renders Normal status with correct class', () => {
    const { container } = render(<StatusBadge status="Normal" />)
    expect(container.firstChild).toHaveClass('badge-normal')
  })
  it('renders Critical Low status', () => {
    render(<StatusBadge status="Critical Low" />)
    expect(screen.getByText('Critical Low')).toBeInTheDocument()
  })
})

describe('LoadingSpinner', () => {
  it('renders with role=status', () => {
    render(<LoadingSpinner />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })
})
