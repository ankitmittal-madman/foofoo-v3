/** POST /v1/dish-ontology — authenticated food ontology and enrichment entrypoint. */
import { defineHandler } from "../_shared/api/handler.ts";
import { authenticate } from "../_shared/auth/authenticate.ts";
import { makeDishOntologyHandler } from "./handler.ts";

Deno.serve(defineHandler(makeDishOntologyHandler(), { middleware: [authenticate()] }));
