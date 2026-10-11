export function App() {
  return (
    <main className="app-shell" aria-labelledby="app-title">
      <section className="hero-card">
        <p className="eyebrow">Fixture foundation</p>
        <h1 id="app-title">Heary Drawy</h1>
        <p>
          The web shell is ready for contract-backed fixtures. Real rooms, voice, drawing relay,
          object delivery, and AI feedback are not implemented yet.
        </p>
        <p className="status-pill" aria-label="Backend health check route is served by the API">
          API health lives at http://127.0.0.1:8000/health
        </p>
      </section>
    </main>
  );
}
