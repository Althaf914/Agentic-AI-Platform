import { useState, useRef, useCallback, useEffect, type ReactNode } from "react";

// ─── Variable descriptor for insertion buttons ──────────────────────────────

interface VariableDescriptor {
  key: string;
  label: string;
}

// ─── Props ──────────────────────────────────────────────────────────────────

interface OutreachEditorProps {
  subject: string;
  body: string;
  variables?: VariableDescriptor[];
  onSave?: (subject: string, body: string) => void;
  readOnly?: boolean;
}

// ─── Toolbar for simple rich text ───────────────────────────────────────────

function ToolbarButton({ label, title, onClick, icon }: {
  label: string; title: string; onClick: () => void; icon: ReactNode;
}) {
  return (
    <button
      type="button"
      title={title}
      onClick={onClick}
      className="px-2 py-1 text-xs rounded hover:bg-[--bg-secondary] text-[--text-secondary] hover:text-white transition-colors"
    >
      {icon}
      <span className="sr-only">{label}</span>
    </button>
  );
}

// ─── Variable insertion helpers ─────────────────────────────────────────────

const DEFAULT_VARIABLES = [
  { key: "{{first_name}}", label: "First name" },
  { key: "{{company_name}}", label: "Company name" },
  { key: "{{market_trigger}}", label: "Market trigger" },
  { key: "{{sender_name}}", label: "Sender name" },
  { key: "{{sender_title}}", label: "Sender title" },
];

// ─── Component ──────────────────────────────────────────────────────────────

export default function OutreachEditor({
  subject: initialSubject,
  body: initialBody,
  variables,
  onSave,
  readOnly = false,
}: OutreachEditorProps) {
  const [subject, setSubject] = useState(initialSubject);
  const [body, setBody] = useState(initialBody);
  const [preview, setPreview] = useState(false);
  const [charCount, setCharCount] = useState(initialBody.length);
  const bodyRef = useRef<HTMLTextAreaElement>(null);
  const variableVars = variables || DEFAULT_VARIABLES;

  useEffect(() => {
    setCharCount(body.length);
  }, [body]);

  const insertAtCursor = useCallback((text: string) => {
    const textarea = bodyRef.current;
    if (!textarea) return;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const newBody = body.slice(0, start) + text + body.slice(end);
    setBody(newBody);
    // Restore cursor position after the inserted text
    requestAnimationFrame(() => {
      textarea.focus();
      textarea.selectionStart = textarea.selectionEnd = start + text.length;
    });
  }, [body]);

  const wrapSelection = useCallback((before: string, after: string) => {
    const textarea = bodyRef.current;
    if (!textarea) return;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selected = body.slice(start, end);
    const newBody = body.slice(0, start) + before + selected + after + body.slice(end);
    setBody(newBody);
    requestAnimationFrame(() => {
      textarea.focus();
      textarea.selectionStart = start + before.length;
      textarea.selectionEnd = start + before.length + selected.length;
    });
  }, [body]);

  const handleBold = () => wrapSelection("**", "**");
  const handleItalic = () => wrapSelection("_", "_");
  const handleLink = () => {
    const url = prompt("Enter URL:", "https://");
    if (url) wrapSelection("[", `](${url})`);
  };

  const handleCopy = async () => {
    const full = `Subject: ${subject}\n\n${body}`;
    try {
      await navigator.clipboard.writeText(full);
    } catch { /* silent */ }
  };

  const handleSave = () => {
    onSave?.(subject, body);
  };

  // ── Render the preview (simple markdown-like rendering) ──────────────────
  const renderPreview = (text: string) => {
    // Very simple: bold **text**, italic _text_, newlines to <br>
    return text
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/_(.+?)_/g, "<em>$1</em>")
      .replace(/\n/g, "<br />");
  };

  return (
    <div className="space-y-3">
      {/* Subject */}
      <div>
        <label className="text-[10px] text-[--text-muted] uppercase tracking-wider mb-1 block">Subject line</label>
        {readOnly || preview ? (
          <p className="text-xs text-white px-3 py-2 rounded-lg border border-[--border] bg-[--bg-secondary]">
            {subject || <span className="italic text-[--text-muted]">No subject</span>}
          </p>
        ) : (
          <input
            type="text"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            placeholder="Enter subject line..."
            className="w-full px-3 py-2 text-xs rounded-lg border bg-[--bg-secondary] border-[--border] text-white placeholder:text-[--text-muted] focus:outline-none focus:border-[#4f7cff]"
          />
        )}
      </div>

      {/* Body */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <label className="text-[10px] text-[--text-muted] uppercase tracking-wider">Email body</label>
          <div className="flex items-center gap-2">
            {!readOnly && (
              <button
                onClick={() => setPreview(!preview)}
                className={`text-[10px] px-2 py-0.5 rounded transition-colors ${
                  preview ? "bg-[#4f7cff]/20 text-[#4f7cff]" : "text-[--text-muted] hover:text-[--text-secondary]"
                }`}
              >
                {preview ? "Edit" : "Preview"}
              </button>
            )}
            <span className={`text-[10px] ${charCount > 300 ? "text-amber-400" : "text-[--text-muted]"}`}>
              {charCount} chars
            </span>
          </div>
        </div>

        {preview || readOnly ? (
          <div
            className="p-3 rounded-lg border border-[--border] bg-[--bg-secondary] text-xs text-[--text-secondary] whitespace-pre-wrap min-h-[120px]"
            dangerouslySetInnerHTML={{ __html: renderPreview(body) }}
          />
        ) : (
          <textarea
            ref={bodyRef}
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="Write your email body here..."
            rows={8}
            className="w-full px-3 py-2 text-xs rounded-lg border bg-[--bg-secondary] border-[--border] text-white placeholder:text-[--text-muted] resize-y focus:outline-none focus:border-[#4f7cff] font-mono leading-relaxed"
          />
        )}
      </div>

      {/* Toolbar (edit mode only) */}
      {!readOnly && !preview && (
        <div className="flex flex-wrap items-center gap-1 px-2 py-1.5 rounded-lg border border-[--border]" style={{ backgroundColor: "var(--bg-card)" }}>
          <ToolbarButton label="Bold" title="Bold" icon={<strong>B</strong>} onClick={handleBold} />
          <ToolbarButton label="Italic" title="Italic" icon={<em>I</em>} onClick={handleItalic} />
          <ToolbarButton label="Link" title="Insert link" icon="🔗" onClick={handleLink} />

          <div className="w-px h-4 bg-[--border] mx-1" />

          {/* Variable insertion */}
          <span className="text-[9px] text-[--text-muted] mr-1">Insert:</span>
          {variableVars.map((v) => (
            <button
              key={v.key}
              type="button"
              title={`Insert ${v.label}`}
              onClick={() => insertAtCursor(v.key)}
              className="text-[9px] px-1.5 py-0.5 rounded bg-[#4f7cff]/10 text-[#4f7cff] hover:bg-[#4f7cff]/20 transition-colors"
            >
              {v.label}
            </button>
          ))}

          <div className="flex-1" />

          <button
            onClick={handleCopy}
            className="text-[9px] px-1.5 py-0.5 rounded text-[--text-muted] hover:text-white transition-colors"
            title="Copy to clipboard"
          >
            📋 Copy
          </button>
        </div>
      )}

      {/* Save button */}
      {!readOnly && onSave && (
        <div className="flex justify-end">
          <button
            onClick={handleSave}
            className="px-4 py-1.5 text-xs font-medium rounded-lg bg-[#4f7cff] text-white hover:bg-[#3a6ae8] transition-colors"
          >
            Save changes
          </button>
        </div>
      )}
    </div>
  );
}
