import {
  AbsoluteFill,
  Audio,
  Easing,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

const palette = {
  canvas: '#F5F7F4',
  paper: '#FFFFFF',
  ink: '#163C2C',
  muted: '#64756D',
  line: '#D7E2DB',
  soft: '#EAF1EC',
  emerald: '#159D72',
  emeraldSoft: '#DCF4EA',
  emeraldDark: '#087455',
  shadow: '0 18px 44px rgba(22, 60, 44, 0.10)',
};

const frames = {
  photo: 0,
  reason: 96,
  check: 297,
  execute: 440,
  result: 559,
};

const captions = [
  {from: 0, to: 96, text: 'An operator brings a photo and a question.'},
  {
    from: 96,
    to: 297,
    text: 'Our Strands agent uses image analysis and the current ERP evidence to propose the next step.',
  },
  {from: 297, to: 375, text: 'LogisticPilot checks the action.'},
  {from: 375, to: 440, text: 'A person confirms it.'},
  {
    from: 440,
    to: 700,
    text: 'Then we update ERPNext and read back the result: twenty dispatched, five still held.',
  },
];

const bounded = (value, min, max) => Math.min(Math.max(value, min), max);

const progress = (frame, start, end) =>
  interpolate(frame, [start, end], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

const rgba = (hex, opacity) => {
  const normalized = hex.replace('#', '');
  const red = Number.parseInt(normalized.slice(0, 2), 16);
  const green = Number.parseInt(normalized.slice(2, 4), 16);
  const blue = Number.parseInt(normalized.slice(4, 6), 16);
  return `rgba(${red}, ${green}, ${blue}, ${opacity})`;
};

const IconBase = ({children, size = 34, stroke = palette.ink, strokeWidth = 2.2}) => (
  <svg
    aria-hidden="true"
    fill="none"
    height={size}
    viewBox="0 0 32 32"
    width={size}
    xmlns="http://www.w3.org/2000/svg"
  >
    <g stroke={stroke} strokeLinecap="round" strokeLinejoin="round" strokeWidth={strokeWidth}>
      {children}
    </g>
  </svg>
);

const PhotoIcon = ({size = 34, stroke}) => (
  <IconBase size={size} stroke={stroke}>
    <rect height="20" rx="3" width="25" x="3.5" y="7" />
    <circle cx="11" cy="13" r="2" />
    <path d="m5.5 24 6.5-6 4.4 4.2 3.3-3 6.8 5.6" />
  </IconBase>
);

const SparkIcon = ({size = 34, stroke}) => (
  <IconBase size={size} stroke={stroke}>
    <path d="M16 2.8c1.6 7.8 5.5 11.7 13.2 13.2-7.7 1.6-11.6 5.5-13.2 13.2C14.5 21.5 10.6 17.6 2.8 16 10.6 14.5 14.5 10.6 16 2.8Z" />
    <path d="M24.5 4.4c.5 2.4 1.7 3.6 4.1 4.1-2.4.5-3.6 1.7-4.1 4.1-.5-2.4-1.7-3.6-4.1-4.1 2.4-.5 3.6-1.7 4.1-4.1Z" />
  </IconBase>
);

const CheckIcon = ({size = 34, stroke}) => (
  <IconBase size={size} stroke={stroke}>
    <circle cx="16" cy="16" r="12.5" />
    <path d="m10.2 16.1 3.7 3.7 7.8-8" />
  </IconBase>
);

const DatabaseIcon = ({size = 34, stroke}) => (
  <IconBase size={size} stroke={stroke}>
    <ellipse cx="16" cy="7.5" rx="11.5" ry="4.1" />
    <path d="M4.5 7.5v8.4C4.5 18.2 9.6 20 16 20s11.5-1.8 11.5-4.1V7.5" />
    <path d="M4.5 15.7v8.1C4.5 26.1 9.6 28 16 28s11.5-1.9 11.5-4.2v-8.1" />
  </IconBase>
);

const CameraScene = () => (
  <div
    style={{
      alignItems: 'center',
      background: 'linear-gradient(145deg, #DBECE3 0%, #F9FCFA 100%)',
      border: `1px solid ${palette.line}`,
      borderRadius: 16,
      display: 'flex',
      height: 92,
      justifyContent: 'center',
      overflow: 'hidden',
      position: 'relative',
    }}
  >
    <div
      style={{
        background: '#BBD4C6',
        borderRadius: 5,
        bottom: 16,
        height: 32,
        left: 42,
        position: 'absolute',
        transform: 'rotate(-7deg)',
        width: 64,
      }}
    />
    <div
      style={{
        background: '#7FB499',
        borderRadius: 5,
        bottom: 16,
        height: 45,
        position: 'absolute',
        right: 48,
        transform: 'rotate(8deg)',
        width: 58,
      }}
    />
    <div
      style={{
        alignItems: 'center',
        background: 'rgba(255, 255, 255, 0.92)',
        border: `1px solid ${rgba(palette.ink, 0.1)}`,
        borderRadius: 11,
        display: 'flex',
        height: 45,
        justifyContent: 'center',
        position: 'relative',
        width: 58,
      }}
    >
      <PhotoIcon size={25} stroke={palette.emeraldDark} />
    </div>
  </div>
);

const Tag = ({children, accent = false}) => (
  <span
    style={{
      background: accent ? palette.emeraldSoft : '#F1F5F2',
      border: `1px solid ${accent ? '#C5EADB' : '#E4ECE7'}`,
      borderRadius: 999,
      color: accent ? palette.emeraldDark : '#496158',
      display: 'inline-flex',
      fontSize: 16,
      fontWeight: 700,
      letterSpacing: '0.01em',
      lineHeight: 1,
      padding: '8px 10px',
      whiteSpace: 'nowrap',
    }}
  >
    {children}
  </span>
);

const StationContents = ({id}) => {
  if (id === 'photo') {
    return (
      <>
        <CameraScene />
        <div style={{display: 'flex', gap: 8, marginTop: 14}}>
          <Tag>Batch photo</Tag>
          <Tag accent>Order + stock</Tag>
        </div>
      </>
    );
  }

  if (id === 'reason') {
    return (
      <div style={{display: 'grid', gap: 12, marginTop: 4}}>
        <div style={{display: 'flex', gap: 8}}>
          <Tag accent>Bedrock</Tag>
          <Tag>Strands</Tag>
        </div>
        <div style={{color: palette.muted, fontSize: 20, lineHeight: 1.4}}>
          Image analysis + evidence tools
        </div>
        <div
          style={{
            alignItems: 'center',
            background: '#F1F8F4',
            borderRadius: 12,
            color: palette.emeraldDark,
            display: 'flex',
            fontSize: 16,
            fontWeight: 700,
            gap: 8,
            padding: '10px 12px',
          }}
        >
          <span style={{fontSize: 20}}>↗</span> Propose next step
        </div>
      </div>
    );
  }

  if (id === 'check') {
    return (
      <div style={{display: 'grid', gap: 10, marginTop: 3}}>
        <div
          style={{
            alignItems: 'center',
            background: '#F5F8F6',
            borderRadius: 13,
            color: palette.ink,
            display: 'flex',
            fontSize: 20,
            fontWeight: 700,
            gap: 10,
            padding: '12px 13px',
          }}
        >
          <CheckIcon size={22} stroke={palette.emeraldDark} /> App checks
        </div>
        <div
          style={{
            alignItems: 'center',
            background: '#F5F8F6',
            borderRadius: 13,
            color: palette.ink,
            display: 'flex',
            fontSize: 20,
            fontWeight: 700,
            gap: 10,
            padding: '12px 13px',
          }}
        >
          <span style={{color: palette.emeraldDark, fontSize: 21, lineHeight: 1}}>●</span> Person approves
        </div>
      </div>
    );
  }

  return (
    <div style={{display: 'grid', gap: 12, marginTop: 4}}>
      <div style={{display: 'flex', gap: 8}}>
        <Tag accent>Write update</Tag>
        <Tag>Read back</Tag>
      </div>
      <div style={{color: palette.muted, fontSize: 20, lineHeight: 1.38}}>
        Verify the ERP record.
      </div>
    </div>
  );
};

const Station = ({frame, icon: Icon, id, index, label, title, start}) => {
  const {fps} = useVideoConfig();
  const entrance = spring({
    config: {damping: 16, mass: 0.65, stiffness: 115},
    fps,
    frame: Math.max(0, frame - 18 - index * 9),
  });
  const stageProgress = progress(frame, start, start + 25);
  const nextStart = [frames.reason, frames.check, frames.execute, 700][index];
  const completed = progress(frame, start + 20, nextStart + 12);
  const active = stageProgress * (1 - progress(frame, nextStart, nextStart + 18));
  const glow = bounded(active + completed * 0.2, 0, 1);

  return (
    <div
      style={{
        background: palette.paper,
        border: `1px solid ${rgba(palette.emerald, 0.10 + glow * 0.38)}`,
        borderRadius: 24,
        boxShadow: glow > 0.1 ? `0 22px 52px ${rgba(palette.emerald, 0.16)}, ${palette.shadow}` : palette.shadow,
        boxSizing: 'border-box',
        display: 'flex',
        flexDirection: 'column',
        height: 326,
        opacity: interpolate(entrance, [0, 0.6, 1], [0, 0.9, 1]),
        padding: '26px 25px 24px',
        position: 'relative',
        transform: `translateY(${interpolate(entrance, [0, 1], [34, 0])}px) scale(${0.975 + entrance * 0.025 + active * 0.012})`,
        width: 350,
      }}
    >
      <div
        style={{
          background: `linear-gradient(90deg, ${palette.emerald}, ${rgba(palette.emerald, 0.12)})`,
          borderRadius: 20,
          height: 4,
          left: 25,
          opacity: 0.18 + glow * 0.82,
          position: 'absolute',
          right: 25,
          top: 14,
          transform: `scaleX(${0.35 + glow * 0.65})`,
          transformOrigin: 'left',
        }}
      />
      <div style={{alignItems: 'center', display: 'flex', justifyContent: 'space-between'}}>
        <div
          style={{
            alignItems: 'center',
            background: glow > 0.26 ? palette.emeraldSoft : '#F1F5F2',
            borderRadius: 15,
            display: 'flex',
            height: 52,
            justifyContent: 'center',
            width: 52,
          }}
        >
          <Icon size={29} stroke={glow > 0.3 ? palette.emeraldDark : palette.ink} />
        </div>
        <div
          style={{
            color: glow > 0.3 ? palette.emeraldDark : palette.muted,
            fontSize: 13,
            fontWeight: 700,
            letterSpacing: '0.12em',
          }}
        >
          {label}
        </div>
      </div>
      <div style={{color: palette.ink, fontSize: 30, fontWeight: 600, letterSpacing: '-0.035em', lineHeight: 1.08, marginTop: 20}}>
        {title}
      </div>
      <div style={{marginTop: 16}}>
        <StationContents id={id} />
      </div>
    </div>
  );
};

const Connector = ({frame, start}) => {
  const reveal = progress(frame, start - 5, start + 26);
  const pulse = progress(frame, start + 8, start + 70);
  const isPast = frame > start + 70;
  const dotPosition = isPast ? 1 : pulse;

  return (
    <div
      style={{
        height: 326,
        position: 'relative',
        width: 86,
      }}
    >
      <div
        style={{
          background: palette.line,
          height: 2,
          left: 18,
          position: 'absolute',
          right: 18,
          top: 162,
        }}
      />
      <div
        style={{
          background: palette.emerald,
          height: 2,
          left: 18,
          opacity: reveal * 0.85,
          position: 'absolute',
          top: 162,
          transform: `scaleX(${reveal})`,
          transformOrigin: 'left',
          width: `calc(100% - 36px)`,
        }}
      />
      <div
        style={{
          borderBottom: `2px solid ${palette.emerald}`,
          borderRight: `2px solid ${palette.emerald}`,
          height: 9,
          opacity: reveal,
          position: 'absolute',
          right: 20,
          top: 157,
          transform: 'rotate(-45deg)',
          width: 9,
        }}
      />
      <div
        style={{
          background: palette.emerald,
          border: `4px solid ${palette.canvas}`,
          borderRadius: 50,
          boxShadow: `0 0 0 5px ${rgba(palette.emerald, 0.13)}`,
          height: 13,
          left: `calc(18px + (100% - 52px) * ${dotPosition})`,
          opacity: reveal * (isPast ? 0.25 : 1),
          position: 'absolute',
          top: 154,
          transform: 'translateX(-50%)',
          width: 13,
        }}
      />
    </div>
  );
};

const ResultPanel = ({frame}) => {
  const {fps} = useVideoConfig();
  const appear = spring({
    config: {damping: 17, mass: 0.62, stiffness: 130},
    fps,
    frame: Math.max(0, frame - frames.result),
  });

  return (
    <div
      style={{
        alignItems: 'center',
        background: palette.ink,
        borderRadius: 22,
        bottom: 121,
        boxShadow: '0 18px 38px rgba(22, 60, 44, 0.22)',
        color: '#FFFFFF',
        display: 'flex',
        gap: 22,
        left: 490,
        minHeight: 103,
        opacity: appear,
        padding: '17px 24px',
        position: 'absolute',
        right: 490,
        transform: `translateY(${interpolate(appear, [0, 1], [28, 0])}px) scale(${0.96 + appear * 0.04})`,
      }}
    >
      <div
        style={{
          alignItems: 'center',
          background: palette.emerald,
          borderRadius: 15,
          display: 'flex',
          height: 58,
          justifyContent: 'center',
          width: 58,
        }}
      >
        <CheckIcon size={32} stroke="#FFFFFF" />
      </div>
      <div style={{flex: 1}}>
        <div style={{fontSize: 13, fontWeight: 700, letterSpacing: '0.12em', opacity: 0.72}}>VERIFIED POC RESULT</div>
        <div style={{fontSize: 28, fontWeight: 600, letterSpacing: '-0.03em', marginTop: 4}}>
          20 dispatched <span style={{color: '#8DE0BC', padding: '0 7px'}}>•</span> 5 held
        </div>
      </div>
      <div style={{borderLeft: '1px solid rgba(255, 255, 255, 0.16)', paddingLeft: 20}}>
        <div style={{color: '#C4D9CD', fontSize: 13, fontWeight: 700}}>ERPNext</div>
        <div style={{fontSize: 15, fontWeight: 700, marginTop: 3}}>read back</div>
      </div>
    </div>
  );
};

const Caption = ({frame}) => {
  const caption = captions.find(({from, to}) => frame >= from && frame < to) ?? captions[captions.length - 1];
  const index = captions.indexOf(caption);
  const entry = progress(frame, caption.from, caption.from + 11);
  const exit = progress(frame, caption.to - 9, caption.to);
  const opacity = entry * (1 - exit);

  return (
    <div
      style={{
        bottom: 45,
        color: palette.ink,
        fontSize: 24,
        fontWeight: 500,
        left: 228,
        letterSpacing: '-0.02em',
        lineHeight: 1.25,
        opacity,
        position: 'absolute',
        right: 228,
        textAlign: 'center',
        transform: `translateY(${interpolate(entry, [0, 1], [8, 0])}px)`,
      }}
    >
      <span style={{color: palette.emeraldDark, fontSize: 15, fontWeight: 700, letterSpacing: '0.10em', marginRight: 15}}>
        {String(index + 1).padStart(2, '0')}
      </span>
      {caption.text}
    </div>
  );
};

export const ArchitecturePreview = () => {
  const frame = useCurrentFrame();
  const titleIn = progress(frame, 0, 22);
  const topLine = progress(frame, 12, 42);
  const stations = [
    {id: 'photo', icon: PhotoIcon, label: '01 · OBSERVE', title: 'Photo + ERP facts', start: frames.photo},
    {id: 'reason', icon: SparkIcon, label: '02 · REASON', title: 'Strands agent', start: frames.reason},
    {id: 'check', icon: CheckIcon, label: '03 · CONTROL', title: 'Check + confirm', start: frames.check},
    {id: 'execute', icon: DatabaseIcon, label: '04 · EXECUTE', title: 'ERPNext', start: frames.execute},
  ];

  return (
    <AbsoluteFill
      style={{
        background: palette.canvas,
        color: palette.ink,
        fontFamily: 'Geist, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        overflow: 'hidden',
      }}
    >
      <style>{`@font-face { font-family: "Geist"; src: url("${staticFile('geist-latin.woff2')}") format("woff2"); font-style: normal; font-weight: 100 900; font-display: block; }`}</style>
      <Audio src={staticFile('narration.mp3')} />
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
        <div style={{alignItems: 'center', display: 'flex', gap: 12, opacity: titleIn}}>
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
        <div
          style={{
            border: `1px solid ${palette.line}`,
            borderRadius: 999,
            color: palette.muted,
            fontSize: 14,
            fontWeight: 700,
            letterSpacing: '0.08em',
            opacity: titleIn,
            padding: '10px 14px',
          }}
        >
          ARCHITECTURE PREVIEW
        </div>
      </div>
      <div
        style={{
          left: 82,
          opacity: titleIn,
          position: 'absolute',
          right: 82,
          textAlign: 'center',
          top: 134,
          transform: `translateY(${interpolate(titleIn, [0, 1], [18, 0])}px)`,
        }}
      >
        <h1 style={{fontSize: 56, fontWeight: 600, letterSpacing: '-0.052em', lineHeight: 1.05, margin: 0}}>
          From a photo to a verified action
        </h1>
        <div
          style={{
            background: palette.emerald,
            height: 4,
            margin: '23px auto 0',
            opacity: topLine,
            transform: `scaleX(${topLine})`,
            transformOrigin: 'center',
            width: 102,
          }}
        />
      </div>
      <div
        style={{
          alignItems: 'center',
          display: 'flex',
          left: 131,
          position: 'absolute',
          right: 131,
          top: 358,
        }}
      >
        {stations.map((station, index) => (
          <div key={station.id} style={{alignItems: 'center', display: 'flex'}}>
            <Station frame={frame} index={index} {...station} />
            {index < stations.length - 1 ? (
              <Connector
                frame={frame}
                start={[frames.reason, frames.check, frames.execute][index]}
              />
            ) : null}
          </div>
        ))}
      </div>
      <ResultPanel frame={frame} />
      <Caption frame={frame} />
    </AbsoluteFill>
  );
};
