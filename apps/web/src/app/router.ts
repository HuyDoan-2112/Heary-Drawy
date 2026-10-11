/** Client-side navigation shared by links (intercepted in App) and code paths such as hold gestures. */
export function navigate(path: string): void {
  window.history.pushState({}, '', path);
  window.dispatchEvent(new PopStateEvent('popstate'));
}
