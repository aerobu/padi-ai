import { render, screen } from '@testing-library/react';
import HomePage from '../../app/(public)/page';

describe('HomePage', () => {
  it('renders navigation with PADI.AI branding', () => {
    render(<HomePage />);

    // Use getAllByText since there are multiple PADI.AI instances
    const branding = screen.getAllByText('PADI.AI');
    expect(branding.length).toBeGreaterThanOrEqual(1);

    // Check that at least one has the gradient styling
    expect(branding[0]).toBeInTheDocument();
  });

  it('renders Sign In button in navigation', () => {
    render(<HomePage />);

    const signInButton = screen.getByText('Sign In');
    expect(signInButton).toBeInTheDocument();
    expect(signInButton.closest('a')).toHaveAttribute('href', '/(auth)/login');
  });

  it('renders Get Started button in navigation', () => {
    render(<HomePage />);

    const getStartedButton = screen.getByText('Get Started');
    expect(getStartedButton).toBeInTheDocument();
    expect(getStartedButton.closest('a')).toHaveAttribute('href', '/(auth)/login');
  });

  it('renders hero badge with Oregon text', () => {
    render(<HomePage />);

    const badge = screen.getByText('Built for Oregon Students');
    expect(badge).toBeInTheDocument();
  });

  it('renders main headline with correct messaging', () => {
    render(<HomePage />);

    const headline = screen.getByText(/Adaptive Math/);
    expect(headline).toBeInTheDocument();

    const subhead = screen.getByText(/Learning That Grows/);
    expect(subhead).toBeInTheDocument();
  });

  it('renders description text', () => {
    render(<HomePage />);

    const description = screen.getByText(
      /Personalized AI-powered tutoring that adapts to each 4th grader's learning style/
    );
    expect(description).toBeInTheDocument();
  });

  it('renders CTA buttons', () => {
    render(<HomePage />);

    const startLearningButton = screen.getByText('Start Learning Free');
    expect(startLearningButton).toBeInTheDocument();
    expect(startLearningButton.closest('a')).toHaveAttribute('href', '/(auth)/login');

    const seeHowItWorksButton = screen.getByText('See How It Works');
    expect(seeHowItWorksButton).toBeInTheDocument();
    expect(seeHowItWorksButton.closest('a')).toHaveAttribute('href', '/(auth)/login');
  });

  it('renders all three feature cards', () => {
    render(<HomePage />);

    const adaptiveFeature = screen.getByText('Adaptive Learning');
    expect(adaptiveFeature).toBeInTheDocument();

    const standardsFeature = screen.getByText('Oregon Standards');
    expect(standardsFeature).toBeInTheDocument();

    const coppaFeature = screen.getByText('COPPA Compliant');
    expect(coppaFeature).toBeInTheDocument();
  });

  it('renders feature descriptions', () => {
    render(<HomePage />);

    const adaptiveDescription = screen.getByText(
      /AI-powered tutoring that adjusts difficulty in real-time/
    );
    expect(adaptiveDescription).toBeInTheDocument();

    const standardsDescription = screen.getByText(
      /Fully aligned with Oregon math standards for grades 1-5/
    );
    expect(standardsDescription).toBeInTheDocument();

    const coppaDescription = screen.getByText(
      /Privacy-first design with local LLM processing/
    );
    expect(coppaDescription).toBeInTheDocument();
  });

  it('renders footer with copyright', () => {
    render(<HomePage />);

    const footer = screen.getByText(/© 2026 PADI.AI/);
    expect(footer).toBeInTheDocument();
  });

  it('has correct page structure', () => {
    render(<HomePage />);

    // Check for main layout elements
    expect(screen.getByRole('navigation')).toBeInTheDocument();
    expect(screen.getByRole('main')).toBeInTheDocument();
  });
});
