/**
 * Laya for pi: local, offline typed decisions from the laya-agent decision server.
 *
 *  - Tools the model can call: laya_choice, laya_yesno, laya_classify (about 15-25 ms each).
 *  - A gate on the built-in bash tool: Laya rates each command safe / needs_approval / destructive.
 *      destructive      -> ask the user (blocked when there is no UI)
 *      needs_approval   -> allowed, unless LAYA_GATE=strict (then ask)
 *  - /laya shows server status.
 *
 * Requires the server:  cd laya-agent && make serve   (127.0.0.1:8780, override with LAYA_URL)
 * Env: LAYA_URL, LAYA_GATE = off | default | strict, LAYA_GATE_FAIL = open (default) | closed
 * The gate is a safety net, not a sandbox: Laya is a classifier and misses things (measured 7/8 on a small set).
 */

import { Type } from "@earendil-works/pi-ai";
import { defineTool, type ExtensionAPI } from "@earendil-works/pi-coding-agent";

const URL_BASE = (process.env.LAYA_URL ?? "http://127.0.0.1:8780").replace(/\/$/, "");
const GATE = process.env.LAYA_GATE ?? "default";
const FAIL_CLOSED = process.env.LAYA_GATE_FAIL === "closed";
const USECASES = [
	"shell_risk",
	"test_verdict",
	"page_kind",
	"is_blocked",
	"agent_health",
	"needs_review",
	"model_tier",
	"chat_route",
] as const;

async function laya(path: string, body?: unknown, signal?: AbortSignal): Promise<any> {
	const response = await fetch(`${URL_BASE}${path}`, {
		method: body === undefined ? "GET" : "POST",
		body: body === undefined ? undefined : JSON.stringify(body),
		signal: signal ?? AbortSignal.timeout(5000),
	});
	const data = await response.json();
	if (!response.ok) throw new Error(data?.error ?? `Laya HTTP ${response.status}`);
	return data;
}

const text = (value: unknown) => ({
	content: [{ type: "text" as const, text: JSON.stringify(value) }],
	details: value,
});

const choiceTool = defineTool({
	name: "laya_choice",
	label: "Laya choice",
	description:
		"Pick exactly one option for a short text using the local Laya classifier (about 15 ms, offline). " +
		"Good for routing, triage and categorising. Not for planning or long documents (keep state under about 150 tokens).",
	parameters: Type.Object({
		state: Type.String({ description: "The text to judge (short)" }),
		question: Type.String({ description: "What to decide, e.g. 'Which team should handle this?'" }),
		options: Type.Array(Type.String(), { description: "Candidate labels", minItems: 2 }),
	}),
	async execute(_id, p, signal) {
		return text(await laya("/v1/choice", { state: p.state, instructions: p.question, options: p.options }, signal));
	},
});

const yesnoTool = defineTool({
	name: "laya_yesno",
	label: "Laya yes/no",
	description:
		"Probability that a proposition about a short text is true (local Laya). p_true is conservative: " +
		"real positives often land at 0.4-0.6, so treat >= 0.4 as likely yes and verify anything important.",
	parameters: Type.Object({
		state: Type.String({ description: "The text to judge (short)" }),
		proposition: Type.String({ description: "A concrete statement, naming the categories you care about" }),
	}),
	async execute(_id, p, signal) {
		return text(await laya("/v1/yesno", { state: p.state, proposition: p.proposition }, signal));
	},
});

const classifyTool = defineTool({
	name: "laya_classify",
	label: "Laya classify",
	description:
		`Run a ready-made Laya primitive on text. name is one of: ${USECASES.join(", ")}. ` +
		"shell_risk(command) -> safe|needs_approval|destructive; test_verdict(log) -> passed|failed|error; " +
		"page_kind(page text); is_blocked(page text); agent_health(terminal tail); needs_review(diff summary); " +
		"model_tier(request); chat_route(message).",
	parameters: Type.Object({
		name: Type.Union(USECASES.map((n) => Type.Literal(n))),
		input: Type.String({ description: "The text to classify (short)" }),
	}),
	async execute(_id, p, signal) {
		return text(await laya(`/v1/usecase/${p.name}`, { input: p.input }, signal));
	},
});

export default function (pi: ExtensionAPI) {
	pi.registerTool(choiceTool);
	pi.registerTool(yesnoTool);
	pi.registerTool(classifyTool);

	pi.registerCommand("laya", {
		description: "Show Laya decision server status",
		handler: async (_args, ctx) => {
			try {
				const health = await laya("/health");
				ctx.ui.notify(`Laya ready: ${health.model} at ${URL_BASE} (gate: ${GATE})`, "info");
			} catch (error) {
				ctx.ui.notify(`Laya server not reachable at ${URL_BASE}: run 'make serve' in laya-agent (${error})`, "warning");
			}
		},
	});

	if (GATE === "off") return;

	pi.on("tool_call", async (event, ctx) => {
		if (event.toolName !== "bash") return undefined;
		const command = String(event.input.command ?? "");
		let risk: string;
		try {
			risk = (await laya("/v1/usecase/shell_risk", { input: command })).result;
		} catch (error) {
			if (FAIL_CLOSED) return { block: true, reason: `Laya gate unavailable (${error}); LAYA_GATE_FAIL=closed` };
			return undefined;
		}
		const ask = risk === "destructive" || (GATE === "strict" && risk === "needs_approval");
		if (!ask) return undefined;
		if (!ctx.hasUI) return { block: true, reason: `Laya rated this command ${risk} and there is no UI to confirm` };
		const choice = await ctx.ui.select(`Laya rates this command "${risk}":\n\n  ${command}\n\nAllow?`, ["Yes", "No"]);
		return choice === "Yes" ? undefined : { block: true, reason: `Blocked by user (Laya: ${risk})` };
	});
}
