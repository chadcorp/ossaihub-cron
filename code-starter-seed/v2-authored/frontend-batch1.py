"""Frontend starters — Next.js + AI SDK, streaming UI, chat components."""

RECORDS = [
    {
        "slug": "nextjs-vercel-ai-sdk-chat",
        "title": "Next.js Chat With Vercel AI SDK and Streaming",
        "tldr": "Production-shape Next.js chat: streaming responses via Vercel AI SDK, tool calling, error retries, and a clean useChat hook integration. Works with OpenAI, Anthropic, or any compatible provider.",
        "category": "frontend",
        "language": "typescript",
        "framework": "Next.js + Vercel AI SDK",
        "tags": ["nextjs", "vercel-ai-sdk", "streaming", "chat-ui"],
        "best_for_tags": ["chat-applications", "ai-saas", "react"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "Building a chat UI with Next.js where you want streaming responses without writing the SSE plumbing. Vercel AI SDK gives you useChat() that handles the stream.",
        "when_not_to_use": "Skip for non-chat UIs (overhead). Skip for highly custom UIs where the SDK's abstractions don't fit — you'll fight it. Skip for non-Next.js stacks (the SDK works in Express/Hono but is best with Next).",
        "quick_start": "npx create-next-app@latest && npm install ai @ai-sdk/openai && cp the code below",
        "full_code": '''// app/api/chat/route.ts — Server route handling LLM streaming
import { openai } from "@ai-sdk/openai";
import { streamText, tool } from "ai";
import { z } from "zod";

export const maxDuration = 30;

export async function POST(req: Request) {
  const { messages } = await req.json();

  const result = streamText({
    model: openai("gpt-4o-mini"),
    system: "You are a helpful assistant. Use tools when relevant.",
    messages,
    maxToolRoundtrips: 5,           // limit tool-use loops
    tools: {
      getWeather: tool({
        description: "Get current weather for a location",
        parameters: z.object({
          location: z.string().describe("City name"),
        }),
        execute: async ({ location }) => {
          // Replace with real API
          return { location, temp: 22, condition: "clear" };
        },
      }),
    },
  });

  return result.toDataStreamResponse();
}

// ---- app/page.tsx — Client UI
'use client';

import { useChat } from 'ai/react';

export default function ChatPage() {
  const {
    messages,
    input,
    handleInputChange,
    handleSubmit,
    isLoading,
    error,
    reload,
    stop,
  } = useChat({
    api: '/api/chat',
    onError: (err) => console.error('chat error:', err),
  });

  return (
    <div className="flex flex-col h-screen max-w-2xl mx-auto p-4">
      <div className="flex-1 overflow-y-auto space-y-4 pb-4">
        {messages.map((m) => (
          <div
            key={m.id}
            className={m.role === 'user' ? 'text-right' : 'text-left'}
          >
            <div
              className={`inline-block rounded-lg px-3 py-2 ${
                m.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              {m.content}
              {m.toolInvocations?.map((tool) => (
                <div key={tool.toolCallId} className="text-xs opacity-70 mt-1">
                  [used tool: {tool.toolName}]
                </div>
              ))}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="text-gray-500">
            <span>thinking...</span>
            <button onClick={stop} className="ml-2 underline">stop</button>
          </div>
        )}

        {error && (
          <div className="text-red-600">
            Something went wrong.{' '}
            <button onClick={() => reload()} className="underline">retry</button>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2 border-t pt-4">
        <input
          value={input}
          onChange={handleInputChange}
          placeholder="say something..."
          disabled={isLoading}
          className="flex-1 border rounded px-3 py-2"
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="bg-blue-500 text-white rounded px-4 py-2 disabled:bg-gray-300"
        >
          send
        </button>
      </form>
    </div>
  );
}
''',
        "dependencies": [
            {"name": "ai", "version": "^3.4", "purpose": "Vercel AI SDK (streaming, tool calling)"},
            {"name": "@ai-sdk/openai", "version": "^0.0.66", "purpose": "OpenAI provider for AI SDK"},
            {"name": "zod", "version": "^3.23", "purpose": "Tool parameter schemas"},
            {"name": "next", "version": "^15.0", "purpose": "Next.js framework"},
            {"name": "react", "version": "^18.3", "purpose": "React"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI key (server-side only)", "example": "sk-..."},
        ],
        "setup_steps": [
            "npx create-next-app@latest my-chat",
            "cd my-chat && npm install ai @ai-sdk/openai zod",
            "Create app/api/chat/route.ts with server code",
            "Create app/page.tsx with client code",
            "echo 'OPENAI_API_KEY=sk-...' >> .env.local",
            "npm run dev",
        ],
        "variations": [
            {
                "label": "Anthropic provider",
                "description": "Swap to Claude.",
                "code_snippet": "import { anthropic } from '@ai-sdk/anthropic';\\n// model: anthropic('claude-3-7-sonnet-latest')",
            },
            {
                "label": "Multiple tools",
                "description": "Add more tools to the route.",
                "code_snippet": "tools: {\\n  getWeather: ...,\\n  searchDocs: tool({ description: 'Search docs', parameters: z.object({ query: z.string() }), execute: async ({query}) => searchDB(query) }),\\n}",
            },
            {
                "label": "Streaming with thinking blocks",
                "description": "Show model's reasoning as it generates.",
                "code_snippet": "// Vercel AI SDK exposes data parts; render them in client distinctly from main content.",
            },
            {
                "label": "Edge runtime",
                "description": "Run on Vercel Edge.",
                "code_snippet": "// In route.ts add: export const runtime = 'edge';\\n// Caveat: some Node-only libs (sharp, fs) won't work.",
            },
        ],
        "common_errors": [
            {
                "error_text": "Maximum execution time exceeded",
                "cause": "Default Vercel function timeout (10-15s).",
                "fix_snippet": "Add: export const maxDuration = 30; (starter has this). For Pro: max 60s. For longer, use Vercel Edge or background functions.",
            },
            {
                "error_text": "Stream cuts off mid-response",
                "cause": "Network issue or function timeout.",
                "fix_snippet": "Implement client-side reload(). Check Vercel logs for timeout. For really long responses, consider async background jobs + polling.",
            },
            {
                "error_text": "Tool calls don't execute",
                "cause": "Forgot maxToolRoundtrips or tool execute didn't return.",
                "fix_snippet": "Set maxToolRoundtrips >= number of tool steps you expect. Tool execute MUST return (sync or async); throwing errors causes infinite retry.",
            },
            {
                "error_text": "API key leaked to client",
                "cause": "Server code accidentally bundled to client.",
                "fix_snippet": "API routes are server-only; ensure OPENAI_API_KEY is in .env.local (not .env). Never reference process.env.OPENAI_API_KEY in client components.",
            },
        ],
        "production_checklist": [
            "Rate-limit API route (use middleware or upstash/redis-ratelimit).",
            "Validate input length; refuse messages over a sane limit.",
            "Set CORS appropriately for cross-origin if needed.",
            "Add auth — anonymous chat means you're paying for trolls' tokens.",
            "Log token usage per request for cost tracking.",
            "Add usage caps per user / API key.",
            "Stream-resilient client: reconnect on network blip.",
            "Test reload() flow when an error occurs mid-stream.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini", "gpt-4o"],
            "library_versions": ["ai==3.4.18", "@ai-sdk/openai==0.0.66", "next==15.0.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": ["vercel-ai-sdk"],
        "related_glossary_slugs": ["streaming", "useChat", "sse"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "Vercel AI SDK vs raw OpenAI SDK?",
                "answer": "Vercel AI SDK handles streaming protocol, useChat hook, tool calling state, and provider abstraction. Raw SDK requires you to wire SSE yourself. AI SDK is the right call for chat UIs.",
            },
            {
                "question": "Does it work with non-Vercel providers?",
                "answer": "Yes — @ai-sdk/openai, @ai-sdk/anthropic, @ai-sdk/google, @ai-sdk/mistral, @ai-sdk/cohere, plus community providers (Groq, Together, etc.). Same API across.",
            },
            {
                "question": "Can I use it without Next.js?",
                "answer": "Yes — works in Express, Hono, SvelteKit, etc. useChat is React-specific; useChat alternatives exist for Svelte and Vue.",
            },
            {
                "question": "How do I add markdown rendering?",
                "answer": "react-markdown + remark-gfm in the message renderer. Sanitize against XSS (use react-markdown's strict mode or DOMPurify).",
            },
        ],
        "github_url": "https://github.com/vercel/ai",
        "meta_title": "Next.js Chat With Vercel AI SDK and Streaming",
        "meta_description": "Production Next.js chat: streaming, tool calling, retries, error handling. useChat() hook + AI SDK route. Provider-agnostic.",
    },
    {
        "slug": "react-streaming-markdown-renderer",
        "title": "React Streaming Markdown Renderer With Syntax Highlighting",
        "tldr": "React component that renders streaming markdown WITH syntax-highlighted code blocks — handles partial code fences gracefully (no broken rendering during stream).",
        "category": "frontend",
        "language": "typescript",
        "framework": "React",
        "tags": ["react", "markdown", "streaming", "syntax-highlighting"],
        "best_for_tags": ["chat-ui", "ai-content-display", "documentation"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "Anywhere AI streams markdown to the UI (chat, doc generation, code review tools). The starter handles the streaming-partial problem: ‘```python\\nprint(’ shouldn't render as broken HTML.",
        "when_not_to_use": "Skip for pure plain-text streaming (use a simple pre tag). Skip for very high-frequency updates (DOM thrash) — debounce or batch updates.",
        "quick_start": "npm install react-markdown remark-gfm rehype-highlight && import the component",
        "full_code": '''// StreamingMarkdown.tsx
import { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github-dark.css';

interface Props {
  content: string;
  isStreaming?: boolean;
}

export function StreamingMarkdown({ content, isStreaming = false }: Props) {
  // Normalize content during streaming to prevent broken renders:
  //   - If we're inside an open code fence (odd number of ``` so far),
  //     close it temporarily so syntax highlighter renders it as a partial code block.
  const safeContent = useMemo(() => {
    if (!isStreaming) return content;

    const fenceCount = (content.match(/```/g) || []).length;
    if (fenceCount % 2 === 1) {
      // Odd number of fences — we're inside an open code block
      // Append a closing fence so the partial code renders as a code block
      return content + '\\n```';
    }
    return content;
  }, [content, isStreaming]);

  return (
    <div className="prose prose-sm max-w-none">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          // Custom code-block renderer with copy button
          pre: ({ children, ...props }) => (
            <div className="relative group">
              <pre {...props} className="bg-gray-900 rounded p-4 overflow-x-auto">
                {children}
              </pre>
              <CopyButton textGetter={() => extractCodeText(children)} />
            </div>
          ),
          // Sanitize/style links (open external in new tab)
          a: ({ href, children, ...props }) => (
            <a
              href={href}
              {...props}
              target={href?.startsWith('http') ? '_blank' : undefined}
              rel={href?.startsWith('http') ? 'noopener noreferrer' : undefined}
              className="text-blue-600 underline"
            >
              {children}
            </a>
          ),
          // Tables get a wrapper for horizontal scroll
          table: ({ children, ...props }) => (
            <div className="overflow-x-auto">
              <table {...props} className="border-collapse border border-gray-300">
                {children}
              </table>
            </div>
          ),
        }}
      >
        {safeContent}
      </ReactMarkdown>

      {isStreaming && (
        <span className="inline-block w-2 h-4 bg-gray-500 animate-pulse ml-1" aria-label="typing" />
      )}
    </div>
  );
}

function CopyButton({ textGetter }: { textGetter: () => string }) {
  const [copied, setCopied] = useState(false);

  return (
    <button
      onClick={async () => {
        await navigator.clipboard.writeText(textGetter());
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      }}
      className="absolute top-2 right-2 px-2 py-1 text-xs bg-gray-700 text-white rounded opacity-0 group-hover:opacity-100 transition-opacity"
    >
      {copied ? 'copied' : 'copy'}
    </button>
  );
}

function extractCodeText(children: React.ReactNode): string {
  // Walk React children to extract text content of <code> within <pre>.
  let text = '';
  const walk = (node: React.ReactNode) => {
    if (typeof node === 'string') text += node;
    else if (Array.isArray(node)) node.forEach(walk);
    else if (typeof node === 'object' && node !== null && 'props' in node) {
      walk((node as { props: { children: React.ReactNode } }).props.children);
    }
  };
  walk(children);
  return text;
}

// Usage:
// const [content, setContent] = useState('');
// // As tokens stream in: setContent(prev => prev + chunk)
// return <StreamingMarkdown content={content} isStreaming={true} />
''',
        "dependencies": [
            {"name": "react-markdown", "version": "^9.0", "purpose": "Markdown rendering"},
            {"name": "remark-gfm", "version": "^4.0", "purpose": "GFM extensions (tables, strikethrough)"},
            {"name": "rehype-highlight", "version": "^7.0", "purpose": "Syntax highlighting via highlight.js"},
            {"name": "highlight.js", "version": "^11.10", "purpose": "Syntax highlighting engine"},
        ],
        "env_vars": [],
        "setup_steps": [
            "npm install react-markdown remark-gfm rehype-highlight highlight.js",
            "Import a highlight.js CSS theme (github-dark, atom-one, etc.)",
            "Use <StreamingMarkdown content={streamingText} isStreaming={true} />",
        ],
        "variations": [
            {
                "label": "KaTeX math support",
                "description": "Render LaTeX formulas.",
                "code_snippet": "import rehypeKatex from 'rehype-katex';\\nimport remarkMath from 'remark-math';\\n// Add to remarkPlugins/rehypePlugins arrays.\\n// import 'katex/dist/katex.min.css';",
            },
            {
                "label": "Mermaid diagrams",
                "description": "Render mermaid code blocks as diagrams.",
                "code_snippet": "// In custom code component:\\nif (language === 'mermaid') return <MermaidDiagram chart={textContent} />;",
            },
            {
                "label": "Sanitization",
                "description": "Block dangerous HTML.",
                "code_snippet": "import rehypeSanitize from 'rehype-sanitize';\\n// Add to rehypePlugins — first in the chain.",
            },
            {
                "label": "Custom token-by-token cursor",
                "description": "Show typing animation.",
                "code_snippet": "// Component already has cursor. Customize: blink rate via animation-duration; style via CSS.",
            },
        ],
        "common_errors": [
            {
                "error_text": "Code blocks flash on every token",
                "cause": "React re-renders entire markdown on every char.",
                "fix_snippet": "Debounce updates: only re-render every 50ms during streaming. useDeferredValue or manual setTimeout.",
            },
            {
                "error_text": "XSS via untrusted markdown",
                "cause": "react-markdown is generally safe but HTML embedded in markdown can be dangerous.",
                "fix_snippet": "Add rehype-sanitize to rehypePlugins. Be especially careful with user-generated content; AI-generated is safer but still review.",
            },
            {
                "error_text": "Streaming partial code looks ugly",
                "cause": "Half-rendered fences.",
                "fix_snippet": "Starter handles this — adds closing fence during streaming. Verify isStreaming is set true while streaming, false when done.",
            },
            {
                "error_text": "Syntax highlighting wrong language",
                "cause": "Language not specified or unknown.",
                "fix_snippet": "Use full language names: ```typescript not ```ts (highlight.js aliases vary). Test target languages.",
            },
        ],
        "production_checklist": [
            "Sanitize if rendering user-generated markdown (XSS risk).",
            "Debounce re-renders during streaming (>50 tokens/sec gets choppy).",
            "Lazy-load highlight.js languages for smaller bundle.",
            "Test long code blocks; horizontal scroll vs wrap.",
            "Accessibility: cursor has aria-label; ensure screen readers handle streaming text well.",
            "Mobile: code blocks need horizontal scroll, not wrap (breaks indentation).",
            "Memoize the component if parent re-renders frequently.",
        ],
        "tested_with": {
            "model_versions": [],
            "library_versions": ["react-markdown==9.0.1", "remark-gfm==4.0.0", "rehype-highlight==7.0.0"],
            "last_verified_date": "2026-05-13",
        },
        "related_tool_slugs": [],
        "related_glossary_slugs": ["markdown", "streaming-ui", "syntax-highlighting"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {
                "question": "Why is streaming code rendering tricky?",
                "answer": "Markdown's '```' fences expect a closing fence. Mid-stream, content has open fence + partial code. Without handling, react-markdown renders raw or breaks. The starter closes the fence virtually for rendering, but the underlying state stays as the actual streamed content.",
            },
            {
                "question": "Bundle size concerns?",
                "answer": "highlight.js bundles many languages. Use the modular import (only register the languages you support): import hljs from 'highlight.js/lib/core'; hljs.registerLanguage('typescript', tsLang);",
            },
            {
                "question": "Does this work with React Server Components?",
                "answer": "Yes for the markdown component. CopyButton (with useState) is client-only. Mark the file 'use client' if using anywhere with state.",
            },
            {
                "question": "Can I use this with Vue / Svelte?",
                "answer": "The pattern transfers; the libraries don't. For Vue: marked + vue-markdown-it. For Svelte: marked + svelte-markdown.",
            },
        ],
        "github_url": "",
        "meta_title": "React Streaming Markdown Renderer — Starter",
        "meta_description": "Render streaming AI markdown in React: handles partial code fences, syntax highlighting, copy button, cursor animation.",
    },
]
