"""Frontend starters — batch 3: assistant-ui chat, CopilotKit in-app agent, generative UI with AI SDK RSC."""

RECORDS = [
    {
        "slug": "assistant-ui-chat-frontend",
        "title": "Production Chat UI With assistant-ui (Streaming, Markdown, Tools)",
        "tldr": "Don't rebuild a chat UI. assistant-ui is a React primitive set with streaming, markdown, code highlighting, auto-scroll, and edit/branch. Wire it to a Next.js route that proxies Anthropic through the Vercel AI SDK.",
        "category": "frontend",
        "language": "typescript",
        "framework": "assistant-ui + Next.js",
        "tags": ["frontend", "assistant-ui", "nextjs", "streaming", "chat"],
        "best_for_tags": ["chat-apps", "ai-sdk", "react"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "Building a chat surface in a Next.js app and you want streaming, markdown, auto-scroll, edit/branch, and tool UI without writing them. assistant-ui supplies the primitives; the AI SDK route proxies the model.",
        "when_not_to_use": "Skip for a single non-interactive completion box (a plain fetch + textarea is less overhead). Skip if you are not on React, since assistant-ui is React-only.",
        "quick_start": "npm i @assistant-ui/react @assistant-ui/react-ai-sdk ai @ai-sdk/anthropic",
        "full_code": '''// ============================================================
// FILE 1: app/api/chat/route.ts  (server — runs on the server only)
// ============================================================
// Proxies the browser chat to Anthropic via the Vercel AI SDK.
// The API key stays server-side; the browser never sees it.
import { anthropic } from "@ai-sdk/anthropic";
import { streamText, convertToCoreMessages, tool, type Message } from "ai";
import { z } from "zod";

export const runtime = "edge";
export const maxDuration = 30;

export async function POST(req: Request) {
  const { messages }: { messages: Message[] } = await req.json();

  const result = streamText({
    model: anthropic("claude-sonnet-4-5"),
    system: "You are a concise, accurate assistant. Use markdown for code.",
    messages: convertToCoreMessages(messages),
    tools: {
      // A tool the model can call; assistant-ui can render its result in the UI.
      getWeather: tool({
        description: "Get the current weather for a city.",
        parameters: z.object({ city: z.string() }),
        execute: async ({ city }) => ({ city, tempC: 21, summary: "Partly cloudy" }),
      }),
    },
  });

  // assistant-ui's runtime reads the AI SDK data-stream protocol.
  // Docs: https://sdk.vercel.ai/docs/ai-sdk-ui/stream-protocol
  return result.toDataStreamResponse();
}

// ============================================================
// FILE 2: app/page.tsx  (client — needs the browser for the hook)
// ============================================================
"use client";

import {
  AssistantRuntimeProvider,
  Thread,
  makeAssistantToolUI,
} from "@assistant-ui/react";
import { useChatRuntime } from "@assistant-ui/react-ai-sdk";

// assistant-ui ships styles; import its CSS (or wire its Tailwind preset).
// Docs: https://www.assistant-ui.com/docs/getting-started
import "@assistant-ui/react/styles/index.css";

// Map the getWeather tool call to a component instead of showing raw JSON.
const WeatherToolUI = makeAssistantToolUI<{ city: string }, { tempC: number; summary: string }>({
  toolName: "getWeather",
  render: ({ args, result }) => (
    <div style={{ border: "1px solid #ddd", borderRadius: 12, padding: 12 }}>
      <strong>{args.city}</strong>
      {result ? <div>{result.tempC}°C — {result.summary}</div> : <div>Loading…</div>}
    </div>
  ),
});

export default function Page() {
  // useChatRuntime points at the route above and speaks the data-stream
  // protocol, so streaming / edit / branch / reload all work out of the box.
  const runtime = useChatRuntime({ api: "/api/chat" });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <main style={{ height: "100dvh", maxWidth: 720, margin: "0 auto" }}>
        <Thread />
        <WeatherToolUI />
      </main>
    </AssistantRuntimeProvider>
  );
}
''',
        "dependencies": [
            {"name": "@assistant-ui/react", "version": "^0.7", "purpose": "Chat UI primitives (Thread, message list, composer)"},
            {"name": "@assistant-ui/react-ai-sdk", "version": "^0.7", "purpose": "useChatRuntime adapter for the Vercel AI SDK"},
            {"name": "ai", "version": "^4.0", "purpose": "Vercel AI SDK: streamText + data-stream protocol"},
            {"name": "@ai-sdk/anthropic", "version": "^1.0", "purpose": "Anthropic model provider for the AI SDK"},
            {"name": "zod", "version": "^3.23", "purpose": "Typed tool parameter schema for getWeather"},
            {"name": "next", "version": "^15.0", "purpose": "App Router, route handlers, RSC"},
        ],
        "env_vars": [
            {"name": "ANTHROPIC_API_KEY", "required": True, "description": "Server-side key read by @ai-sdk/anthropic inside the route handler.", "example": "sk-ant-..."},
        ],
        "setup_steps": [
            "npx create-next-app@latest my-chat (App Router, TypeScript)",
            "npm i @assistant-ui/react @assistant-ui/react-ai-sdk ai @ai-sdk/anthropic zod",
            "Add ANTHROPIC_API_KEY to .env.local",
            "Create app/api/chat/route.ts and app/page.tsx from full_code",
            "npm run dev and open http://localhost:3000",
        ],
        "variations": [
            {"label": "Custom tool UI", "description": "Render a component for a tool call instead of raw JSON.", "code_snippet": "import { makeAssistantToolUI } from '@assistant-ui/react';\\nexport const WeatherUI = makeAssistantToolUI({ toolName: 'getWeather', render: ({ args }) => <WeatherCard city={args.city} /> });"},
            {"label": "Thread list (persistence)", "description": "Add a sidebar of saved conversations.", "code_snippet": "import { ThreadList } from '@assistant-ui/react';\\n// Render <ThreadList /> alongside <Thread /> and back it with a persistence adapter."},
            {"label": "Swap model provider", "description": "Only the AI SDK model changes; the UI is unchanged.", "code_snippet": "import { openai } from '@ai-sdk/openai';\\n// model: openai('gpt-4o') instead of anthropic('claude-sonnet-4-5')"},
        ],
        "common_errors": [
            {"error_text": "Module not found / 'use client' error importing the SDK in the page", "cause": "The server SDK was imported into a client component.", "fix_snippet": "Keep streamText + the model in app/api/chat/route.ts (server). The page is 'use client' and only imports the assistant-ui hook."},
            {"error_text": "Runtime can't parse the stream / messages never render", "cause": "The route returned plain text instead of the AI SDK data-stream.", "fix_snippet": "Return result.toDataStreamResponse() (not toTextStreamResponse). useChatRuntime expects the data-stream protocol."},
            {"error_text": "UI renders unstyled / broken layout", "cause": "assistant-ui styles were not imported.", "fix_snippet": "Import '@assistant-ui/react/styles/index.css' (or configure its Tailwind preset per the docs) once in the app."},
            {"error_text": "401 from Anthropic in the browser console / key visible", "cause": "The model was called from the client, exposing the key.", "fix_snippet": "Never call anthropic() in a client component. All model calls go through the server route; the browser only talks to /api/chat."},
        ],
        "production_checklist": [
            "Call the model only from the server route; never expose ANTHROPIC_API_KEY to the client.",
            "Return toDataStreamResponse so the assistant-ui runtime parses the stream.",
            "Import the assistant-ui CSS (or Tailwind preset) so the UI renders.",
            "Set maxDuration on the route to cover the longest expected stream.",
            "Add rate limiting / auth in front of /api/chat before launch.",
            "Pin @assistant-ui and AI SDK versions; both move fast.",
        ],
        "tested_with": {
            "model_versions": ["claude-sonnet-4-5"],
            "library_versions": ["@assistant-ui/react@0.7", "@assistant-ui/react-ai-sdk@0.7", "ai@4.0", "@ai-sdk/anthropic@1.0", "zod@3.23", "next@15.0"],
            "last_verified_date": "2026-06-10",
        },
        "related_tool_slugs": ["assistant-ui-assistant-ui", "vercel-ai-sdk"],
        "related_glossary_slugs": ["streaming", "server-sent-events", "tool-use", "system-prompt"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "assistant-ui vs building chat with useChat directly?", "answer": "useChat (AI SDK) gives you the message state and streaming; you still build every UI piece — list, auto-scroll, markdown, code blocks, edit/branch. assistant-ui supplies those as composable primitives, so you wire a runtime and drop in <Thread /> instead of rebuilding chat UX."},
            {"question": "Why split into a route and a page?", "answer": "The model call needs the secret key and must run server-side, so streamText lives in the route handler. The page is a client component because useChatRuntime is a React hook that runs in the browser. Mixing them leaks the key or breaks the build."},
            {"question": "Does it stream token by token?", "answer": "Yes. streamText returns a data-stream and toDataStreamResponse sends it incrementally; useChatRuntime consumes the same protocol, so tokens render as they arrive with auto-scroll, no extra wiring."},
            {"question": "Can I render custom UI for tool calls?", "answer": "Yes — makeAssistantToolUI maps a tool name to a React component, so a getWeather call renders a weather card instead of JSON. See the custom tool UI variation."},
        ],
        "github_url": "https://github.com/assistant-ui/assistant-ui",
        "meta_title": "Production Chat UI With assistant-ui + Next.js",
        "meta_description": "Streaming chat UI in Next.js: assistant-ui primitives wired to an AI SDK route proxying Anthropic. Markdown, auto-scroll, edit/branch. Key stays server-side.",
    },
    {
        "slug": "copilotkit-in-app-agent",
        "title": "In-App Copilot With CopilotKit (App-Aware Actions)",
        "tldr": "An assistant that sees app state and acts on it. CopilotKit exposes state via useCopilotReadable and registers actions via useCopilotAction, so the copilot calls your functions with rendered UI — not just chat.",
        "category": "frontend",
        "language": "typescript",
        "framework": "CopilotKit + Next.js",
        "tags": ["frontend", "copilotkit", "nextjs", "agentic", "actions"],
        "best_for_tags": ["in-app-assistant", "agentic-ui", "react"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "Embedding an assistant that reads live app state and calls your frontend functions (add/edit/filter) inside an existing React app. CopilotKit handles state exposure, action dispatch, and the chat popup.",
        "when_not_to_use": "Skip if you only need a standalone chat window with no app-state awareness (assistant-ui or a plain AI SDK chat is lighter). Skip for purely server-side agent loops with no UI.",
        "quick_start": "npm i @copilotkit/react-core @copilotkit/react-ui @copilotkit/runtime",
        "full_code": '''// ============================================================
// FILE 1: app/api/copilotkit/route.ts  (server — runtime endpoint)
// ============================================================
import {
  CopilotRuntime,
  AnthropicAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import Anthropic from "@anthropic-ai/sdk";

export const runtime = "nodejs";

// AnthropicAdapter wraps the Anthropic SDK for the CopilotKit runtime.
// Docs: https://docs.copilotkit.ai/reference/classes/llm-adapters/AnthropicAdapter
const serviceAdapter = new AnthropicAdapter({
  anthropic: new Anthropic(),       // reads ANTHROPIC_API_KEY from the env
  model: "claude-sonnet-4-5",
});

export const POST = async (req: Request) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime: new CopilotRuntime(),
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });
  return handleRequest(req);
};

// ============================================================
// FILE 2: app/page.tsx  (client — provider + readable + action)
// ============================================================
"use client";

import { useState } from "react";
import { CopilotKit, useCopilotReadable, useCopilotAction } from "@copilotkit/react-core";
import { CopilotPopup } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";

type Todo = { id: number; text: string; done: boolean };

function TodoApp() {
  const [todos, setTodos] = useState<Todo[]>([]);

  // Expose live state to the copilot so it can reason over current todos.
  useCopilotReadable({ description: "The current todo list", value: todos });

  // Register a frontend action the copilot can call.
  useCopilotAction({
    name: "addTodo",
    description: "Add a new todo item to the list.",
    parameters: [
      { name: "text", type: "string", description: "The todo text", required: true },
    ],
    handler: async ({ text }) => {
      // Idempotency guard: a retried call must not duplicate state.
      setTodos((prev) =>
        prev.some((t) => t.text === text)
          ? prev
          : [...prev, { id: Date.now(), text, done: false }],
      );
    },
  });

  return (
    <main style={{ maxWidth: 560, margin: "2rem auto" }}>
      <h1>Todos</h1>
      <ul>
        {todos.map((t) => (
          <li key={t.id}>{t.text}</li>
        ))}
      </ul>
    </main>
  );
}

export default function Page() {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit">
      <TodoApp />
      <CopilotPopup labels={{ title: "Assistant", initial: "Try: add 'buy milk'" }} />
    </CopilotKit>
  );
}
''',
        "dependencies": [
            {"name": "@copilotkit/react-core", "version": "^1.5", "purpose": "CopilotKit provider, useCopilotReadable, useCopilotAction"},
            {"name": "@copilotkit/react-ui", "version": "^1.5", "purpose": "CopilotPopup / CopilotSidebar chat UI"},
            {"name": "@copilotkit/runtime", "version": "^1.5", "purpose": "Server runtime + AnthropicAdapter + Next.js endpoint"},
            {"name": "@anthropic-ai/sdk", "version": "^0.40", "purpose": "Anthropic client used by the adapter"},
            {"name": "next", "version": "^15.0", "purpose": "App Router + route handlers"},
        ],
        "env_vars": [
            {"name": "ANTHROPIC_API_KEY", "required": True, "description": "Server-side key read by the Anthropic client inside the runtime route.", "example": "sk-ant-..."},
        ],
        "setup_steps": [
            "npx create-next-app@latest my-copilot (App Router, TypeScript)",
            "npm i @copilotkit/react-core @copilotkit/react-ui @copilotkit/runtime @anthropic-ai/sdk",
            "Add ANTHROPIC_API_KEY to .env.local",
            "Create app/api/copilotkit/route.ts and app/page.tsx from full_code",
            "npm run dev, open the popup, and ask it to add a todo",
        ],
        "variations": [
            {"label": "Generative UI in an action", "description": "Render a component while/after the action runs.", "code_snippet": "useCopilotAction({ name: 'addTodo', parameters: [{ name: 'text', type: 'string' }], render: ({ args }) => <TodoChip text={args.text} />, handler });"},
            {"label": "CoAgents (LangGraph backend)", "description": "Drive a stateful backend agent instead of single actions.", "code_snippet": "// Use @copilotkit/react-core useCoAgent + a LangGraph agent registered on the runtime. Docs: docs.copilotkit.ai/coagents"},
            {"label": "Confirm before mutating", "description": "Gate a destructive action behind human approval.", "code_snippet": "handler: async ({ id }) => { if (!confirm('Delete this item?')) return 'cancelled'; remove(id); }"},
        ],
        "common_errors": [
            {"error_text": "Retried action duplicates state", "cause": "The handler isn't idempotent, so a re-dispatched tool call adds the item twice.", "fix_snippet": "Guard inside the handler (dedupe by a natural key or id) as in addTodo, so repeats are no-ops."},
            {"error_text": "Copilot reasons over stale data", "cause": "A non-reactive snapshot was passed to useCopilotReadable.", "fix_snippet": "Pass the live state value (the useState variable). CopilotKit re-syncs the readable whenever it changes."},
            {"error_text": "Calls 404 / copilot can't reach the runtime", "cause": "runtimeUrl doesn't match the route path.", "fix_snippet": "Keep <CopilotKit runtimeUrl='/api/copilotkit'> identical to the endpoint folder app/api/copilotkit/route.ts."},
            {"error_text": "Build error: server module in client bundle", "cause": "@copilotkit/runtime was imported into a client component.", "fix_snippet": "Import @copilotkit/runtime only in the route handler. Client components import react-core / react-ui."},
        ],
        "production_checklist": [
            "Keep runtimeUrl and the route folder path identical.",
            "Make every action handler idempotent so retries don't duplicate state.",
            "Pass live (reactive) values to useCopilotReadable, not snapshots.",
            "Import @copilotkit/runtime only on the server route.",
            "Gate destructive actions behind a confirm step before they mutate data.",
            "Pin @copilotkit/* versions together; core/ui/runtime must match.",
        ],
        "tested_with": {
            "model_versions": ["claude-sonnet-4-5"],
            "library_versions": ["@copilotkit/react-core@1.5", "@copilotkit/react-ui@1.5", "@copilotkit/runtime@1.5", "@anthropic-ai/sdk@0.40", "next@15.0"],
            "last_verified_date": "2026-06-10",
        },
        "related_tool_slugs": ["copilotkit", "vercel-ai-sdk"],
        "related_glossary_slugs": ["tool-use", "agentic-ai", "function-calling", "hitl"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "CopilotKit vs a plain chat widget?", "answer": "A chat widget only talks. CopilotKit makes the assistant app-aware: useCopilotReadable feeds it live state and useCopilotAction lets it call your functions with rendered UI. So it can actually add a task or filter a list, not just describe how."},
            {"question": "How does the model call my function?", "answer": "Each useCopilotAction registers a tool (name + typed parameters) with the runtime. The model emits a tool call, the runtime dispatches it to your handler in the browser, and the result feeds back into the conversation — standard function calling with the UI wired up."},
            {"question": "Why must the handler be idempotent?", "answer": "Tool calls can be retried (network hiccup, model re-issue). If the handler appends blindly, a retry duplicates the item. Dedupe by id or natural key so a repeated call is a safe no-op."},
            {"question": "Where does the API key live?", "answer": "Server-side only. The Anthropic client and adapter run inside app/api/copilotkit/route.ts; the browser talks to that route via runtimeUrl and never sees the key."},
        ],
        "github_url": "https://github.com/CopilotKit/CopilotKit",
        "meta_title": "In-App Copilot With CopilotKit + Next.js",
        "meta_description": "Add an app-aware copilot: useCopilotReadable exposes state, useCopilotAction registers actions the model calls with rendered UI. Anthropic adapter, server-side.",
    },
    {
        "slug": "generative-ui-ai-sdk-rsc",
        "title": "Generative UI: Stream React Components From Tool Calls (AI SDK RSC)",
        "tldr": "The model returns UI, not just text. With the AI SDK's streamUI, each tool call streams a real React component (a weather card, a chart) into the conversation — text where text fits, components where structure fits.",
        "category": "frontend",
        "language": "typescript",
        "framework": "Vercel AI SDK RSC + Next.js",
        "tags": ["frontend", "ai-sdk", "rsc", "generative-ui", "nextjs"],
        "best_for_tags": ["generative-ui", "server-actions", "react"],
        "difficulty_tier": "advanced",
        "featured": False,
        "when_to_use": "You want model responses to render structured components (cards, charts, forms) instead of plain text, using App Router server actions. streamUI streams a React node per tool call with a loading state.",
        "when_not_to_use": "Skip on the Pages Router (RSC needs App Router + server actions). Skip if plain text streaming is enough — generative UI adds serialization-boundary complexity you don't need.",
        "quick_start": "npm i ai @ai-sdk/rsc @ai-sdk/anthropic zod",
        "full_code": '''// ============================================================
// FILE 1: app/actions.tsx  (server action — returns a React node)
// ============================================================
"use server";

import { anthropic } from "@ai-sdk/anthropic";
import { streamUI } from "@ai-sdk/rsc";
import { z } from "zod";

// Stand-in data source; swap for a real API.
async function fetchWeather(city: string) {
  return { city, tempC: 21, summary: "Partly cloudy" };
}

function Spinner() {
  return <div aria-busy="true">Loading weather…</div>;
}

function WeatherCard({ city, tempC, summary }: { city: string; tempC: number; summary: string }) {
  return (
    <div style={{ border: "1px solid #ddd", borderRadius: 12, padding: 16 }}>
      <strong>{city}</strong>
      <div>{tempC}°C — {summary}</div>
    </div>
  );
}

export async function askWeather(prompt: string) {
  // streamUI streams text for prose and a component per matched tool call.
  // Docs: https://sdk.vercel.ai/docs/ai-sdk-rsc/streaming-react-components
  const result = await streamUI({
    model: anthropic("claude-sonnet-4-5"),
    prompt,
    text: ({ content }) => <p>{content}</p>,
    tools: {
      getWeather: {
        description: "Show current weather for a city as a card.",
        parameters: z.object({ city: z.string().describe("City name") }),
        generate: async function* ({ city }) {
          yield <Spinner />;                 // loading state first, or the UI hangs
          const data = await fetchWeather(city);
          return <WeatherCard {...data} />;  // final component replaces the spinner
        },
      },
    },
  });

  return result.value; // a serializable React node
}

// ============================================================
// FILE 2: app/page.tsx  (client — calls the action, renders the node)
// ============================================================
"use client";

import { useState, type ReactNode } from "react";
import { askWeather } from "./actions";

export default function Page() {
  const [ui, setUi] = useState<ReactNode>(null);
  const [pending, setPending] = useState(false);

  async function onAsk() {
    setPending(true);
    try {
      setUi(await askWeather("What's the weather in Lisbon?"));
    } finally {
      setPending(false);
    }
  }

  return (
    <main style={{ maxWidth: 560, margin: "2rem auto" }}>
      <button onClick={onAsk} disabled={pending}>
        {pending ? "Asking…" : "Ask the weather"}
      </button>
      <div style={{ marginTop: 16 }}>{ui}</div>
    </main>
  );
}
''',
        "dependencies": [
            {"name": "ai", "version": "^4.0", "purpose": "Vercel AI SDK core"},
            {"name": "@ai-sdk/rsc", "version": "^1.0", "purpose": "streamUI + RSC streaming of React components"},
            {"name": "@ai-sdk/anthropic", "version": "^1.0", "purpose": "Anthropic model provider"},
            {"name": "zod", "version": "^3.23", "purpose": "Typed tool parameter schemas"},
            {"name": "next", "version": "^15.0", "purpose": "App Router + server actions (required for RSC)"},
        ],
        "env_vars": [
            {"name": "ANTHROPIC_API_KEY", "required": True, "description": "Server-side key read by @ai-sdk/anthropic inside the server action.", "example": "sk-ant-..."},
        ],
        "setup_steps": [
            "npx create-next-app@latest my-genui (App Router, TypeScript)",
            "npm i ai @ai-sdk/rsc @ai-sdk/anthropic zod",
            "Add ANTHROPIC_API_KEY to .env.local",
            "Create app/actions.tsx ('use server') and app/page.tsx from full_code",
            "npm run dev and click 'Ask the weather'",
        ],
        "variations": [
            {"label": "Multiple tools, distinct components", "description": "Each tool renders its own component.", "code_snippet": "tools: { getWeather: { /* ... */ }, getStock: { parameters: z.object({ ticker: z.string() }), generate: async function* ({ ticker }) { yield <Spinner />; return <StockCard {...await fetchStock(ticker)} />; } } }"},
            {"label": "Persist + restore the UI tree", "description": "Serialize tool results, re-render later.", "code_snippet": "// Store { tool: 'getWeather', args, data } per turn; on reload, map saved results back to <WeatherCard /> to rebuild the thread."},
            {"label": "Fall back to text", "description": "When no tool matches, stream prose.", "code_snippet": "text: ({ content }) => <p>{content}</p>  // already the default; the model streams text when no tool fits"},
        ],
        "common_errors": [
            {"error_text": "streamUI / ai-rsc imports fail or error at runtime", "cause": "Used on the Pages Router, which has no server actions.", "fix_snippet": "RSC generative UI needs the App Router. Put the action under app/ with 'use server' and call it from an App Router page."},
            {"error_text": "Error serializing props / 'Functions cannot be passed to Client Components'", "cause": "A component with non-serializable props crossed the server/client boundary.", "fix_snippet": "Mark interactive leaves 'use client' and pass only serializable props (strings, numbers, plain objects) across the boundary."},
            {"error_text": "UI hangs with no feedback during fetch", "cause": "The generator returned without yielding a loading state.", "fix_snippet": "yield <Spinner /> before the await, then return the final component. The first yield renders immediately."},
            {"error_text": "Payload huge / slow render", "cause": "Large objects serialized across the boundary as props.", "fix_snippet": "Pass ids, not blobs. Fetch heavy data inside the component (a client component) instead of serializing it through props."},
        ],
        "production_checklist": [
            "Use the App Router with 'use server' actions; RSC generative UI requires it.",
            "Yield a loading state before any await inside generate().",
            "Pass only serializable props across the server/client boundary.",
            "Mark interactive component leaves 'use client'.",
            "Validate tool parameters with zod and describe each field for the model.",
            "Pin ai / @ai-sdk/rsc versions; the RSC API surface still changes.",
        ],
        "tested_with": {
            "model_versions": ["claude-sonnet-4-5"],
            "library_versions": ["ai@4.0", "@ai-sdk/rsc@1.0", "@ai-sdk/anthropic@1.0", "zod@3.23", "next@15.0"],
            "last_verified_date": "2026-06-10",
        },
        "related_tool_slugs": ["vercel-ai-sdk"],
        "related_glossary_slugs": ["tool-use", "streaming", "structured-output", "function-calling"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "What is generative UI?", "answer": "Instead of the model returning only text, a tool call returns a rendered React component. streamUI streams text for prose and a component (weather card, chart) where structured output reads better, mixing both in one response."},
            {"question": "streamUI vs streamText + custom rendering?", "answer": "streamText gives you a token stream you parse and render yourself. streamUI streams the component directly from the server action via RSC, including an async-generator loading state, so you skip the client-side tool-result-to-UI plumbing."},
            {"question": "Why does it need the App Router?", "answer": "@ai-sdk/rsc streams React Server Components from a 'use server' action, a mechanism that only exists in the App Router. On the Pages Router there are no server actions, so streamUI has nothing to stream through."},
            {"question": "Why yield a spinner before awaiting?", "answer": "generate() is an async generator: the first yield renders immediately, so the user sees a loading state while the await (the data fetch) runs. Without it the UI shows nothing until the component is fully ready."},
        ],
        "github_url": "https://github.com/vercel/ai",
        "meta_title": "Generative UI With AI SDK RSC + Next.js",
        "meta_description": "Stream React components from tool calls with the AI SDK's streamUI: a component per tool, zod-typed params, async loading state. App Router server actions.",
    },
]
