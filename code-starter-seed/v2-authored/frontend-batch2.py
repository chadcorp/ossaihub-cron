"""Frontend starters — batch 2: Next.js AI SDK chat, Streamlit chat, Vercel AI SDK with tools."""

RECORDS = [
    {
        "slug": "nextjs-ai-sdk-chat-streaming",
        "title": "Next.js + Vercel AI SDK Chat With Streaming",
        "tldr": "Next.js 15 App Router + Vercel AI SDK 5: streaming chat UI in 100 lines. Provider-agnostic, server actions, type-safe tool calling. Production-grade frontend.",
        "category": "frontend",
        "language": "typescript",
        "framework": "Next.js + Vercel AI SDK",
        "tags": ["nextjs", "ai-sdk", "vercel", "streaming"],
        "best_for_tags": ["typescript-stack", "vercel-hosting", "saas-apps"],
        "difficulty_tier": "intermediate",
        "featured": True,
        "when_to_use": "Building a customer-facing chat product on Next.js. Vercel AI SDK + useChat hook handles streaming, conversation state, tool calls. Production-grade out of the box.",
        "when_not_to_use": "Skip for non-Next.js apps (use AI SDK directly with React Native / SvelteKit / Vue adapters). Skip for batch inference (server actions or worker queue).",
        "quick_start": "npx create-next-app@latest && npm i ai @ai-sdk/openai && code .",
        "full_code": '''/**
 * Next.js 15 + Vercel AI SDK 5: streaming chat with tools.
 *
 * Files:
 *   app/page.tsx           <- client component with useChat
 *   app/api/chat/route.ts  <- streaming chat endpoint
 */

// =============== app/api/chat/route.ts ===============
import { openai } from "@ai-sdk/openai";
import { streamText, tool } from "ai";
import { z } from "zod";

export const maxDuration = 60;

export async function POST(req: Request) {
  const { messages } = await req.json();

  const result = streamText({
    model: openai("gpt-4o-mini"),
    system: "You are a helpful assistant. Use the search tool when asked about current events.",
    messages,
    tools: {
      search: tool({
        description: "Search the web for current information.",
        parameters: z.object({
          query: z.string().describe("The search query"),
        }),
        execute: async ({ query }) => {
          // Replace with real search API
          return { results: [`Stub result for: ${query}`] };
        },
      }),
      getCurrentTime: tool({
        description: "Get current UTC time.",
        parameters: z.object({}),
        execute: async () => ({ time: new Date().toISOString() }),
      }),
    },
    maxSteps: 5, // allow multi-turn tool calling
  });

  return result.toDataStreamResponse();
}


// =============== app/page.tsx ===============
"use client";

import { useChat } from "ai/react";

export default function Page() {
  const { messages, input, handleInputChange, handleSubmit, isLoading, stop, error } =
    useChat({
      api: "/api/chat",
      onError: (err) => console.error("Chat error:", err),
    });

  return (
    <div className="max-w-3xl mx-auto p-6 flex flex-col h-screen">
      <h1 className="text-2xl font-bold mb-4">AI Chat</h1>

      <div className="flex-1 overflow-y-auto space-y-4 mb-4">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`p-3 rounded ${m.role === "user" ? "bg-blue-100 ml-12" : "bg-gray-100 mr-12"}`}
          >
            <div className="text-xs text-gray-500 mb-1">{m.role}</div>
            <div className="whitespace-pre-wrap">{m.content}</div>

            {/* Show tool invocations */}
            {m.toolInvocations?.map((ti, i) => (
              <div key={i} className="mt-2 text-xs bg-yellow-50 p-2 rounded">
                <code>{ti.toolName}({JSON.stringify(ti.args)})</code>
                {ti.state === "result" && (
                  <pre className="mt-1">{JSON.stringify(ti.result, null, 2)}</pre>
                )}
              </div>
            ))}
          </div>
        ))}

        {isLoading && (
          <div className="text-sm text-gray-500 italic">
            Generating...
            <button onClick={stop} className="ml-2 underline">stop</button>
          </div>
        )}

        {error && (
          <div className="text-sm text-red-600">Error: {error.message}</div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          value={input}
          onChange={handleInputChange}
          placeholder="Ask anything..."
          className="flex-1 p-3 border rounded"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading || !input}
          className="px-6 bg-blue-600 text-white rounded disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}
''',
        "dependencies": [
            {"name": "ai", "version": ">=4.0", "purpose": "Vercel AI SDK"},
            {"name": "@ai-sdk/openai", "version": ">=1.0", "purpose": "OpenAI provider"},
            {"name": "next", "version": ">=15.0", "purpose": "Next.js"},
            {"name": "zod", "version": ">=3.23", "purpose": "Tool param schemas"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI key", "example": "sk-..."},
        ],
        "setup_steps": [
            "npx create-next-app@latest my-chat (TypeScript + App Router)",
            "cd my-chat && npm i ai @ai-sdk/openai zod",
            "Create app/api/chat/route.ts + app/page.tsx",
            "export OPENAI_API_KEY=sk-... (or add to .env.local)",
            "npm run dev → http://localhost:3000",
        ],
        "variations": [
            {"label": "Anthropic provider", "description": "Swap to Claude.", "code_snippet": "import { anthropic } from '@ai-sdk/anthropic';\\nmodel: anthropic('claude-3-5-sonnet-latest')"},
            {"label": "Persisted conversation", "description": "Save messages to DB.", "code_snippet": "// onFinish: save messages to DB. useChat({ initialMessages: <load from DB> }) restores."},
            {"label": "Generative UI", "description": "Stream React components.", "code_snippet": "// Use streamUI from 'ai/rsc'; tools can return JSX. Renders rich UI server-side during streaming."},
        ],
        "common_errors": [
            {"error_text": "useChat not streaming", "cause": "Wrong return type from route handler.", "fix_snippet": "Use result.toDataStreamResponse() (not toTextStreamResponse for useChat). They send different formats."},
            {"error_text": "Tool not invoked", "cause": "Description too vague.", "fix_snippet": "Improve tool descriptions: 'Search the web' beats 'Search'. LLM reads descriptions to decide when to use tools."},
            {"error_text": "Hydration mismatch", "cause": "Messages rendered server vs client differently.", "fix_snippet": "Keep messages state client-only. Don't try to SSR the chat list. Initial empty state is fine."},
            {"error_text": "maxDuration exceeded on Vercel", "cause": "Long tool chains.", "fix_snippet": "Vercel Hobby: 10s. Pro: 60s. Increase maxDuration; for >60s, use Vercel Functions Pro tier or alternative hosting."},
        ],
        "production_checklist": [
            "Use App Router (Pages Router lacks streaming features).",
            "Add rate limiting via middleware (per-IP / per-user).",
            "Persist messages to DB on onFinish.",
            "Set maxDuration to match worst-case multi-step tool calls.",
            "Add user auth before allowing chat (cost protection).",
            "Use streamText (not generateText) for streaming UX.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini"],
            "library_versions": ["ai==4.0", "next==15.0"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["vercel-ai-sdk", "nextjs"],
        "related_glossary_slugs": ["server-actions", "streaming-ui"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Vercel AI SDK vs Mastra?", "answer": "Vercel AI SDK: minimal, frontend-focused, perfect for chat UIs. Mastra: full agent framework, BUILT ON top of AI SDK. Use AI SDK for chat; Mastra when you need agents + workflows."},
            {"question": "useChat options?", "answer": "Many: api, initialMessages, onFinish, onError, body (extra data), headers, sendExtraMessageFields. Check the AI SDK docs for full list."},
            {"question": "How to handle long conversations?", "answer": "Truncate or summarize older messages server-side. Or use AI SDK's experimental_useAssistant for thread-based conversations with persisted state."},
            {"question": "Mobile?", "answer": "Use React Native + @ai-sdk/react-native (experimental) or use AI SDK Core directly with custom UI. Web works in PWA mode out of the box."},
        ],
        "github_url": "https://github.com/vercel/ai",
        "meta_title": "Next.js Vercel AI SDK Chat Starter",
        "meta_description": "Next.js 15 + Vercel AI SDK 5: streaming chat UI with tools, useChat hook, server actions. Production-grade frontend.",
    },
    {
        "slug": "streamlit-llm-chat-with-memory",
        "title": "Streamlit LLM Chat With Memory + RAG",
        "tldr": "Streamlit: Python LLM apps in 50 lines. Chat memory via st.session_state, RAG via embedded vector search, file upload. Perfect for internal tools + prototypes.",
        "category": "frontend",
        "language": "python",
        "framework": "Streamlit",
        "tags": ["streamlit", "chat", "rag", "internal-tools"],
        "best_for_tags": ["internal-tools", "research-demos", "python-first-teams"],
        "difficulty_tier": "beginner",
        "featured": False,
        "when_to_use": "Internal tool or research demo where Python-first development beats JS frontend overhead. Streamlit gives you a chat UI in minutes. Easy auth via Streamlit Community Cloud.",
        "when_not_to_use": "Skip for customer-facing prod (UX limited, can't customize deeply). Skip for high-traffic (Streamlit's request-per-rerun model is slow at scale).",
        "quick_start": "pip install streamlit openai && streamlit run app.py",
        "full_code": '''"""Streamlit chat with memory + simple RAG."""
from __future__ import annotations

import os
import streamlit as st
from openai import OpenAI
import numpy as np


# ----------------- SETUP -----------------

st.set_page_config(page_title="LLM Chat", layout="wide", initial_sidebar_state="expanded")
st.title("LLM Chat with RAG")


@st.cache_resource
def get_client():
    return OpenAI(api_key=os.environ["OPENAI_API_KEY"])


client = get_client()


# ----------------- SIDEBAR (settings + uploads) -----------------

with st.sidebar:
    model = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o", "gpt-4o-2024-08-06"])
    temperature = st.slider("Temperature", 0.0, 2.0, 0.0, 0.1)
    max_tokens = st.slider("Max tokens", 64, 4096, 1024, 64)

    st.divider()
    st.subheader("Upload docs for RAG")
    files = st.file_uploader("Markdown / text files", accept_multiple_files=True, type=["md", "txt"])

    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()


# ----------------- RAG (simple in-memory) -----------------

@st.cache_data
def embed(texts: tuple[str, ...]) -> np.ndarray:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=list(texts),
    )
    return np.array([e.embedding for e in response.data])


def ingest_files(files) -> tuple[list[str], np.ndarray]:
    """Extract + chunk + embed uploaded files."""
    chunks: list[str] = []
    for f in files:
        text = f.read().decode("utf-8", errors="replace")
        # Simple chunker: 500 words per chunk
        words = text.split()
        for i in range(0, len(words), 400):
            chunks.append(" ".join(words[i:i + 500]))
    if not chunks:
        return [], np.array([])
    return chunks, embed(tuple(chunks))


def retrieve(query: str, chunks: list[str], chunk_emb: np.ndarray, k: int = 3) -> list[str]:
    """Cosine similarity retrieval."""
    q_emb = embed((query,))[0]
    sims = chunk_emb @ q_emb / (np.linalg.norm(chunk_emb, axis=1) * np.linalg.norm(q_emb))
    top_k = np.argsort(-sims)[:k]
    return [chunks[i] for i in top_k]


if files:
    if "rag_chunks" not in st.session_state or st.session_state.get("rag_files") != [f.name for f in files]:
        with st.spinner("Embedding documents..."):
            chunks, chunk_emb = ingest_files(files)
        st.session_state.rag_chunks = chunks
        st.session_state.rag_emb = chunk_emb
        st.session_state.rag_files = [f.name for f in files]
        st.sidebar.success(f"Indexed {len(chunks)} chunks from {len(files)} files")


# ----------------- CHAT MEMORY -----------------

if "messages" not in st.session_state:
    st.session_state.messages = []


# Display history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ----------------- HANDLE NEW MESSAGE -----------------

if prompt := st.chat_input("Ask anything..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Build context (RAG if files uploaded)
    system_msg = "You are a helpful assistant."
    if st.session_state.get("rag_chunks"):
        retrieved = retrieve(prompt, st.session_state.rag_chunks, st.session_state.rag_emb)
        context = "\\n\\n---\\n\\n".join(retrieved)
        system_msg = f"Answer using ONLY this context:\\n\\n{context}\\n\\nIf not in context, say so."

    api_messages = [{"role": "system", "content": system_msg}] + st.session_state.messages

    # Stream response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        stream = client.chat.completions.create(
            model=model,
            messages=api_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                full_response += delta
                message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
''',
        "dependencies": [
            {"name": "streamlit", "version": ">=1.40", "purpose": "Streamlit framework"},
            {"name": "openai", "version": ">=1.40", "purpose": "OpenAI client"},
            {"name": "numpy", "version": ">=1.26", "purpose": "Vector math for RAG"},
        ],
        "env_vars": [
            {"name": "OPENAI_API_KEY", "required": True, "description": "OpenAI key", "example": "sk-..."},
        ],
        "setup_steps": [
            "pip install streamlit openai numpy",
            "Save app.py with the code above",
            "export OPENAI_API_KEY=sk-...",
            "streamlit run app.py",
            "Browser auto-opens at http://localhost:8501",
        ],
        "variations": [
            {"label": "Deploy on Streamlit Community Cloud", "description": "Free hosting.", "code_snippet": "# Push to GitHub; connect at share.streamlit.io; secrets via dashboard. Free tier: public apps only."},
            {"label": "Use persistent vector DB", "description": "RAG that survives restarts.", "code_snippet": "# Replace in-memory embeddings with Chroma or pgvector. Survives reruns + page refreshes."},
            {"label": "Auth via streamlit-authenticator", "description": "Private apps.", "code_snippet": "# pip install streamlit-authenticator; basic-auth or OAuth. Gates app behind login."},
        ],
        "common_errors": [
            {"error_text": "App resets on every interaction", "cause": "Not using session_state.", "fix_snippet": "Streamlit re-runs the whole script per interaction. Use st.session_state for state that should persist (messages, uploaded files)."},
            {"error_text": "Streaming markdown looks broken", "cause": "Mid-stream partial markdown.", "fix_snippet": "Use st.empty() + .markdown() to overwrite cleanly. The placeholder.markdown(text + cursor) pattern in code works."},
            {"error_text": "Slow first response", "cause": "Embedding model warm-up.", "fix_snippet": "Use @st.cache_resource for client and @st.cache_data for embeddings. Streamlit caches across reruns."},
            {"error_text": "Memory grows with uploads", "cause": "Files held in session_state forever.", "fix_snippet": "Clear st.session_state.rag_chunks when user uploads new files. Pattern in code does this on filename change."},
        ],
        "production_checklist": [
            "Use @st.cache_resource for clients (OpenAI, DB).",
            "Use @st.cache_data for expensive computations (embeddings).",
            "Persist session_state to DB for multi-user.",
            "Add streamlit-authenticator for private apps.",
            "Deploy on Streamlit Community Cloud (free) or self-host.",
            "Monitor: Streamlit logs everything; pipe to Loki / Datadog.",
        ],
        "tested_with": {
            "model_versions": ["gpt-4o-mini", "text-embedding-3-small"],
            "library_versions": ["streamlit==1.40", "openai==1.51"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["streamlit"],
        "related_glossary_slugs": ["streamlit", "internal-tools"],
        "related_learn_slugs": [],
        "license": "Apache-2.0",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Streamlit vs Gradio?", "answer": "Streamlit: more flexible, better for complex layouts, slower per-interaction. Gradio: simpler, ML-demo-optimized, integrated with HF Spaces. Pick by app shape."},
            {"question": "Multi-user app on Streamlit?", "answer": "Possible but tricky — Streamlit's session model assumes single user per session. For real multi-user: external state store (Postgres / Redis) + session-tied user_id."},
            {"question": "Production traffic?", "answer": "Streamlit handles ~5-20 concurrent users per pod well. Past that: scale-out via Streamlit Cloud Enterprise or self-host with Kubernetes."},
            {"question": "Can I customize the UI?", "answer": "Within Streamlit's constraints. Custom CSS via st.markdown allows tweaks. For full pixel-perfect control, switch to Next.js / Gradio Blocks."},
        ],
        "github_url": "https://github.com/streamlit/streamlit",
        "meta_title": "Streamlit LLM Chat With RAG Starter",
        "meta_description": "Streamlit chat with memory, file upload RAG, streaming, settings sidebar. Python LLM UI in 100 lines.",
    },
    {
        "slug": "react-chat-with-anthropic",
        "title": "Pure React Chat With Anthropic Streaming",
        "tldr": "React chat without a framework — just fetch() + ReadableStream + SSE parsing. Direct Anthropic streaming endpoint. Tiny dep footprint; works in any React app.",
        "category": "frontend",
        "language": "typescript",
        "framework": "React + Anthropic",
        "tags": ["react", "anthropic", "streaming", "sse"],
        "best_for_tags": ["react-purists", "tiny-deps", "embed-in-existing-app"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "Adding chat to an existing React app without pulling in Vercel AI SDK or other heavy frameworks. Direct streaming from your backend. Minimal deps.",
        "when_not_to_use": "Skip if you have time to use Vercel AI SDK (it's well-designed). Skip for complex chat (tool calling, multi-turn) — AI SDK handles edge cases.",
        "quick_start": "Save the component + backend route into your existing React app",
        "full_code": '''/**
 * React chat with raw fetch + streaming.
 *
 * Pair with a backend route that streams Anthropic SSE.
 */
import { useState, useRef, useEffect } from "react";


// =============== Component ===============

type Message = { role: "user" | "assistant"; content: string };


export function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);


  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages]);


  async function send() {
    if (!input.trim() || isStreaming) return;
    const userMsg: Message = { role: "user", content: input };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput("");
    setIsStreaming(true);

    // Insert empty assistant placeholder; stream fills it
    setMessages([...newMessages, { role: "assistant", content: "" }]);

    abortRef.current = new AbortController();
    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: newMessages }),
        signal: abortRef.current.signal,
      });

      if (!response.ok || !response.body) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        // Parse SSE-style events (data: {...}\\n\\n)
        const lines = buffer.split("\\n\\n");
        buffer = lines.pop() || "";
        for (const line of lines) {
          if (!line.startsWith("data:")) continue;
          const payload = line.slice(5).trim();
          if (payload === "[DONE]") break;
          try {
            const event = JSON.parse(payload);
            if (event.type === "content_block_delta" && event.delta?.text) {
              setMessages((prev) => {
                const copy = [...prev];
                copy[copy.length - 1] = {
                  ...copy[copy.length - 1],
                  content: copy[copy.length - 1].content + event.delta.text,
                };
                return copy;
              });
            }
          } catch {}
        }
      }
    } catch (err: any) {
      if (err.name !== "AbortError") {
        console.error(err);
        setMessages((prev) => [...prev.slice(0, -1), { role: "assistant", content: `Error: ${err.message}` }]);
      }
    } finally {
      setIsStreaming(false);
      abortRef.current = null;
    }
  }


  function stop() {
    abortRef.current?.abort();
  }


  return (
    <div className="flex flex-col h-screen max-w-2xl mx-auto p-4">
      <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-3 mb-4">
        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
            <div className={`inline-block p-3 rounded-lg ${m.role === "user" ? "bg-blue-500 text-white" : "bg-gray-100"}`}>
              {m.content || (isStreaming && i === messages.length - 1 ? "..." : "")}
            </div>
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          disabled={isStreaming}
          className="flex-1 p-3 border rounded"
          placeholder="Type a message..."
        />
        {isStreaming ? (
          <button onClick={stop} className="px-4 bg-red-500 text-white rounded">Stop</button>
        ) : (
          <button onClick={send} disabled={!input} className="px-4 bg-blue-500 text-white rounded disabled:opacity-50">
            Send
          </button>
        )}
      </div>
    </div>
  );
}


// =============== Backend route (Node / Bun / Express) ===============
// app.post('/api/chat', async (req, res) => {
//   const Anthropic = (await import('@anthropic-ai/sdk')).default;
//   const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
//
//   res.setHeader('Content-Type', 'text/event-stream');
//   res.setHeader('Cache-Control', 'no-cache');
//   res.setHeader('Connection', 'keep-alive');
//
//   const stream = await client.messages.stream({
//     model: 'claude-3-5-haiku-20241022',
//     max_tokens: 1024,
//     messages: req.body.messages,
//   });
//
//   for await (const event of stream) {
//     res.write(`data: ${JSON.stringify(event)}\\n\\n`);
//   }
//   res.write('data: [DONE]\\n\\n');
//   res.end();
// });
''',
        "dependencies": [
            {"name": "react", "version": ">=18", "purpose": "React"},
            {"name": "@anthropic-ai/sdk", "version": ">=0.36", "purpose": "Backend Anthropic client"},
        ],
        "env_vars": [
            {"name": "ANTHROPIC_API_KEY", "required": True, "description": "Backend only", "example": "sk-ant-..."},
        ],
        "setup_steps": [
            "Drop Chat component into existing React app",
            "Add backend route /api/chat (Node / Bun / Express / Next.js / etc.)",
            "Set ANTHROPIC_API_KEY in backend env",
            "Wire backend to your hosting (Express, Fastify, Next.js API route, etc.)",
        ],
        "variations": [
            {"label": "Tool calling support", "description": "Handle tool_use events.", "code_snippet": "// In streaming parser: switch on event.type === 'content_block_start' with type='tool_use'; track partial_json; execute after content_block_stop"},
            {"label": "Conversation persistence", "description": "Save + load chats.", "code_snippet": "// useEffect to fetch from /api/conversations/:id on mount. Save messages to backend after each user/assistant pair."},
            {"label": "Token counter UI", "description": "Show usage live.", "code_snippet": "// Track event.usage.input_tokens + output_tokens from message_start / message_delta events; display in footer"},
        ],
        "common_errors": [
            {"error_text": "Stream hangs / never completes", "cause": "Backend not flushing properly.", "fix_snippet": "Express: res.write() + res.flushHeaders() at start. Bun / Next.js streaming responses handle this natively."},
            {"error_text": "Partial JSON parse failures", "cause": "SSE event split across chunks.", "fix_snippet": "Buffer incomplete lines; the buffer.pop() pattern in the code keeps the last partial line for next iteration."},
            {"error_text": "CORS errors", "cause": "Frontend on different origin.", "fix_snippet": "Backend: Access-Control-Allow-Origin: <your-frontend>. Or proxy backend through Next.js / Vite dev server."},
            {"error_text": "Multiple connections per click", "cause": "useEffect cleanup missing.", "fix_snippet": "Track AbortController in ref; abort on unmount or new send. Pattern in code handles this with abortRef."},
        ],
        "production_checklist": [
            "Abort controller for clean unmount.",
            "Server-side: stream from backend, never expose API key client-side.",
            "Add rate limiting (per-IP / per-user).",
            "Set up CORS correctly.",
            "Handle network errors gracefully (retry / friendly message).",
            "Test connection drop mid-stream.",
        ],
        "tested_with": {
            "model_versions": ["claude-3-5-haiku-20241022"],
            "library_versions": ["react==18", "@anthropic-ai/sdk==0.36"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["anthropic", "react"],
        "related_glossary_slugs": ["streaming-ui", "server-sent-events"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Why raw vs Vercel AI SDK?", "answer": "Raw: minimal deps, full control, learn how streaming works. Vercel AI SDK: less code, more features (tools, generative UI), framework-tied. Use raw for embedding into existing apps; AI SDK for greenfield."},
            {"question": "SSE format from Anthropic?", "answer": "Anthropic SDK emits events: message_start, content_block_start, content_block_delta (text chunks), content_block_stop, message_stop. Parse content_block_delta.delta.text to accumulate."},
            {"question": "Browser SSE alternatives?", "answer": "EventSource API works but is GET-only. For POST with streaming, use fetch + ReadableStream (what this code does). Or use WebSockets for bidirectional."},
            {"question": "Mobile React Native?", "answer": "Same fetch + ReadableStream pattern works in RN with polyfills. Or use the AI SDK's react-native adapter for smoother experience."},
        ],
        "github_url": "https://github.com/anthropics/anthropic-sdk-typescript",
        "meta_title": "React Chat With Anthropic Streaming Starter",
        "meta_description": "Pure React chat: fetch + ReadableStream + SSE parsing. Direct Anthropic streaming. Tiny dep footprint, embed in any React app.",
    },
    {
        "slug": "vue-pinia-llm-chat-store",
        "title": "Vue 3 + Pinia LLM Chat Store",
        "tldr": "Vue 3 with Composition API + Pinia store for chat state. Provider-agnostic (OpenAI / Anthropic). Streaming via fetch + ReadableStream. Production-grade Vue chat.",
        "category": "frontend",
        "language": "typescript",
        "framework": "Vue 3 + Pinia",
        "tags": ["vue", "pinia", "chat", "composition-api"],
        "best_for_tags": ["vue-stack", "nuxt-apps", "ts-strict"],
        "difficulty_tier": "intermediate",
        "featured": False,
        "when_to_use": "Vue 3 / Nuxt 3 app adding LLM chat. Pinia store manages messages + streaming state. Pattern works in any Vue context — full app, micro-frontend, embedded widget.",
        "when_not_to_use": "Skip for vanilla JS (use raw fetch). Skip for Vue 2 (Composition API patterns won't translate cleanly). Skip for non-streaming workloads.",
        "quick_start": "npm i pinia vue@3 && code .",
        "full_code": '''// Vue 3 + Pinia chat store with streaming

// =============== stores/chat.ts ===============
import { defineStore } from "pinia";
import { ref, computed } from "vue";


interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
}


export const useChatStore = defineStore("chat", () => {
  // ----- STATE -----
  const messages = ref<Message[]>([]);
  const isStreaming = ref(false);
  const error = ref<string | null>(null);
  const abortController = ref<AbortController | null>(null);


  // ----- GETTERS -----
  const hasMessages = computed(() => messages.value.length > 0);
  const lastMessage = computed(() => messages.value[messages.value.length - 1]);


  // ----- ACTIONS -----

  function addMessage(role: Message["role"], content: string) {
    messages.value.push({
      id: crypto.randomUUID(),
      role,
      content,
    });
  }


  function appendToLast(text: string) {
    const last = messages.value[messages.value.length - 1];
    if (last) last.content += text;
  }


  function clear() {
    messages.value = [];
    error.value = null;
  }


  function stop() {
    abortController.value?.abort();
    abortController.value = null;
    isStreaming.value = false;
  }


  async function send(userText: string, options: { endpoint?: string; system?: string } = {}) {
    if (isStreaming.value || !userText.trim()) return;

    addMessage("user", userText);
    addMessage("assistant", ""); // placeholder for streaming
    isStreaming.value = true;
    error.value = null;
    abortController.value = new AbortController();

    try {
      const apiMessages = options.system
        ? [{ role: "system", content: options.system }, ...messages.value.slice(0, -1)]
        : messages.value.slice(0, -1);

      const response = await fetch(options.endpoint || "/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: apiMessages }),
        signal: abortController.value.signal,
      });

      if (!response.ok || !response.body) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\\n\\n");
        buffer = lines.pop() || "";
        for (const line of lines) {
          if (!line.startsWith("data:")) continue;
          const payload = line.slice(5).trim();
          if (payload === "[DONE]") break;
          try {
            const event = JSON.parse(payload);
            // Adapt to your backend's stream format
            const delta = event.choices?.[0]?.delta?.content || event.delta?.text;
            if (delta) appendToLast(delta);
          } catch {}
        }
      }
    } catch (err: any) {
      if (err.name !== "AbortError") {
        error.value = err.message;
        appendToLast(`\\n\\n[Error: ${err.message}]`);
      }
    } finally {
      isStreaming.value = false;
      abortController.value = null;
    }
  }


  return {
    messages, isStreaming, error,
    hasMessages, lastMessage,
    addMessage, clear, stop, send,
  };
});


// =============== components/ChatView.vue ===============
const TEMPLATE = `<template>
  <div class="flex flex-col h-screen max-w-2xl mx-auto p-4">
    <div ref="scrollEl" class="flex-1 overflow-y-auto space-y-3 mb-4">
      <div v-for="m in store.messages" :key="m.id"
           :class="m.role === 'user' ? 'text-right' : 'text-left'">
        <div :class="['inline-block p-3 rounded-lg max-w-prose',
                      m.role === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-100']">
          <pre class="whitespace-pre-wrap font-sans">{{ m.content || '...' }}</pre>
        </div>
      </div>
    </div>

    <div v-if="store.error" class="text-red-600 text-sm mb-2">{{ store.error }}</div>

    <div class="flex gap-2">
      <input v-model="input"
             @keydown.enter="onSend"
             :disabled="store.isStreaming"
             placeholder="Ask anything..."
             class="flex-1 p-3 border rounded" />
      <button v-if="store.isStreaming" @click="store.stop()"
              class="px-4 bg-red-500 text-white rounded">Stop</button>
      <button v-else @click="onSend" :disabled="!input"
              class="px-4 bg-blue-500 text-white rounded disabled:opacity-50">
        Send
      </button>
      <button @click="store.clear()" class="px-3 text-gray-500">Clear</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue';
import { useChatStore } from '../stores/chat';

const store = useChatStore();
const input = ref('');
const scrollEl = ref<HTMLElement | null>(null);

watch(() => store.messages.length, async () => {
  await nextTick();
  scrollEl.value?.scrollTo({ top: scrollEl.value.scrollHeight, behavior: 'smooth' });
});

function onSend() {
  const text = input.value;
  input.value = '';
  store.send(text);
}
</script>`;
''',
        "dependencies": [
            {"name": "vue", "version": ">=3.4", "purpose": "Vue 3"},
            {"name": "pinia", "version": ">=2.2", "purpose": "State management"},
        ],
        "env_vars": [],
        "setup_steps": [
            "npm create vue@latest my-chat (TypeScript + Pinia)",
            "Save stores/chat.ts + components/ChatView.vue",
            "Add backend route streaming SSE",
            "Import ChatView into App.vue",
            "npm run dev",
        ],
        "variations": [
            {"label": "Nuxt 3 with server route", "description": "Use Nuxt's nitro server.", "code_snippet": "// server/api/chat.post.ts: defineEventHandler with sendStream() for SSE"},
            {"label": "Persistent state with VueUse", "description": "Save to localStorage.", "code_snippet": "import { useStorage } from '@vueuse/core'; const messages = useStorage('chat-msgs', [])"},
            {"label": "Multiple chat threads", "description": "Store threads by ID.", "code_snippet": "// Pinia state: threads: Record<string, Message[]>; switch via activeThreadId"},
        ],
        "common_errors": [
            {"error_text": "Reactivity lost on append", "cause": "Modifying nested object incorrectly.", "fix_snippet": "Use last.content += text directly on the array element (Vue 3 tracks deep). DON'T spread into new objects mid-stream."},
            {"error_text": "Pinia store not auto-imported in Nuxt", "cause": "Missing pinia module.", "fix_snippet": "npm i @pinia/nuxt; add to nuxt.config.ts modules: ['@pinia/nuxt']. Stores then auto-import."},
            {"error_text": "Scroll lagging behind", "cause": "DOM not updated yet.", "fix_snippet": "Use nextTick() after state change, BEFORE scrolling. Pattern in template handles this."},
            {"error_text": "CORS preflight", "cause": "Backend on different origin.", "fix_snippet": "Backend: Access-Control-Allow-* headers. Or use Vite proxy in development; reverse proxy in prod."},
        ],
        "production_checklist": [
            "Use Pinia store for chat state (single source of truth).",
            "Abort controller for clean unmount.",
            "Persist messages to localStorage / backend for resilience.",
            "Add rate limiting on backend (per-user / per-IP).",
            "Validate user input client-side + server-side.",
            "Use Vue's <script setup> + TypeScript strict mode.",
        ],
        "tested_with": {
            "model_versions": [],
            "library_versions": ["vue==3.4", "pinia==2.2"],
            "last_verified_date": "2026-05-14",
        },
        "related_tool_slugs": ["vue", "pinia"],
        "related_glossary_slugs": ["composition-api", "state-management"],
        "related_learn_slugs": [],
        "license": "MIT",
        "attribution": "OSS AI Hub",
        "faq": [
            {"question": "Pinia vs Vuex?", "answer": "Pinia: Composition API native, TypeScript-friendly, simpler. Vuex: older, Options API era. Pinia is the official recommendation for Vue 3."},
            {"question": "Vue AI SDK?", "answer": "Vercel's AI SDK has a Vue adapter (useChat for Vue). Easier than rolling your own; this starter is for when you want full control."},
            {"question": "Nuxt 3 specifics?", "answer": "Server routes via /server/api. Use sendStream() in defineEventHandler for SSE. Auto-imports of components. Pinia auto-imports with @pinia/nuxt."},
            {"question": "Performance?", "answer": "Vue 3 reactivity is fast. Pinia adds minimal overhead. For 1k+ message threads, virtualize the list (vue-virtual-scroller)."},
        ],
        "github_url": "https://github.com/vuejs/pinia",
        "meta_title": "Vue 3 + Pinia LLM Chat Store Starter",
        "meta_description": "Vue 3 chat with Pinia store: streaming, abort control, persistent state, Nuxt 3 ready. Production-grade Vue LLM frontend.",
    },
]
