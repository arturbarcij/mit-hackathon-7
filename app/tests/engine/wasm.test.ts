import { gzipSync } from 'node:zlib';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { fetchWasmBinary } from '../../src/engine/model';

const WASM_MAGIC = [0x00, 0x61, 0x73, 0x6d];
const sample = new Uint8Array([...WASM_MAGIC, 1, 0, 0, 0, ...Array.from({ length: 500 }, (_, i) => i % 7)]);

function serve(body: Uint8Array, status = 200) {
  vi.stubGlobal('fetch', vi.fn(async () => new Response(body as BlobPart, { status })));
}

afterEach(() => vi.unstubAllGlobals());

describe('fetchWasmBinary', () => {
  it('inflates the gzipped runtime', async () => {
    serve(new Uint8Array(gzipSync(sample)));
    expect(Array.from(await fetchWasmBinary('http://x/ort.wasm.gz'))).toEqual(Array.from(sample));
  });

  it('uses the bytes as they are when a host already unpacked them', async () => {
    serve(sample);
    expect(Array.from(await fetchWasmBinary('http://x/ort.wasm.gz'))).toEqual(Array.from(sample));
  });

  it('fails loudly on a download error', async () => {
    serve(new Uint8Array(), 404);
    await expect(fetchWasmBinary('http://x/ort.wasm.gz')).rejects.toThrow(/HTTP 404/);
  });
});
