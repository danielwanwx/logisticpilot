import {build} from 'esbuild';
import {copyFile, mkdir, stat, writeFile} from 'node:fs/promises';
import {dirname, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const scriptDirectory = dirname(fileURLToPath(import.meta.url));
const projectDirectory = resolve(scriptDirectory, '..');
const outputDirectory = resolve(
  process.env.REMOTION_PLAYER_OUTPUT || '/Users/danielwan/Documents/LogisticPilot-media/remotion-player',
);
const mediaDirectory = dirname(outputDirectory);
const mp4Source = resolve(
  process.env.REMOTION_PLAYER_MP4 || '/Users/danielwan/Documents/LogisticPilot-media/opening-architecture-v3.mp4',
);
const posterSource = resolve(
  process.env.REMOTION_PLAYER_POSTER || '/Users/danielwan/Documents/LogisticPilot-media/opening-architecture-v3-poster.jpg',
);

const assertFile = async (path) => {
  const details = await stat(path);
  if (!details.isFile()) throw new Error('Expected a file: ' + path);
};

await Promise.all([
  assertFile(mp4Source),
  assertFile(posterSource),
  assertFile(resolve(projectDirectory, 'public/narration-v2.mp3')),
  assertFile(resolve(projectDirectory, 'public/geist-latin.woff2')),
]);

await mkdir(resolve(outputDirectory, 'assets'), {recursive: true});

await build({
  bundle: true,
  define: {'process.env.NODE_ENV': '"production"'},
  entryPoints: [resolve(projectDirectory, 'src/player-preview-entry.jsx')],
  format: 'esm',
  jsx: 'automatic',
  minify: true,
  outfile: resolve(outputDirectory, 'assets/player-preview.js'),
  platform: 'browser',
  target: ['es2022'],
});

await Promise.all([
  copyFile(resolve(projectDirectory, 'player-preview.html'), resolve(outputDirectory, 'index.html')),
  copyFile(resolve(projectDirectory, 'opening-preview.html'), resolve(mediaDirectory, 'opening-preview.html')),
  copyFile(resolve(projectDirectory, 'public/narration-v2.mp3'), resolve(outputDirectory, 'narration-v2.mp3')),
  copyFile(resolve(projectDirectory, 'public/geist-latin.woff2'), resolve(outputDirectory, 'geist-latin.woff2')),
  copyFile(mp4Source, resolve(outputDirectory, 'opening-architecture.mp4')),
  copyFile(posterSource, resolve(outputDirectory, 'opening-architecture-poster.jpg')),
]);

const manifest = {
  composition: 'OpeningArchitectureV2',
  durationInFrames: 1410,
  fps: 30,
  audio: 'narration-v2.mp3',
  exportFile: 'opening-architecture.mp4',
  poster: 'opening-architecture-poster.jpg',
  sourceExport: mp4Source,
  sourcePoster: posterSource,
};
await writeFile(resolve(outputDirectory, 'preview-manifest.json'), JSON.stringify(manifest, null, 2) + '\n');

console.log('Built Remotion Player preview at ' + outputDirectory);
