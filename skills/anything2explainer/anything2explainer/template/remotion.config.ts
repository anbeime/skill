import {Config} from '@remotion/cli/config';

// Linux / ARM (e.g. Raspberry Pi) support.
// Chrome-for-Testing has no linux-arm64 build, so Remotion can't download a browser there.
// Point it at a system Chromium via env, e.g.:
//   export REMOTION_BROWSER_EXECUTABLE=/usr/bin/chromium
// On a GPU-less headless box also set software GL (default 'swangle'); override with REMOTION_GL.
// Both are unset on macOS / x86 → this file is a no-op and Remotion uses its own browser.
const GL_RENDERERS = ['swangle', 'angle', 'egl', 'swiftshader', 'vulkan', 'angle-egl'] as const;
type GlRenderer = (typeof GL_RENDERERS)[number];
const isGlRenderer = (v: string | undefined): v is GlRenderer => (GL_RENDERERS as readonly string[]).includes(v ?? '');

const browser = process.env.REMOTION_BROWSER_EXECUTABLE;
if (browser) {
  Config.setBrowserExecutable(browser);
  const gl = process.env.REMOTION_GL;
  if (gl && !isGlRenderer(gl)) {
    throw new Error(`REMOTION_GL=${gl} is not a valid renderer; use one of: ${GL_RENDERERS.join(' / ')}`);
  }
  Config.setChromiumOpenGlRenderer(isGlRenderer(gl) ? gl : 'swangle');
}
