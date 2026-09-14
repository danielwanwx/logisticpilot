import {
  AbsoluteFill,
  Audio,
  Easing,
  interpolate,
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

const Logo = ({opacity = 1}) => (
  <div style={{alignItems: 'center', display: 'flex', gap: 12, opacity}}>
    <div
      style={{
        alignItems: 'center',
        background: palette.ink,
        borderRadius: 11,
        display: 'flex',
        height: 38,
        justifyContent: 'center',
        width: 38,
      }}
    >
      <div style={{display: 'grid', gap: 3, gridTemplateColumns: 'repeat(2, 5px)'}}>
        {[0, 1, 2, 3].map((dot) => (
          <span key={dot} style={{background: '#92E0BD', borderRadius: 50, height: 5, width: 5}} />
        ))}
      </div>
    </div>
    <span style={{fontSize: 22, fontWeight: 650, letterSpacing: '-0.025em'}}>LogisticPilot</span>
  </div>
);

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

const Role = ({label, symbol}) => (
  <div
    style={{
      alignItems: 'center',
      borderTop: '1px solid ' + palette.line,
      display: 'flex',
      gap: 13,
      minWidth: 214,
      paddingTop: 16,
    }}
  >
    <span
      style={{
        alignItems: 'center',
        background: palette.emeraldSoft,
        borderRadius: 50,
        color: palette.emeraldDark,
        display: 'flex',
        fontSize: 22,
        fontWeight: 700,
        height: 38,
        justifyContent: 'center',
        width: 38,
      }}
    >
      {symbol}
    </span>
    <span style={{color: palette.ink, fontSize: 20, fontWeight: 650, letterSpacing: '-0.02em'}}>{label}</span>
  </div>
);

const Quantity = ({label, value, strong = false}) => (
  <div
    style={{
      borderLeft: '1px solid ' + (strong ? '#AEE3C9' : palette.line),
      minWidth: 245,
      paddingLeft: 24,
    }}
  >
    <div
      style={{
        color: strong ? palette.emeraldDark : palette.muted,
        fontSize: 58,
        fontWeight: 650,
        letterSpacing: '-0.07em',
        lineHeight: 0.9,
      }}
    >
      {value}
    </div>
    <div style={{color: palette.ink, fontSize: 18, fontWeight: 650, marginTop: 10}}>{label}</div>
  </div>
);

const FlowStep = ({index, label, symbol}) => (
  <div style={{alignItems: 'center', display: 'flex', gap: 15}}>
    <div
      style={{
        alignItems: 'center',
        background: index === 2 ? palette.emerald : palette.paper,
        border: '1px solid ' + (index === 2 ? palette.emerald : palette.line),
        borderRadius: 17,
        boxShadow: index === 2 ? '0 12px 28px rgba(21, 157, 114, 0.18)' : 'none',
        color: index === 2 ? '#FFFFFF' : palette.emeraldDark,
        display: 'flex',
        fontSize: 30,
        height: 62,
        justifyContent: 'center',
        width: 62,
      }}
    >
      {symbol}
    </div>
    <div>
      <div style={{color: palette.muted, fontSize: 13, fontWeight: 750, letterSpacing: '0.11em'}}>
        0{index + 1}
      </div>
      <div style={{color: palette.ink, fontSize: 22, fontWeight: 650, letterSpacing: '-0.03em', marginTop: 4}}>
        {label}
      </div>
    </div>
  </div>
);

const Opening = ({frame}) => {
  const intro = sceneOpacity(frame, timeline.intro.from, timeline.intro.to);
  const question = sceneOpacity(frame, timeline.question.from, timeline.question.to);
  const promise = sceneOpacity(frame, timeline.promise.from, timeline.promise.to);
  const handoff = sceneOpacity(frame, timeline.handoff.from, timeline.handoff.to, 10, 12);
  const brandOpacity = 1 - progress(frame, timeline.architecture.from - 16, timeline.architecture.from + 12);

  return (
    <AbsoluteFill>
      <div
        style={{
          alignItems: 'center',
          display: 'flex',
          justifyContent: 'space-between',
          left: 82,
          position: 'absolute',
          right: 82,
          top: 58,
        }}
      >
        <Logo opacity={brandOpacity} />
        <div
          style={{
            border: '1px solid ' + palette.line,
            borderRadius: 999,
            color: palette.muted,
            fontSize: 14,
            fontWeight: 700,
            letterSpacing: '0.08em',
            opacity: brandOpacity,
            padding: '10px 14px',
          }}
        >
          RECEIVING DECISIONS
        </div>
      </div>

      <div
        style={{
          left: 180,
          opacity: intro,
          position: 'absolute',
          right: 180,
          textAlign: 'center',
          top: 225,
          transform: 'translateY(' + interpolate(intro, [0, 1], [20, 0]) + 'px)',
        }}
      >
        <Eyebrow>Built for the person running the receiving desk</Eyebrow>
        <h1
          style={{
            color: palette.ink,
            fontSize: 76,
            fontWeight: 630,
            letterSpacing: '-0.065em',
            lineHeight: 0.98,
            margin: '22px 0 0',
          }}
        >
          Built for small parts distributors
        </h1>
        <p style={{color: palette.muted, fontSize: 28, letterSpacing: '-0.025em', lineHeight: 1.35, margin: '24px auto 0', maxWidth: 820}}>
          One person may handle receiving, inspections, and customer orders.
        </p>
        <div style={{display: 'flex', gap: 52, justifyContent: 'center', marginTop: 76}}>
          <Role label="Receiving" symbol="↓" />
          <Role label="Inspection" symbol="○" />
          <Role label="Customer orders" symbol="→" />
        </div>
      </div>

      <div
        style={{
          alignItems: 'center',
          display: 'flex',
          flexDirection: 'column',
          left: 150,
          opacity: question,
          position: 'absolute',
          right: 150,
          textAlign: 'center',
          top: 236,
          transform: 'translateY(' + interpolate(question, [0, 1], [24, 0]) + 'px)',
        }}
      >
        <Eyebrow>One receiving exception</Eyebrow>
        <h2 style={{fontSize: 64, fontWeight: 625, letterSpacing: '-0.06em', lineHeight: 1, margin: '24px 0 0'}}>
          When five parts look questionable,
          <br />
          should all twenty-five have to wait?
        </h2>
        <div
          style={{
            alignItems: 'stretch',
            background: palette.paper,
            border: '1px solid ' + palette.line,
            borderRadius: 24,
            boxShadow: palette.shadow,
            display: 'flex',
            gap: 58,
            marginTop: 66,
            padding: '27px 54px',
          }}
        >
          <Quantity label="need inspection" value="5" />
          <Quantity label="eligible to move" strong value="20" />
        </div>
      </div>

      <div
        style={{
          left: 160,
          opacity: promise,
          position: 'absolute',
          right: 160,
          textAlign: 'center',
          top: 242,
          transform: 'translateY(' + interpolate(promise, [0, 1], [24, 0]) + 'px)',
        }}
      >
        <Eyebrow>Follow one decision end to end</Eyebrow>
        <h2 style={{fontSize: 62, fontWeight: 625, letterSpacing: '-0.06em', lineHeight: 1, margin: '22px 0 0'}}>
          Upload a photo. Ask the agent what can move.
          <br />
          Verify the result in your apps.
        </h2>
        <div
          style={{
            alignItems: 'center',
            display: 'flex',
            gap: 42,
            justifyContent: 'center',
            marginTop: 82,
          }}
        >
          <FlowStep index={0} label="Upload a photo" symbol="↗" />
          <div style={{background: palette.line, height: 1, width: 80}} />
          <FlowStep index={1} label="Ask the agent" symbol="✦" />
          <div style={{background: palette.line, height: 1, width: 80}} />
          <FlowStep index={2} label="Verify in your apps" symbol="✓" />
        </div>
      </div>

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
      text: 'I built LogisticPilot for small parts distributors, where one person may handle receiving, inspections, and customer orders.',
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
