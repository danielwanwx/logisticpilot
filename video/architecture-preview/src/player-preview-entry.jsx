import {createRoot} from 'react-dom/client';
import {PlayerPreview} from './PlayerPreview.jsx';

// `staticFile()` requires an absolute base. A relative value such as `.` is
// normalized to `/./…`, which resolves at the server root rather than beside
// this deployed player bundle.
const previewPath = new URL('./', window.location.href).pathname.replace(/\/$/, '');
window.remotion_staticBase = previewPath || undefined;

const root = document.getElementById('root');
if (!root) throw new Error('Player preview root is missing.');

createRoot(root).render(<PlayerPreview />);
