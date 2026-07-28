/**
 * Contract validation for POST /v1/recommendations (Phase C).
 *
 * The SINGLE source of truth is `contracts/ghar-re-v1.schema.json` (Phase A) — imported directly,
 * NOT re-declared here (RE-DOC-10 §15, RE-DOC-11 §5). The Edge Function validates its OUTGOING
 * payload before calling the RE, and (defensively) the RE's response before passing it through.
 *
 * Uses Ajv (2020-12) in non-strict mode so the schema's `x-*` annotation keywords and open
 * `additionalProperties:true` (the additive/open compatibility rule, RE-DOC-11 §5) are honored.
 */
import Ajv2020 from "ajv/dist/2020.js";
import contract from "../../../contracts/ghar-re-v1.schema.json" with { type: "json" };

// deno-lint-ignore no-explicit-any
const ajv = new (Ajv2020 as any)({ strict: false, allErrors: true });
// deno-lint-ignore no-explicit-any
const c = contract as any;
ajv.addSchema(c, "ghar-re-v1");

// deno-lint-ignore no-explicit-any
const requestValidator = ajv.getSchema(`ghar-re-v1#/$defs/RecommendationRequest`) as any;
// deno-lint-ignore no-explicit-any
const responseValidator = ajv.getSchema(`ghar-re-v1#/$defs/RecommendationResponse`) as any;

export interface ContractCheck {
  valid: boolean;
  errors: string[];
}

// deno-lint-ignore no-explicit-any
function run(validator: any, payload: unknown): ContractCheck {
  const valid = validator(payload) as boolean;
  if (valid) return { valid: true, errors: [] };
  // deno-lint-ignore no-explicit-any
  const errors = ((validator.errors ?? []) as any[]).slice(0, 8).map(
    (e) => `${e.instancePath || "<root>"} ${e.message}`,
  );
  return { valid: false, errors };
}

/** Validate an outgoing recommendation request against the ghar-re-v1 contract (additive/open). */
export function validateRequest(payload: unknown): ContractCheck {
  return run(requestValidator, payload);
}

/** Validate a recommendation response against the contract (fail-closed defense on passthrough). */
export function validateResponse(payload: unknown): ContractCheck {
  return run(responseValidator, payload);
}
