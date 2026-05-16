/**
 * Public entry for `@padi/types`.
 *
 * Re-exports:
 * - `api.*`: generated from FastAPI OpenAPI by `pnpm gen:types` at the repo root.
 *   These are the source of truth for request/response shapes.
 * - `domain.*`: hand-curated cross-cutting types that don't appear in the
 *   API surface (e.g., UI store shapes). Phased out as endpoints adopt
 *   strict Pydantic v2 schemas.
 *
 * Until `pnpm gen:types` is run for the first time, only `domain` is
 * exported. After generation, `api.ts` will be re-exported automatically.
 */

export * from "./domain";
// The line below becomes valid after running `pnpm gen:types`:
// export type * as api from "./api";
