import { render, screen, fireEvent } from '@testing-library/react'
import UpgradePrompt from '@/components/UpgradePrompt'

// Mock Next.js Link component
jest.mock('next/link', () => {
  return function MockLink({ children, href }: { children: React.ReactNode; href: string }) {
    return <a href={href}>{children}</a>
  }
})

describe('UpgradePrompt', () => {
  const defaultProps = {
    title: 'Test Title',
    message: 'Test message for upgrade',
  }

  it('renders with title and message', () => {
    render(<UpgradePrompt {...defaultProps} />)
    
    expect(screen.getByText('Test Title')).toBeInTheDocument()
    expect(screen.getByText('Test message for upgrade')).toBeInTheDocument()
  })

  it('shows upgrade button with correct link', () => {
    render(<UpgradePrompt {...defaultProps} />)
    
    const upgradeButton = screen.getByRole('link', { name: /upgrade now/i })
    expect(upgradeButton).toHaveAttribute('href', '/dashboard/subscription')
  })

  it('shows view plans link', () => {
    render(<UpgradePrompt {...defaultProps} />)
    
    const viewPlansLink = screen.getByRole('link', { name: /view plans/i })
    expect(viewPlansLink).toHaveAttribute('href', '/dashboard/subscription')
  })

  it('can be dismissed when dismissible', () => {
    const onDismiss = jest.fn()
    render(<UpgradePrompt {...defaultProps} onDismiss={onDismiss} dismissible={true} />)
    
    const dismissButton = screen.getByRole('button')
    fireEvent.click(dismissButton)
    
    expect(onDismiss).toHaveBeenCalledTimes(1)
  })

  it('does not show dismiss button when not dismissible', () => {
    render(<UpgradePrompt {...defaultProps} dismissible={false} />)
    
    const dismissButton = screen.queryByRole('button')
    expect(dismissButton).not.toBeInTheDocument()
  })

  it('hides after being dismissed', () => {
    render(<UpgradePrompt {...defaultProps} dismissible={true} />)
    
    const dismissButton = screen.getByRole('button')
    fireEvent.click(dismissButton)
    
    expect(screen.queryByText('Test Title')).not.toBeInTheDocument()
  })
})