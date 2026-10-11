import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { FakeWebSocket } from '../test/fakeWebSocket';
import { App } from './App';

function renderAt(path: string) {
  window.history.pushState({}, '', path);
  return render(<App />);
}

beforeEach(() => {
  FakeWebSocket.reset();
  vi.stubGlobal('WebSocket', FakeWebSocket);
});

afterEach(() => {
  vi.unstubAllGlobals();
  window.sessionStorage.clear();
});

describe('fixture frontend routes', () => {
  it('renders the pick character screen first', () => {
    renderAt('/join');

    expect(screen.getByRole('heading', { name: 'Pick your character' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Mango/ })).toBeInTheDocument();
    expect(screen.getByText(/No Room join flow is configured/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Join room' })).not.toBeInTheDocument();
  });

  it('resumes a stored guest session on load without joining again', async () => {
    window.sessionStorage.setItem('heary_guest_session', JSON.stringify({
      room_id: 'room-test', player_id: 'player-test', guest_session_token: 'test-token', expires_at: '2099-01-01T00:00:00Z',
    }));
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
    renderAt('/join');

    expect(await screen.findByText('Connecting to your room...')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Your team' })).toBeInTheDocument();
    expect(screen.queryByRole('textbox', { name: 'My name' })).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Choose one avatar')).not.toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('navigates through UI-03 to UI-09 without a full page load', async () => {
    const user = userEvent.setup();
    renderAt('/join');

    await user.click(screen.getByRole('link', { name: 'Preview screens' }));
    expect(screen.getByRole('heading', { name: 'Turn on your mic' })).toBeInTheDocument();

    await user.click(screen.getByRole('link', { name: 'I understand' }));
    expect(screen.getByRole('heading', { name: 'Pick a picture mode' })).toBeInTheDocument();

    await user.click(screen.getByRole('link', { name: /Normal/ }));
    expect(screen.getByRole('heading', { name: /You and Kiwi are a team/ })).toBeInTheDocument();

    await user.click(screen.getByRole('link', { name: "Let's play" }));
    expect(screen.getByRole('heading', { name: 'Tell Mango what you see' })).toBeInTheDocument();

    await user.click(screen.getByRole('link', { name: 'Start talking' }));
    expect(screen.getByLabelText('Authorized Speaker object placeholder')).toBeInTheDocument();

    await user.click(screen.getByRole('link', { name: 'Drawer' }));
    expect(screen.getByRole('heading', { name: 'Draw what you hear' })).toBeInTheDocument();
  });

  it('keeps the Drawer play screen secret blind before Reveal', () => {
    const { container } = renderAt('/play/drawer');

    expect(screen.getByRole('heading', { name: 'Draw what you hear' })).toBeInTheDocument();
    expect(container).not.toHaveTextContent('object_id');
    expect(container).not.toHaveTextContent('image_url');
    expect(container).not.toHaveTextContent('model_url');
    expect(container).not.toHaveTextContent('rubric');
    expect(container).not.toHaveTextContent('Secret picture slot');
  });

  it('shows Speaker drawing as read-only', () => {
    renderAt('/play/speaker');

    const preview = screen.getByLabelText('Read-only drawing preview');
    expect(preview).toHaveAttribute('data-readonly', 'true');
    expect(within(preview).getByText('Read-only live frame')).toBeInTheDocument();
  });

  it('shows the Checking screen as a disabled finalizing fixture', async () => {
    const user = userEvent.setup();
    renderAt('/play/drawer');

    await user.click(screen.getByRole('link', { name: 'Done!' }));

    expect(screen.getByRole('heading', { name: 'Drawy is checking' })).toBeInTheDocument();
    expect(screen.getByText(/Talking and drawing are paused/)).toBeInTheDocument();
    expect(screen.getByLabelText('Finalizing fixture state')).toHaveTextContent('No AI score is running');
  });

  it('shows a neutral Result and Discovery Reward fixture', () => {
    renderAt('/result');

    expect(screen.getByRole('heading', { name: 'You finished together!' })).toBeInTheDocument();
    expect(screen.getByText(/Drawy had trouble checking this one/)).toBeInTheDocument();
    expect(screen.getByLabelText('Discovery Reward fixture')).toHaveTextContent('Available every round');
    expect(screen.getByText('Drawy says')).toBeInTheDocument();
  });

  it('keeps the grown-ups area blocked behind a placeholder gate', async () => {
    const user = userEvent.setup();
    renderAt('/join');

    await user.click(screen.getByRole('link', { name: 'Grown-ups' }));

    expect(screen.getByRole('heading', { name: 'Grown-ups gate' })).toBeInTheDocument();
    expect(screen.getByText(/blocked until separate authorization/)).toBeInTheDocument();
    expect(screen.getByLabelText('Blocked grown-up access')).toHaveTextContent('No parent metrics');
  });
});
