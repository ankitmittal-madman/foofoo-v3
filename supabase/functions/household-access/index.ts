/** Authenticated household role, invitation and ownership-management API. */
import { defineHandler } from "../_shared/api/handler.ts";
import { authenticate } from "../_shared/auth/authenticate.ts";
import { makeHouseholdAccessHandler } from "./handler.ts";

Deno.serve(defineHandler(makeHouseholdAccessHandler(), { middleware: [authenticate()] }));
