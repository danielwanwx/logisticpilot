import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

const palette = {
  ink: '#062C20',
  emerald: '#16A576',
  emeraldBright: '#77E0B5',
  emeraldSoft: '#CFF6E2',
  mint: '#E8FBF1',
  paper: '#F8FCF9',
  muted: '#A9C9B8',
  subtle: '#76A793',
  card: 'rgba(14, 69, 51, 0.72)',
  cardBorder: 'rgba(183, 239, 211, 0.17)',
};

const bounded = (value, min = 0, max = 1) => Math.min(Math.max(value, min), max);

const ease = (frame, start, end) =>
  interpolate(frame, [start, end], [0, 1], {
    easing: Easing.out(Easing.cubic),
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

const springIn = (frame, fps, start, duration = 28) =>
  bounded(
    spring({
      config: {damping: 18, mass: 0.68, stiffness: 120},
      durationInFrames: duration,
      fps,
      frame: Math.max(0, frame - start),
    }),
  );

const Brand = () => (
  <div
    style={{
      alignItems: 'center',
      display: 'flex',
      gap: 13,
      left: 76,
      position: 'absolute',
      top: 62,
    }}
  >
    <div
      style={{
        alignItems: 'center',
        background: '#E7FFF2',
        borderRadius: 12,
        boxShadow: '0 12px 28px rgba(1, 19, 13, 0.22)',
        display: 'grid',
        gap: 4,
        gridTemplateColumns: 'repeat(2, 6px)',
        height: 38,
        justifyContent: 'center',
        width: 38,
      }}
    >
      {[0, 1, 2, 3].map((dot) => (
        <span
          key={dot}
          style={{background: palette.emerald, borderRadius: '50%', height: 6, width: 6}}
        />
      ))}
    </div>
    <span style={{color: palette.paper, fontSize: 24, fontWeight: 680, letterSpacing: '-0.04em'}}>
      LogisticPilot
    </span>
  </div>
);

const Background = () => (
  <>
    <AbsoluteFill
      style={{
        background:
          'radial-gradient(circle at 50% 12%, rgba(48, 158, 111, 0.42) 0%, rgba(19, 106, 75, 0.18) 25%, rgba(6, 44, 32, 0) 52%), linear-gradient(138deg, #052B20 0%, #073A2B 52%, #06281E 100%)',
      }}
    />
    <div
      style={{
        border: '1px solid rgba(153, 244, 199, 0.08)',
        borderRadius: '50%',
        height: 1130,
        left: 390,
        position: 'absolute',
        top: -616,
        width: 1140,
      }}
    />
    <div
      style={{
        border: '1px solid rgba(153, 244, 199, 0.055)',
        borderRadius: '50%',
        height: 920,
        left: 500,
        position: 'absolute',
        top: -505,
        width: 920,
      }}
    />
    <div
      style={{
        background: 'radial-gradient(circle, rgba(114, 230, 175, 0.14) 0%, rgba(114, 230, 175, 0) 68%)',
        bottom: -260,
        height: 620,
        left: -210,
        position: 'absolute',
        width: 620,
      }}
    />
    <div
      style={{
        background: 'radial-gradient(circle, rgba(35, 178, 125, 0.13) 0%, rgba(35, 178, 125, 0) 68%)',
        height: 620,
        position: 'absolute',
        right: -235,
        top: 516,
        width: 620,
      }}
    />
  </>
);

const Hero = ({frame, fps}) => {
  const heroIn = springIn(frame, fps, 0, 42);
  const capabilityIn = springIn(frame, fps, 30, 54);
  const heroLine = ease(frame, 12, 43);

  return (
    <>
      <div
        style={{
          left: 160,
          opacity: heroIn,
          position: 'absolute',
          right: 160,
          textAlign: 'center',
          top: 162,
          transform: `translateY(${interpolate(heroIn, [0, 1], [32, 0])}px)`,
        }}
      >
        <h1
          style={{
            color: palette.paper,
            fontSize: 98,
            fontWeight: 660,
            letterSpacing: '-0.072em',
            lineHeight: 0.98,
            margin: 0,
          }}
        >
          Keep good orders moving.
        </h1>
        <div
          style={{
            background: palette.emeraldBright,
            borderRadius: 999,
            height: 5,
            margin: '28px auto 0',
            transform: `scaleX(${heroLine})`,
            transformOrigin: 'center',
            width: 110,
          }}
        />
      </div>

      <div
        style={{
          alignItems: 'center',
          background: 'rgba(231, 255, 242, 0.09)',
          border: '1px solid rgba(197, 249, 220, 0.22)',
          borderRadius: 999,
          boxShadow: '0 18px 38px rgba(0, 21, 15, 0.16)',
          color: palette.mint,
          display: 'flex',
          fontSize: 34,
          fontWeight: 540,
          justifyContent: 'center',
          left: 336,
          letterSpacing: '-0.035em',
          minHeight: 76,
          opacity: capabilityIn,
          position: 'absolute',
          right: 336,
          top: 367,
          transform: `translateY(${interpolate(capabilityIn, [0, 1], [22, 0])}px) scale(${interpolate(capabilityIn, [0, 1], [0.975, 1])})`,
        }}
      >
        Photo + order evidence <span style={{color: palette.emeraldBright, margin: '0 13px'}}>→</span> safe fulfillment plan
      </div>
    </>
  );
};

const outcomeStats = [
  {label: 'dispatched', start: 62, value: 20},
  {label: 'safely held', start: 78, value: 5},
  {label: 'systems verified', start: 94, value: 4},
];

const OutcomeCard = ({frame, fps, label, start, value}) => {
  const entry = springIn(frame, fps, start, 48);
  const countProgress = ease(frame, start + 7, start + 43);
  const count = Math.round(interpolate(countProgress, [0, 1], [0, value]));

  return (
    <div
      aria-label={`${value} ${label}`}
      style={{
        background: palette.card,
        border: `1px solid ${palette.cardBorder}`,
        borderRadius: 24,
        boxShadow: '0 22px 50px rgba(0, 18, 12, 0.22)',
        boxSizing: 'border-box',
        height: 194,
        opacity: entry,
        overflow: 'hidden',
        padding: '37px 36px',
        position: 'relative',
        transform: `translateY(${interpolate(entry, [0, 1], [38, 0])}px) scale(${interpolate(entry, [0, 1], [0.96, 1])})`,
        width: 420,
      }}
    >
      <div
        style={{
          background: 'linear-gradient(90deg, #58D9A4, rgba(88, 217, 164, 0.06))',
          height: 4,
          left: 36,
          position: 'absolute',
          right: 36,
          top: 23,
          transform: `scaleX(${countProgress})`,
          transformOrigin: 'left',
        }}
      />
      <div
        style={{
          alignItems: 'baseline',
          color: palette.paper,
          display: 'flex',
          gap: 15,
          lineHeight: 1,
          whiteSpace: 'nowrap',
        }}
      >
        <span style={{fontSize: 76, fontVariantNumeric: 'tabular-nums', fontWeight: 670, letterSpacing: '-0.075em'}}>{count}</span>
        <span style={{color: palette.mint, fontSize: label === 'systems verified' ? 25 : 29, fontWeight: 570, letterSpacing: '-0.04em'}}>
          {label}
        </span>
      </div>
      <div
        style={{
          background: 'rgba(202, 247, 222, 0.14)',
          borderRadius: 999,
          bottom: 31,
          height: 8,
          left: 38,
          position: 'absolute',
          width: 8,
        }}
      />
    </div>
  );
};

const Outcomes = ({frame, fps}) => (
  <div
    style={{
      display: 'flex',
      gap: 24,
      justifyContent: 'center',
      left: 0,
      position: 'absolute',
      right: 0,
      top: 505,
    }}
  >
    {outcomeStats.map((stat) => (
      <OutcomeCard key={stat.label} frame={frame} fps={fps} {...stat} />
    ))}
  </div>
);

const approvalSteps = [
  {label: 'Agent recommends', start: 141},
  {label: 'Human approves', start: 153, emphasis: true},
  {label: 'Systems execute', start: 165},
];

const ApprovalBoundary = ({frame, fps}) => {
  const shell = springIn(frame, fps, 141, 30);

  return (
    <div
      aria-label="Agent recommends · Human approves · Systems execute"
      style={{
        alignItems: 'center',
        background: 'rgba(3, 31, 22, 0.42)',
        border: '1px solid rgba(202, 247, 222, 0.16)',
        borderRadius: 19,
        boxShadow: '0 18px 42px rgba(0, 16, 10, 0.15)',
        display: 'flex',
        height: 94,
        justifyContent: 'center',
        left: 263,
        opacity: shell,
        position: 'absolute',
        right: 263,
        top: 759,
        transform: `translateY(${interpolate(shell, [0, 1], [22, 0])}px)`,
      }}
    >
      {approvalSteps.map((step, index) => {
        const entry = springIn(frame, fps, step.start, 42);
        return (
          <div key={step.label} style={{alignItems: 'center', display: 'flex'}}>
            {index > 0 ? (
              <span
                style={{
                  color: palette.emeraldBright,
                  fontSize: 29,
                  margin: '0 29px',
                  opacity: entry,
                  transform: `scale(${interpolate(entry, [0, 1], [0.3, 1])})`,
                }}
              >
                ·
              </span>
            ) : null}
            <span
              style={{
                color: step.emphasis ? palette.emeraldBright : palette.mint,
                fontSize: 30,
                fontWeight: step.emphasis ? 660 : 560,
                letterSpacing: '-0.042em',
                opacity: entry,
                transform: `translateY(${interpolate(entry, [0, 1], [10, 0])}px)`,
                whiteSpace: 'nowrap',
              }}
            >
              {step.label}
            </span>
          </div>
        );
      })}
    </div>
  );
};

const apps = ['ERPNext', 'Airtable', 'Jira', 'Slack'];

const AppProof = ({frame, fps}) => (
  <div
    aria-label="ERPNext · Airtable · Jira · Slack"
    style={{
      alignItems: 'center',
      display: 'flex',
      justifyContent: 'center',
      left: 0,
      position: 'absolute',
      right: 0,
      top: 924,
    }}
  >
    {apps.map((app, index) => {
      const entry = springIn(frame, fps, 193 + index * 12, 24);
      return (
        <div key={app} style={{alignItems: 'center', display: 'flex'}}>
          {index > 0 ? (
            <span
              style={{
                color: palette.emeraldBright,
                fontSize: 28,
                margin: '0 20px',
                opacity: entry,
              }}
            >
              ·
            </span>
          ) : null}
          <span
            style={{
              color: palette.muted,
              fontSize: 27,
              fontWeight: 570,
              letterSpacing: '-0.035em',
              opacity: entry,
              transform: `translateY(${interpolate(entry, [0, 1], [10, 0])}px)`,
            }}
          >
            {app}
          </span>
        </div>
      );
    })}
  </div>
);

export const CompetitionEndCard = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  return (
    <AbsoluteFill
      style={{
        background: palette.ink,
        color: palette.paper,
        fontFamily: 'Geist, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        overflow: 'hidden',
      }}
    >
      <style>{`@font-face { font-family: "Geist"; src: url("${staticFile('geist-latin.woff2')}") format("woff2"); font-style: normal; font-weight: 100 900; font-display: block; }`}</style>
      <Background />
      <Brand />
      <Hero frame={frame} fps={fps} />
      <Outcomes frame={frame} fps={fps} />
      <ApprovalBoundary frame={frame} fps={fps} />
      <AppProof frame={frame} fps={fps} />
    </AbsoluteFill>
  );
};
