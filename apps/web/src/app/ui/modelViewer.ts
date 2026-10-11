let library: Promise<unknown> | null = null;

/**
 * Loads the 3D viewer library (model-viewer + three.js, its own lazy chunk) once per page. It holds
 * no secret, so every device starts it during the round and the Reveal shows the model without a
 * multi-second download. A failed load is forgotten so the next call tries again.
 */
export function loadModelViewer(): Promise<unknown> {
  library ??= import('@google/model-viewer').catch((error: unknown) => {
    library = null;
    throw error;
  });
  return library;
}
