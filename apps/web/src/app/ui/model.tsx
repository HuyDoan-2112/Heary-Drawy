import type { DetailedHTMLProps, HTMLAttributes } from 'react';
import { useEffect, useRef, useState } from 'react';
import { loadModelViewer } from './modelViewer';

declare module 'react' {
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace JSX {
    interface IntrinsicElements {
      'model-viewer': DetailedHTMLProps<HTMLAttributes<HTMLElement>, HTMLElement> & {
        class?: string;
        src: string;
        poster?: string;
        alt: string;
        'camera-controls'?: boolean;
        'camera-orbit'?: string;
        'touch-action'?: string;
        'auto-rotate'?: boolean;
        'auto-rotate-delay'?: number;
        'rotation-per-second'?: string;
        'interaction-prompt'?: string;
        'disable-pan'?: boolean;
      };
    }
  }
}

/**
 * The secret object as a 3D model to spin and pinch-zoom: the Speaker's during the round, both
 * players' from Reveal. The picture shows while the 3D library and model load, and stays if
 * either fails.
 */
export function SecretModel({ modelSrc, pictureSrc, label }: { modelSrc: string | null; pictureSrc: string | null; label: string }) {
  const [viewerReady, setViewerReady] = useState(false);
  const [failed, setFailed] = useState(false);
  const viewerRef = useRef<HTMLElement>(null);

  useEffect(() => {
    let live = true;
    loadModelViewer()
      .then(() => live && setViewerReady(true))
      .catch(() => live && setFailed(true));
    return () => {
      live = false;
    };
  }, []);

  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer) return undefined;
    const onError = () => setFailed(true);
    viewer.addEventListener('error', onError);
    return () => viewer.removeEventListener('error', onError);
  }, [viewerReady, modelSrc]);

  if (!modelSrc || !viewerReady || failed) {
    return pictureSrc ? <img className="secret-picture" src={pictureSrc} alt={label} /> : null;
  }
  return (
    <model-viewer
      ref={viewerRef}
      class="secret-model"
      src={modelSrc}
      poster={pictureSrc ?? undefined}
      alt={label}
      camera-controls
      camera-orbit="30deg 70deg auto"
      touch-action="none"
      auto-rotate
      auto-rotate-delay={2500}
      rotation-per-second="24deg"
      interaction-prompt="none"
      disable-pan
    />
  );
}
