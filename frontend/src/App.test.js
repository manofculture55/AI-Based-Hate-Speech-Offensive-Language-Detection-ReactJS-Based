import { render, screen } from '@testing-library/react';
import App from './App';
import { ThemeProvider } from './components/ThemeContext';

// index.js wraps App in ThemeProvider, so Navbar's useContext(ThemeContext)
// only resolves inside it. Mirror that here.
const renderApp = () =>
  render(
    <ThemeProvider>
      <App />
    </ThemeProvider>
  );

// The CRA starter test looked for a "learn react" link that this app has
// never contained, so `npm test` failed on a clean checkout.

// The app calls the API on mount; stub fetch so the test doesn't hit network.
beforeEach(() => {
  jest.spyOn(global, 'fetch').mockImplementation(() =>
    Promise.resolve({
      ok: true,
      status: 200,
      headers: { get: () => 'application/json' },
      json: () => Promise.resolve({ data: [], words: [], pagination: {} }),
    })
  );
});

afterEach(() => {
  jest.restoreAllMocks();
});

// Home fetches on mount, so each test awaits a query to let those state
// updates settle inside act() rather than after the test has finished.

test('renders the app shell with primary navigation', async () => {
  renderApp();

  // /HateSpeech/i also matches the hero heading, so target the logo itself.
  expect(
    await screen.findByText('HateSpeech', { selector: '.logo-text' })
  ).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /history/i })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /analytics/i })).toBeInTheDocument();
});

test('renders the analyzer input on the home route', async () => {
  renderApp();

  expect(
    await screen.findByPlaceholderText(/enter text to analyze/i)
  ).toBeInTheDocument();
});
