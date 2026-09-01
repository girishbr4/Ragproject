export default function TypingIndicator() {
  return (
    <div className="flex flex-col items-start">
      <div className="bg-[#222a3d]/80 backdrop-blur-xl border border-white/10 py-4 px-5 rounded-[20px] rounded-bl-sm flex items-center gap-2 w-fit">
        <div className="w-2 h-2 rounded-full bg-[#89ceff] animate-bounce-dot-1" />
        <div className="w-2 h-2 rounded-full bg-[#89ceff] animate-bounce-dot-2" />
        <div className="w-2 h-2 rounded-full bg-[#89ceff] animate-bounce-dot-3" />
      </div>
    </div>
  );
}
