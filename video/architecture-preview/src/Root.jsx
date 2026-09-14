import {Composition} from 'remotion';
import {ArchitecturePreview} from './ArchitecturePreview.jsx';
import {OpeningArchitectureV2} from './OpeningArchitectureV2.jsx';

export const ArchitectureRoot = () => {
  return (
    <>
      <Composition
        id="ArchitecturePreview"
        component={ArchitecturePreview}
        durationInFrames={700}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="OpeningArchitectureV2"
        component={OpeningArchitectureV2}
        durationInFrames={1410}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
