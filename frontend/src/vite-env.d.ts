/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_UPLOAD_API_URL: string;
  readonly VITE_QUERY_API_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
