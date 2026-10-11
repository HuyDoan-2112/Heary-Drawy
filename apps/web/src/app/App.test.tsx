import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { App } from './App';

function renderAt(path: string) {
  window.history.pushState({}, '', path);
  return render(<App />);
}

afterEach(() => {
  vi.unstubAllGlobals();
  window.sessionStorage.clear();
});

describe('fixture frontend routes', () => {
  it('renders the pick character screen first', () => {
    renderAt('/join');

    expect(screen.getByRole('heading', { name: 'Pick your character' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Mango/ })).toBeInTheDocument();
    expect(screen.getByText(/Fixture UI only/)).toBeInTheDocument();
  });

  it('joins a private room using the selected nickname, avatar, and shape code', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({
      room_id: 'room-test', player_id: 'player-test', guest_session_token: 'test-token', admission_status: 'admitted',
      expires_at: '2030-01-01T00:00:00Z',
    }) });
    vi.stubGlobal('fetch', fetchMock);
    const user = userEvent.setup();
    renderAt('/join');
    await user.clear(screen.getByRole('textbox', { name: 'My name' }));
    await user.type(screen.getByRole('textbox', { name: 'My name' }), 'Sam');
    await user.click(screen.getByRole('button', { name: 'Berry' }));
    await user.click(screen.getByRole('button', { name: 'Join room' }));

    expect(fetchMock).toHaveBeenCalledWith('/api/v1/rooms/join', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({ nickname: 'Sam', avatar_id: 'berry', shape_code: ['circle', 'triangle', 'square'] }),
    }));
    expect(await screen.findByText(/Joined the room/)).toBeInTheDocument();
    expect(window.sessionStorage.getItem('heary_guest_session')).toContain('test-token');
    fetchMock.mockResolvedValueOnce({ ok: true, json: async () => ({
      session_player_id: 'player-test', room: { teammate: { nickname: 'Kiwi' } },
      round: { role: 'drawer' },
    }) });
    await user.click(screen.getByRole('button', { name: 'Check teammate' }));
    expect(await screen.findByText(/You are the drawer. Your teammate is Kiwi/)).toBeInTheDocument();
    expect(fetchMock).toHaveBeenLastCalledWith('/api/v1/rooms/room-test/state', {
      headers: { Authorization: 'Bearer test-token' },
    });
  });

  it('shows friendly duplicate nickname errors without saving a token', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, json: async () => ({
      error: { code: 'nickname_taken', message: 'Internal details', retryable: true },
    }) }));
    renderAt('/join');
    await userEvent.setup().click(screen.getByRole('button', { name: 'Join room' }));
    expect(await screen.findByText('That name is already taken here. Try another one!')).toBeInTheDocument();
    expect(window.sessionStorage.getItem('heary_guest_session')).toBeNull();
  });

  it('navigates through UI-03 to UI-09 without a full page load', async () => {
    const user = userEvent.setup();
    renderAt('/join');

    await user.click(screen.getByRole('link', { name: 'Next' }));
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
