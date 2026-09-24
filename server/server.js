// Runs Digicoach outside Claude.
// - Serves the repo (app/, data/, assets/) as static files.
// - Serves /_blob/<id> from the local SVGs, using the ids in data/exercises.json.
// - POST /api/suggest calls the Claude API with the key kept on the server.
import http from "node:http";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import Anthropic from "@anthropic-ai/sdk";

const here = path.dirname(fileURLToPath(import.meta.url));
try { process.loadEnvFile(path.join(here, ".env")); } catch {}

const ROOT = path.resolve(here, "..");
const PORT = Number(process.env.PORT) || 8080;
const MODEL = process.env.ANTHROPIC_MODEL || "claude-opus-5";

if (!process.env.ANTHROPIC_API_KEY) {
  console.warn("ANTHROPIC_API_KEY is not set: copy server/.env.example to server/.env and add your key.");
}
const client = new Anthropic();

// Blob id -> SVG file, from the ids stored in the catalog
const catalog = JSON.parse(await readFile(path.join(ROOT, "data/exercises.json"), "utf8"));
const blobs = {};
for (const e of catalog) {
  if (e.imagenInicio) blobs[e.imagenInicio] = e.files.start;
  if (e.imagenFin) blobs[e.imagenFin] = e.files.end;
  if (e.imagen && !blobs[e.imagen]) blobs[e.imagen] = e.files.start;
}

// Shape the app expects back (see sugerir() in app/index.html)
const ROUTINE_SCHEMA = {
  type: "object",
  properties: {
    ejercicios: {
      type: "array",
      items: {
        type: "object",
        properties: {
          id: { type: "string" },
          repeticiones: { type: "integer" },
          tiempoSegundos: { type: "integer" },
          motivo_en: { type: "string" },
          motivo_es: { type: "string" },
        },
        required: ["id", "repeticiones", "tiempoSegundos", "motivo_en", "motivo_es"],
        additionalProperties: false,
      },
    },
  },
  required: ["ejercicios"],
  additionalProperties: false,
};

async function suggest(prompt) {
  const response = await client.beta.messages.create({
    model: MODEL,
    max_tokens: 4096,
    betas: ["server-side-fallback-2026-07-01"],
    fallbacks: "default",
    output_config: { effort: "low", format: { type: "json_schema", schema: ROUTINE_SCHEMA } },
    messages: [{ role: "user", content: prompt }],
  });
  if (response.stop_reason === "refusal") throw Object.assign(new Error("refused"), { code: "refused" });
  const text = response.content.filter(b => b.type === "text").map(b => b.text).join("");
  return JSON.parse(text);
}

const TYPES = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".json": "application/json; charset=utf-8", ".svg": "image/svg+xml", ".css": "text/css; charset=utf-8", ".png": "image/png" };

function send(res, status, body, type = "application/json; charset=utf-8") {
  res.writeHead(status, { "Content-Type": type });
  res.end(typeof body === "string" || Buffer.isBuffer(body) ? body : JSON.stringify(body));
}

async function readBody(req) {
  let data = "";
  for await (const chunk of req) {
    data += chunk;
    if (data.length > 100_000) throw new Error("body too large");
  }
  return JSON.parse(data || "{}");
}

async function sendFile(res, rel) {
  const file = path.resolve(ROOT, rel);
  if (!file.startsWith(ROOT + path.sep) || /[\\/]\.|node_modules|[\\/]server[\\/]/.test(file.slice(ROOT.length))) {
    return send(res, 404, { error: "not found" });
  }
  try {
    send(res, 200, await readFile(file), TYPES[path.extname(file)] || "application/octet-stream");
  } catch {
    send(res, 404, { error: "not found" });
  }
}

http.createServer(async (req, res) => {
  const url = new URL(req.url, "http://localhost");
  try {
    if (req.method === "POST" && url.pathname === "/api/suggest") {
      const { prompt } = await readBody(req);
      if (typeof prompt !== "string" || !prompt) return send(res, 400, { code: "bad_request" });
      try {
        return send(res, 200, await suggest(prompt));
      } catch (e) {
        console.error("Claude API error:", e.status ?? "", e.message);
        if (e instanceof Anthropic.RateLimitError) return send(res, 429, { code: "rate_limited" });
        if (e instanceof Anthropic.AuthenticationError) return send(res, 502, { code: "bad_key" });
        return send(res, 502, { code: e.code || "api_error" });
      }
    }
    if (req.method !== "GET") return send(res, 405, { error: "method not allowed" });
    if (url.pathname === "/") { res.writeHead(302, { Location: "/app/index.html" }); return res.end(); }
    if (url.pathname.startsWith("/_blob/")) {
      const rel = blobs[url.pathname.slice(7)];
      return rel ? sendFile(res, rel) : send(res, 404, { error: "not found" });
    }
    return sendFile(res, decodeURIComponent(url.pathname.slice(1)));
  } catch (e) {
    send(res, 500, { error: "server error" });
  }
}).listen(PORT, () => {
  console.log(`Digicoach running at http://localhost:${PORT}/  (model: ${MODEL})`);
});
