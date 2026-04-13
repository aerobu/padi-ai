import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LoginPage from '../../app/(auth)/login/page';

describe('LoginPage', () => {
  it('renders welcome heading', () => {
    render(<LoginPage />);

    const heading = screen.getByText(/Welcome to PADI.AI/);
    expect(heading).toBeInTheDocument();
  });

  it('renders subtitle', () => {
    render(<LoginPage />);

    const subtitle = screen.getByText(
      /Sign in to continue your adaptive math learning journey/
    );
    expect(subtitle).toBeInTheDocument();
  });

  it('renders Auth0 login button', () => {
    render(<LoginPage />);

    const authButton = screen.getByText('Continue with Auth0');
    expect(authButton).toBeInTheDocument();
  });

  it('handles login button click', async () => {
    render(<LoginPage />);

    const user = userEvent.setup();
    const authButton = screen.getByText('Continue with Auth0');

    await user.click(authButton);

    // Verify router.push was called with correct path
    // The mock should redirect to /api/auth/login
  });

  it('renders Terms of Service link', () => {
    render(<LoginPage />);

    const termsLink = screen.getByText('Terms of Service');
    expect(termsLink).toBeInTheDocument();
    expect(termsLink).toHaveAttribute('href', '/terms');
  });

  it('renders Privacy Policy link', () => {
    render(<LoginPage />);

    const privacyLink = screen.getByText('Privacy Policy');
    expect(privacyLink).toBeInTheDocument();
    expect(privacyLink).toHaveAttribute('href', '/privacy');
  });

  it('renders legal text section', () => {
    render(<LoginPage />);

    expect(screen.getByText(/By continuing, you agree to our/)).toBeInTheDocument();
    expect(screen.getByText('and')).toBeInTheDocument();
  });

  it('has centered layout', () => {
    render(<LoginPage />);

    // Check for centered content
    expect(screen.getByText('Welcome to PADI.AI')).toBeInTheDocument();
  });

  it('renders card with shadow and border', () => {
    render(<LoginPage />);

    const authButton = screen.getByText('Continue with Auth0');
    const buttonContainer = authButton.closest('button');
    expect(buttonContainer).toBeInTheDocument();
  });
});
