/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL of the LearnFlow FastAPI backend, e.g. http://localhost:8000 */
  readonly VITE_API_BASE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
