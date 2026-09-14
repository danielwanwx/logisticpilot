import {
  AbsoluteFill,
  Audio,
  Easing,
  interpolate,
  interpolateColors,
  spring,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import {ArchitectureDiagram} from './ArchitecturePreview.jsx';

const palette = {
  canvas: '#F5F7F4',
  paper: '#FFFFFF',
  ink: '#163C2C',
  muted: '#64756D',
  line: '#D7E2DB',
  emerald: '#159D72',
  emeraldDark: '#087455',
  emeraldSoft: '#DCF4EA',
  amber: '#C97827',
  amberSoft: '#FFF0D8',
  shadow: '0 18px 44px rgba(22, 60, 44, 0.10)',
};

const timeline = {
  intro: {from: 0, to: 274},
  question: {from: 274, to: 417},
  promise: {from: 417, to: 655},
  handoff: {from: 655, to: 693},
  architecture: {from: 693, to: 1205},
  goal: {from: 1171, to: 1410},
};

const bounded = (value, min, max) => Math.min(Math.max(value, min), max);

const progress = (frame, start, end) =>
  interpolate(frame, [start, end], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

const sceneOpacity = (frame, from, to, enter = 16, exit = 18) => {
  const exitOpacity = exit > 0 ? 1 - progress(frame, to - exit, to) : 1;
  return bounded(progress(frame, from, from + enter) * exitOpacity, 0, 1);
};

const springIn = (frame, start, duration = 24) => {
  if (frame <= start) return 0;
  return bounded(
    spring({
      frame: frame - start,
      fps: 30,
      durationInFrames: duration,
      config: {damping: 18, mass: 0.7, stiffness: 120},
    }),
    0,
    1,
  );
};

const Eyebrow = ({children}) => (
  <div
    style={{
      color: palette.emeraldDark,
      fontSize: 14,
      fontWeight: 750,
      letterSpacing: '0.13em',
      textTransform: 'uppercase',
    }}
  >
    {children}
  </div>
);

const ResponsibilityCard = ({label, symbol, style = {}}) => (
  <div
    style={{
      alignItems: 'center',
      background: '#F7FCF9',
      border: '1px solid #B6E4CD',
      borderRadius: 17,
      boxShadow: '0 12px 26px rgba(4, 54, 36, 0.16)',
      color: palette.ink,
      display: 'flex',
      gap: 12,
      height: 94,
      padding: '0 18px',
      position: 'absolute',
      width: 206,
      ...style,
    }}
  >
    <span
      style={{
        alignItems: 'center',
        background: '#D9F6E8',
        borderRadius: 11,
        color: palette.emeraldDark,
        display: 'flex',
        fontSize: 24,
        height: 38,
        justifyContent: 'center',
        width: 38,
      }}
    >
      {symbol}
    </span>
    <span style={{fontSize: 19, fontWeight: 680, letterSpacing: '-0.03em'}}>{label}</span>
  </div>
);

const OperatorScene = ({frame, opacity}) => {
  const operatorIn = springIn(frame, 12, 30);
  const roles = [
    {label: 'Receiving', symbol: '↓', start: {x: 100, y: 652}, target: {x: 628, y: 650}},
    {label: 'Inspection', symbol: '○', start: {x: 857, y: 260}, target: {x: 857, y: 650}},
    {label: 'Customer orders', symbol: '→', start: {x: 1614, y: 652}, target: {x: 1086, y: 650}},
  ];
  const operator = {x: 600, y: 470, width: 720, height: 355};

  return (
    <AbsoluteFill style={{opacity, pointerEvents: 'none'}}>
      <div style={{left: 180, position: 'absolute', right: 180, textAlign: 'center', top: 200}}>
        <Eyebrow>Built for the receiving desk</Eyebrow>
        <h1 style={{fontSize: 78, fontWeight: 630, letterSpacing: '-0.065em', lineHeight: 0.98, margin: '22px 0 0'}}>
          Built for small businesses
        </h1>
      </div>

      <div
        style={{
          background: 'linear-gradient(145deg, #0E4D37 0%, #126647 100%)',
          border: '1px solid rgba(185, 239, 211, 0.4)',
          borderRadius: 30,
          boxShadow: '0 24px 56px rgba(9, 67, 45, 0.22)',
          height: operator.height,
          left: operator.x,
          opacity: operatorIn,
          position: 'absolute',
          top: operator.y,
          transform: 'translateY(' + interpolate(operatorIn, [0, 1], [24, 0]) + 'px) scale(' + interpolate(operatorIn, [0, 1], [0.96, 1]) + ')',
          width: operator.width,
        }}
      >
        <div style={{alignItems: 'center', display: 'flex', gap: 18, left: 38, position: 'absolute', top: 34}}>
          <div
            style={{
              alignItems: 'center',
              background: '#18AC79',
              border: '6px solid rgba(207, 249, 227, 0.28)',
              borderRadius: '50%',
              color: '#FFFFFF',
              display: 'flex',
              fontSize: 30,
              height: 68,
              justifyContent: 'center',
              width: 68,
            }}
          >
            ●
          </div>
          <div>
            <div style={{color: '#A8E8C9', fontSize: 13, fontWeight: 760, letterSpacing: '0.14em'}}>THE OPERATOR</div>
            <div style={{color: '#FFFFFF', fontSize: 32, fontWeight: 680, letterSpacing: '-0.04em', marginTop: 7}}>One person handles all three</div>
          </div>
        </div>
      </div>

      {roles.map(({label, symbol, start, target}, index) => {
        const roleProgress = springIn(frame, 28 + index * 54, 32);
        const x = interpolate(roleProgress, [0, 1], [start.x, target.x]);
        const y = interpolate(roleProgress, [0, 1], [start.y, target.y]);

        return (
          <ResponsibilityCard key={label} label={label} symbol={symbol} style={{left: x, opacity: roleProgress, top: y}} />
        );
      })}
    </AbsoluteFill>
  );
};

const ExceptionScene = ({frame, opacity}) => {
  const separation = springIn(frame, 316, 36);
  const gridX = 850;
  const gridY = 585;
  const tileWidth = 36;
  const tileHeight = 28;
  const gap = 10;
  const eligibleX = 585;
  const inspectionX = 1245;

  return (
    <AbsoluteFill style={{opacity, pointerEvents: 'none'}}>
      <div style={{left: 130, position: 'absolute', right: 130, textAlign: 'center', top: 196}}>
        <Eyebrow>One receiving exception</Eyebrow>
        <h2 style={{fontSize: 64, fontWeight: 625, letterSpacing: '-0.06em', lineHeight: 1, margin: '24px 0 0'}}>
          When five parts look questionable,
          <br />
          should all twenty-five have to wait?
        </h2>
      </div>

      <div style={{left: 560, opacity: separation, position: 'absolute', textAlign: 'center', top: 500, width: 270}}>
        <div style={{color: palette.emeraldDark, fontSize: 16, fontWeight: 760, letterSpacing: '0.11em'}}>20 ELIGIBLE</div>
        <div style={{background: palette.emeraldSoft, borderRadius: 999, height: 5, margin: '12px auto 0', width: 92}} />
      </div>
      <div style={{left: 1195, opacity: separation, position: 'absolute', textAlign: 'center', top: 500, width: 180}}>
        <div style={{color: palette.amber, fontSize: 16, fontWeight: 760, letterSpacing: '0.11em'}}>5 INSPECTION</div>
        <div style={{background: palette.amberSoft, borderRadius: 999, height: 5, margin: '12px auto 0', width: 92}} />
      </div>

      {Array.from({length: 25}, (_, index) => {
        const isInspection = index >= 20;
        const row = isInspection ? index - 20 : Math.floor(index / 4);
        const col = isInspection ? 0 : index % 4;
        const neutralRow = Math.floor(index / 5);
        const neutralCol = index % 5;
        const targetX = (isInspection ? inspectionX : eligibleX) + col * (tileWidth + gap);
        const targetY = 565 + row * (tileHeight + gap);
        const initialX = gridX + neutralCol * (tileWidth + gap);
        const initialY = gridY + neutralRow * (tileHeight + gap);
        const x = interpolate(separation, [0, 1], [initialX, targetX]);
        const y = interpolate(separation, [0, 1], [initialY, targetY]);
        const base = isInspection ? palette.amberSoft : palette.emeraldSoft;
        const border = isInspection ? '#E7C18B' : '#A9DEC7';

        return (
          <div
            key={index}
            style={{
              background: interpolateColors(separation, [0, 1], ['#FFFFFF', base]),
              border: '1px solid ' + interpolateColors(separation, [0, 1], [palette.line, border]),
              borderRadius: 8,
              height: tileHeight,
              left: x,
              opacity: interpolate(separation, [0, 1], [0.76, 1]),
              position: 'absolute',
              top: y,
              width: tileWidth,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

const EvidenceNode = ({active, icon, label, sublabel, style = {}}) => (
  <div
    style={{
      alignItems: 'center',
      background: palette.paper,
      border: '1px solid ' + (active ? palette.emerald : palette.line),
      borderRadius: 22,
      boxShadow: active ? '0 15px 34px rgba(21, 157, 114, 0.18)' : palette.shadow,
      display: 'flex',
      gap: 16,
      padding: '18px 22px',
      position: 'absolute',
      width: 270,
      ...style,
    }}
  >
    <span
      style={{
        alignItems: 'center',
        background: active ? palette.emeraldSoft : '#F0F5F1',
        borderRadius: 14,
        color: palette.emeraldDark,
        display: 'flex',
        fontSize: 27,
        height: 52,
        justifyContent: 'center',
        width: 52,
      }}
    >
      {icon}
    </span>
    <div>
      <div style={{color: palette.ink, fontSize: 21, fontWeight: 680, letterSpacing: '-0.03em'}}>{label}</div>
      <div style={{color: palette.muted, fontSize: 14, marginTop: 4}}>{sublabel}</div>
    </div>
  </div>
);

const EvidenceScene = ({frame, opacity}) => {
  const photoIn = springIn(frame, 438, 20);
  const agentIn = springIn(frame, 474, 20);
  const appsIn = springIn(frame, 510, 20);
  const stage = frame < 485 ? 0 : frame < 535 ? 1 : 2;
  const flowY = 570;
  const photoRight = 420;
  const agentLeft = 755;
  const agentRight = 1025;
  const spineX = 1250;
  const appsLeft = 1320;
  const packetStart = {x: photoRight, y: flowY};
  const agentPoint = {x: agentLeft, y: flowY};
  const hubPoint = {x: spineX, y: flowY};
  const appPoints = [507, 555, 603, 651];
  const appStart = 540;
  let packetX = packetStart.x;
  let packetY = packetStart.y;

  if (frame < 500) {
    const move = springIn(frame, 438, 50);
    packetX = interpolate(move, [0, 1], [packetStart.x, agentPoint.x]);
  } else if (frame < 560) {
    const move = springIn(frame, 500, 46);
    packetX = interpolate(move, [0, 1], [agentPoint.x, hubPoint.x]);
  } else {
    packetX = hubPoint.x;
    packetY = hubPoint.y;
  }

  const appNames = ['ERPNext', 'Airtable', 'Jira', 'Slack'];

  return (
    <AbsoluteFill style={{opacity, pointerEvents: 'none'}}>
      <div style={{left: 120, position: 'absolute', right: 120, textAlign: 'center', top: 184}}>
        <Eyebrow>One evidence packet</Eyebrow>
        <h2 style={{fontSize: 62, fontWeight: 625, letterSpacing: '-0.06em', lineHeight: 1, margin: '22px 0 0'}}>
          Upload a photo. Ask the agent what can move.
          <br />
          Verify the result in your apps.
        </h2>
      </div>

      <div style={{background: stage === 0 ? palette.emerald : palette.line, height: 3, left: photoRight, opacity: photoIn, position: 'absolute', top: flowY, width: agentLeft - photoRight}} />
      <div style={{background: stage >= 1 ? palette.emerald : palette.line, height: 3, left: agentRight, opacity: agentIn, position: 'absolute', top: flowY, width: spineX - agentRight}} />
      <div
        style={{
          background: stage === 2 ? palette.emerald : palette.line,
          height: appPoints[appPoints.length - 1] - appPoints[0],
          left: spineX,
          opacity: appsIn,
          position: 'absolute',
          top: appPoints[0],
          width: 3,
        }}
      />
      {appPoints.map((appY, index) => {
        const branchActive = stage === 2 && frame >= appStart + index * 18;
        return (
          <div
            key={appY}
            style={{
              background: branchActive ? palette.emerald : palette.line,
              height: 2,
              left: spineX,
              opacity: appsIn,
              position: 'absolute',
              top: appY,
              width: appsLeft - spineX,
            }}
          />
        );
      })}
      <div style={{background: stage === 2 ? palette.emerald : palette.line, borderRadius: 50, height: 13, left: spineX - 5, opacity: appsIn, position: 'absolute', top: hubPoint.y - 5, width: 13}} />

      <EvidenceNode active={stage === 0} icon="▧" label="Photo" sublabel="observations" style={{left: 150, opacity: photoIn, top: 525}} />
      <EvidenceNode active={stage === 1} icon="✦" label="Strands agent" sublabel="proposed next step" style={{left: agentLeft, opacity: agentIn, top: 525}} />
      <div style={{left: appsLeft, opacity: appsIn, position: 'absolute', top: 458, width: 350}}>
        <div style={{color: palette.muted, fontSize: 13, fontWeight: 760, letterSpacing: '0.12em', marginBottom: 12}}>CONNECTED APPS</div>
        {appNames.map((name, index) => (
          <div
            key={name}
            style={{
              alignItems: 'center',
              background: palette.paper,
              border: '1px solid ' + (stage === 2 && frame >= appStart + index * 18 ? palette.emerald : palette.line),
              borderRadius: 12,
              color: palette.ink,
              display: 'flex',
              fontSize: 17,
              fontWeight: 650,
              gap: 10,
              height: 40,
              marginBottom: 8,
              padding: '0 14px',
            }}
          >
            <span style={{background: stage === 2 && frame >= appStart + index * 18 ? palette.emerald : palette.line, borderRadius: 50, height: 8, width: 8}} />
            {name}
          </div>
        ))}
      </div>

      <div
        style={{
          alignItems: 'center',
          background: palette.emerald,
          borderRadius: 14,
          boxShadow: '0 10px 24px rgba(21, 157, 114, 0.25)',
          color: '#FFFFFF',
          display: 'flex',
          fontSize: 13,
          fontWeight: 760,
          height: 30,
          justifyContent: 'center',
          left: packetX - 43,
          letterSpacing: '0.04em',
          opacity: photoIn * agentIn * appsIn,
          position: 'absolute',
          top: packetY - 15,
          width: 86,
        }}
      >
        EVIDENCE
      </div>
    </AbsoluteFill>
  );
};

const Opening = ({frame}) => {
  const intro = sceneOpacity(frame, timeline.intro.from, timeline.intro.to);
  const question = sceneOpacity(frame, timeline.question.from, timeline.question.to);
  const promise = sceneOpacity(frame, timeline.promise.from, timeline.promise.to);
  const handoff = sceneOpacity(frame, timeline.handoff.from, timeline.handoff.to, 10, 12);

  return (
    <AbsoluteFill>
      <OperatorScene frame={frame} opacity={intro} />
      <ExceptionScene frame={frame} opacity={question} />
      <EvidenceScene frame={frame} opacity={promise} />

      <div
        style={{
          left: 180,
          opacity: handoff,
          position: 'absolute',
          right: 180,
          textAlign: 'center',
          top: 390,
          transform: 'translateY(' + interpolate(handoff, [0, 1], [18, 0]) + 'px)',
        }}
      >
        <Eyebrow>Evidence, judgment, confirmation</Eyebrow>
        <h2 style={{fontSize: 74, fontWeight: 625, letterSpacing: '-0.065em', lineHeight: 1, margin: '22px 0 0'}}>
          Here’s how I built it.
        </h2>
      </div>
    </AbsoluteFill>
  );
};

const Goal = ({frame}) => {
  const opacity = sceneOpacity(frame, timeline.goal.from, timeline.goal.to, 18, 0);
  const lift = interpolate(opacity, [0, 1], [28, 0]);

  return (
    <AbsoluteFill
      style={{
        alignItems: 'center',
        background: 'linear-gradient(140deg, ' + palette.ink + ' 0%, #0D5C44 100%)',
        display: 'flex',
        justifyContent: 'center',
        opacity,
      }}
    >
      <div
        style={{
          border: '1px solid rgba(218, 248, 232, 0.22)',
          borderRadius: 28,
          boxShadow: '0 24px 60px rgba(0, 0, 0, 0.16)',
          padding: '64px 94px 68px',
          textAlign: 'center',
          transform: 'translateY(' + lift + 'px)',
        }}
      >
        <div style={{color: '#A6E9C8', fontSize: 14, fontWeight: 750, letterSpacing: '0.14em'}}>
          THE GOAL
        </div>
        <div style={{color: '#FFFFFF', fontSize: 74, fontWeight: 625, letterSpacing: '-0.065em', lineHeight: 1, marginTop: 22}}>
          Keep eligible orders moving
        </div>
        <div style={{color: '#CDE8D9', fontSize: 32, letterSpacing: '-0.035em', marginTop: 20}}>
          while questionable stock stays held.
        </div>
      </div>
    </AbsoluteFill>
  );
};

const NarrationCaption = ({frame}) => {
  const captions = [
    {
      from: 0,
      to: 274,
      text: 'I built LogisticPilot for small businesses, where one person may handle receiving, inspections, and customer orders.',
    },
    {from: 274, to: 417, text: 'When five parts look questionable, should all twenty-five have to wait?'},
    {
      from: 417,
      to: 655,
      text: 'I’ll show you how I upload a photo, ask the agent what can move, and verify the result in the connected apps.',
    },
    {from: 655, to: 693, text: 'Here’s how I built it.'},
    {
      from: 707,
      to: 915,
      text: 'Strands and Bedrock combine image analysis with current ERP evidence to propose the next step.',
    },
    {from: 915, to: 1043, text: 'My application checks the action, and an operator confirms it.'},
    {from: 1043, to: 1171, text: 'Then it updates ERPNext and reads the result back.'},
    {
      from: 1171,
      to: 1410,
      text: 'The goal is simple: keep eligible orders moving while the questionable stock stays held.',
    },
  ];
  const caption = captions.find(({from, to}) => frame >= from && frame < to);
  if (!caption) return null;

  const opacity = sceneOpacity(frame, caption.from, caption.to, 10, 10);
  const contrast = frame >= timeline.goal.from ? '#CDE8D9' : frame >= timeline.architecture.from ? palette.ink : palette.muted;

  return (
    <div
      style={{
        bottom: 45,
        color: contrast,
        fontSize: 21,
        fontWeight: 560,
        left: 210,
        letterSpacing: '-0.02em',
        lineHeight: 1.25,
        opacity,
        position: 'absolute',
        right: 210,
        textAlign: 'center',
      }}
    >
      {caption.text}
    </div>
  );
};

export const OpeningArchitectureV2 = () => {
  const frame = useCurrentFrame();
  const architectureFrame = interpolate(
    frame,
    [timeline.architecture.from, 707, 915, 1043, timeline.goal.from],
    [0, 96, 297, 440, 559],
    {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    },
  );
  const architectureOpacity =
    progress(frame, timeline.architecture.from, timeline.architecture.from + 18) *
    (1 - progress(frame, timeline.goal.from + 18, timeline.goal.from + 48));

  return (
    <AbsoluteFill
      style={{
        background: palette.canvas,
        color: palette.ink,
        fontFamily: 'Geist, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        overflow: 'hidden',
      }}
    >
      <style>{'@font-face { font-family: "Geist"; src: url("' + staticFile('geist-latin.woff2') + '") format("woff2"); font-style: normal; font-weight: 100 900; font-display: block; }'}</style>
      <Audio src={staticFile('narration-v2.mp3')} />
      <Opening frame={frame} />
      <AbsoluteFill style={{opacity: architectureOpacity}}>
        <ArchitectureDiagram frame={architectureFrame} showCaptions={false} />
      </AbsoluteFill>
      <NarrationCaption frame={frame} />
      <Goal frame={frame} />
    </AbsoluteFill>
  );
};
