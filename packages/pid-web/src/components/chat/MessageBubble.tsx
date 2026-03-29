import type { ChatMessage } from "@/types/chat";

interface MessageBubbleProps {
  message: ChatMessage;
}

/**
 * Regex to detect P&ID equipment/instrument tags such as P-101, TIC-201, FV-301A, etc.
 * Matches patterns like: 1-3 uppercase letters, optional dash, then digits, optional letter suffix.
 */
const TAG_REGEX = /\b([A-Z]{1,4}-?\d{2,5}[A-Z]?)\b/g;

/** Very lightweight markdown: **bold** and simple unordered lists. */
function renderContent(text: string): React.ReactNode[] {
  const lines = text.split("\n");
  const result: React.ReactNode[] = [];

  lines.forEach((line, lineIdx) => {
    // Simple unordered list
    const listMatch = line.match(/^[-*]\s+(.*)/);
    const content = listMatch ? listMatch[1] : line;

    // Process inline formatting
    const parts: React.ReactNode[] = [];
    let lastIndex = 0;

    // Bold
    const boldRegex = /\*\*(.+?)\*\*/g;
    let boldMatch: RegExpExecArray | null;
    const segments: { start: number; end: number; node: React.ReactNode }[] =
      [];

    while ((boldMatch = boldRegex.exec(content)) !== null) {
      segments.push({
        start: boldMatch.index,
        end: boldMatch.index + boldMatch[0].length,
        node: (
          <strong key={`b-${lineIdx}-${boldMatch.index}`}>
            {boldMatch[1]}
          </strong>
        ),
      });
    }

    // Sort segments by start
    segments.sort((a, b) => a.start - b.start);

    for (const seg of segments) {
      if (seg.start > lastIndex) {
        parts.push(highlightTags(content.slice(lastIndex, seg.start), lineIdx));
      }
      parts.push(seg.node);
      lastIndex = seg.end;
    }
    if (lastIndex < content.length) {
      parts.push(highlightTags(content.slice(lastIndex), lineIdx));
    }
    if (parts.length === 0) {
      parts.push(highlightTags(content, lineIdx));
    }

    if (listMatch) {
      result.push(
        <li key={`l-${lineIdx}`} className="ml-4 list-disc">
          {parts}
        </li>,
      );
    } else {
      result.push(
        <span key={`s-${lineIdx}`}>
          {parts}
          {lineIdx < lines.length - 1 && <br />}
        </span>,
      );
    }
  });

  return result;
}

/** Highlight equipment/instrument tags within a text fragment. */
function highlightTags(text: string, keyPrefix: number): React.ReactNode {
  const parts: React.ReactNode[] = [];
  let lastIdx = 0;
  let match: RegExpExecArray | null;

  TAG_REGEX.lastIndex = 0;
  while ((match = TAG_REGEX.exec(text)) !== null) {
    if (match.index > lastIdx) {
      parts.push(text.slice(lastIdx, match.index));
    }
    parts.push(
      <span
        key={`tag-${keyPrefix}-${match.index}`}
        className="tag-equipment"
      >
        {match[1]}
      </span>,
    );
    lastIdx = match.index + match[0].length;
  }
  if (lastIdx < text.length) {
    parts.push(text.slice(lastIdx));
  }
  return parts.length === 1 ? parts[0] : <>{parts}</>;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-xl px-4 py-2 text-sm leading-relaxed ${
          isUser
            ? "bg-blue-600 text-white"
            : "bg-gray-100 text-gray-800"
        }`}
      >
        {isUser ? message.content : renderContent(message.content)}
      </div>
    </div>
  );
}
