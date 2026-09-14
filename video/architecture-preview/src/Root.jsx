import {Composition} from 'remotion';
import {ArchitecturePreview} from './ArchitecturePreview.jsx';

export const ArchitectureRoot = () => {
  return (
    <Composition
      id="ArchitecturePreview"
      component={ArchitecturePreview}
      durationInFrames={700}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
