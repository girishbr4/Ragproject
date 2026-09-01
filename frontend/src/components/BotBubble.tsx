interface BotBubbleProps {
  content: string;
  timestamp: string;
}

// Parse the backend response to extract source URL, date, and answer text
function parseResponse(raw: string): {
  answer: string;
  sourceUrl: string | null;
  updatedDate: string | null;
  disclaimer: boolean;
} {
  let answer = raw;
  let sourceUrl: string | null = null;
  let updatedDate: string | null = null;
  let disclaimer = false;

  // Extract source URL
  const sourceMatch = answer.match(/Source:\s*(https?:\/\/[^\s\n]+)/i);
  if (sourceMatch) {
    sourceUrl = sourceMatch[1];
    answer = answer.replace(sourceMatch[0], "").trim();
  }

  // Extract last updated date
  const dateMatch = answer.match(/Last updated from sources:\s*([^\n]+)/i);
  if (dateMatch) {
    updatedDate = dateMatch[1].trim();
    answer = answer.replace(dateMatch[0], "").trim();
  }

  // Extract disclaimer line
  if (answer.includes("Facts-only. No investment advice.")) {
    disclaimer = true;
    answer = answer
      .replace(/>\s*Facts-only\. No investment advice\./gi, "")
      .trim();
  }

  return { answer: answer.trim(), sourceUrl, updatedDate, disclaimer };
}

export default function BotBubble({ content, timestamp }: BotBubbleProps) {
  const { answer, sourceUrl, updatedDate } = parseResponse(content);

  return (
    <div className="flex flex-col items-start animate-fade-in-left">
      <div className="bg-[#222a3d]/80 backdrop-blur-xl border border-white/10 p-5 rounded-[20px] rounded-bl-sm max-w-[85%] shadow-xl relative overflow-hidden group">
        {/* Hover gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-br from-[#89ceff]/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none" />

        {/* Header row */}
        <div className="flex items-center gap-3 mb-4">
          <div className="w-8 h-8 rounded-full bg-[#89ceff]/20 flex items-center justify-center">
            <span className="material-symbols-outlined text-[#89ceff] text-[18px]">
              info
            </span>
          </div>
          <span className="text-xs font-semibold text-[#89ceff] tracking-widest uppercase">
            Fund Details
          </span>
        </div>

        {/* Answer text */}
        <p className="text-base text-[#dae2fd] mb-6 leading-relaxed whitespace-pre-wrap">
          {answer}
        </p>

        {/* Source + date footer */}
        <div className="flex flex-wrap items-center gap-3 mt-4 pt-4 border-t border-white/5">
          {sourceUrl && (
            <a
              href={sourceUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/5 hover:bg-white/10 hover:border-[#89ceff]/50 border border-white/10 transition-all cursor-pointer"
            >
              <span className="material-symbols-outlined text-[14px] text-[#bec8d2]">
                description
              </span>
              <span className="text-xs text-[#bec8d2] max-w-[240px] truncate">
                Source: {sourceUrl}
              </span>
            </a>
          )}
          {updatedDate && (
            <div className="flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[14px] text-[#bec8d2]/50">
                update
              </span>
              <span className="text-xs text-[#bec8d2]/60">{updatedDate}</span>
            </div>
          )}
        </div>
      </div>

      {/* Disclaimer micro-text */}
      <div className="mt-2 flex items-center gap-2 max-w-[85%] pl-2">
        <span className="material-symbols-outlined text-[12px] text-[#bec8d2]/40">
          gavel
        </span>
        <p className="text-xs text-[#bec8d2]/50">
          Facts-only. No investment advice.
          {timestamp && ` · ${timestamp}`}
        </p>
      </div>
    </div>
  );
}
