import {useRef} from 'react';
import {Player} from '@remotion/player';
import {OpeningArchitectureV2} from './OpeningArchitectureV2.jsx';

const playerStyle = {
  background: '#F5F7F4',
  height: '100%',
  width: '100%',
};

export const PlayerPreview = () => {
  const playerRef = useRef(null);

  return (
    <>
      <style>{`
        :root {
          color-scheme: light;
          font-family: Geist, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          background: #f5f7f4;
          color: #163c2c;
        }
        * { box-sizing: border-box; }
        body { margin: 0; min-width: 320px; background: #f5f7f4; }
        .preview-shell { width: min(1160px, calc(100% - 32px)); margin: 0 auto; padding: 24px 0 32px; }
        .preview-bar { display: flex; align-items: center; justify-content: space-between; gap: 20px; margin: 0 0 18px; }
        .brand { display: inline-flex; align-items: center; gap: 10px; font-size: 16px; font-weight: 760; letter-spacing: -0.035em; }
        .mark { display: grid; grid-template-columns: repeat(2, 4px); gap: 3px; place-content: center; width: 30px; height: 30px; border-radius: 9px; background: #163c2c; }
        .mark i { width: 4px; height: 4px; border-radius: 50%; background: #92e0bd; }
        .meta { color: #60716a; font-size: 12px; font-weight: 720; letter-spacing: .08em; text-transform: uppercase; }
        .player-card { overflow: hidden; border: 1px solid #cfe0d6; border-radius: 22px; background: #fff; box-shadow: 0 24px 64px rgba(21,69,51,.12); }
        .player-frame { position: relative; aspect-ratio: 16 / 9; overflow: hidden; background: #f5f7f4; }
        .export:focus-visible { outline: 3px solid rgba(16,156,112,.42); outline-offset: -5px; }
        .footer { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 16px 20px 18px; }
        .detail { color: #60716a; font-size: 13px; font-weight: 620; }
        .export { display: inline-flex; align-items: center; gap: 8px; border: 1px solid #b7d9c8; border-radius: 10px; color: #0e573d; padding: 9px 12px; font-size: 13px; font-weight: 740; text-decoration: none; }
        .export:hover { background: #eff9f3; }
        @media (max-width: 640px) {
          .preview-shell { width: min(100% - 20px, 1160px); padding-top: 12px; }
          .preview-bar { margin-bottom: 12px; }
          .meta { font-size: 10px; }
          .player-card { border-radius: 16px; }
          .footer { align-items: flex-start; flex-direction: column; padding: 14px; }
          .export { width: 100%; justify-content: center; }
        }
      `}</style>
      <main className="preview-shell">
        <header className="preview-bar">
          <div className="brand" aria-label="LogisticPilot">
            <span className="mark" aria-hidden="true"><i></i><i></i><i></i><i></i></span>
            <span>LogisticPilot</span>
          </div>
          <span className="meta">Architecture</span>
        </header>
        <section className="player-card" aria-label="Interactive opening and architecture preview">
          <div className="player-frame">
            <Player
              ref={playerRef}
              component={OpeningArchitectureV2}
              durationInFrames={1410}
              compositionWidth={1920}
              compositionHeight={1080}
              fps={30}
              controls
              showVolumeControls
              allowFullscreen
              clickToPlay
              autoPlay={false}
              initialFrame={1}
              initiallyMuted={false}
              initiallyShowControls
              alwaysShowControls
              showPosterWhenUnplayed={false}
              showPosterWhenPaused={false}
              showPosterWhenEnded={false}
              style={playerStyle}
            />
          </div>
          <div className="footer">
            <span className="detail">47 sec · interactive Remotion composition · audio on</span>
            <a className="export" href="./opening-architecture.mp4" download>Download current MP4 ↗</a>
          </div>
        </section>
      </main>
    </>
  );
};
