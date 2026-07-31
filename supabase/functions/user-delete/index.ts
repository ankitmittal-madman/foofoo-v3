/**
 * POST /v1/user/delete — Edge Function entrypoint. Same always-on pipeline + `authenticate()`
 * middleware pattern as every other endpoint in this repo.
 */
import { defineHandler } from "../_shared/api/handler.ts";
import { authenticate } from "../_shared/auth/authenticate.ts";
import { makeUserDeleteHandler } from "./handler.ts";

Deno.serve(defineHandler(makeUserDeleteHandler(), { middleware: [authenticate()] }));
