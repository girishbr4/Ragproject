interface UserBubbleProps {
  content: string;
  timestamp: string;
}

export default function UserBubble({ content, timestamp }: UserBubbleProps) {
  return (
    <div className="flex flex-col items-end animate-fade-in-right">
      <div className="bg-[#0ea5e9] text-[#00344d] font-medium text-base py-3 px-5 rounded-[20px] rounded-br-sm max-w-[80%] shadow-[0_4px_24px_rgba(14,165,233,0.3)]">
        {content}
      </div>
      {timestamp && (
        <span className="text-xs text-[#bec8d2] mt-2 opacity-70">
          {timestamp}
        </span>
      )}
    </div>
  );
}
