import { useEffect } from 'react';
import { useEngine, type EngineState } from '../hooks/useEngine';

/**
 * Loads the model and reports its state (for the mock badge). App mounts this only once the
 * service worker has finished caching (or is not available), so on a first visit the model and
 * the onnxruntime wasm are downloaded once, by the service worker, not twice.
 */
export function EngineProbe({ onState }: { onState: (s: EngineState) => void }) {
  const state = useEngine();
  useEffect(() => onState(state), [state, onState]);
  return null;
}
