import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { App } from './App';

describe('App foundation shell', () => {
  it('renders an honest non-playable shell', () => {
    render(<App />);

    expect(screen.getByRole('heading', { name: 'Heary Drawy' })).toBeInTheDocument();
    expect(screen.getByText(/Real rooms, voice, drawing relay/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Backend health check/)).toHaveTextContent('http://127.0.0.1:8000/health');
  });
});
