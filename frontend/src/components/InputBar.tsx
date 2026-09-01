"use client";
import { useState, useRef, KeyboardEvent } from "react";

interface InputBarProps {
  onSend: (query: string) => void;
  disabled: boolean;
}

export default function InputBar({ onSend, disabled }: InputBarProps) {
  const [value, setValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <footer className="fixed bottom-0 left-72 right-0 p-6 bg-gradient-to-t from-[#0b1326] to-transparent pointer-events-none">
      <div className="max-w-4xl mx-auto pointer-events-auto">
        <div className="bg-[#171f33]/70 backdrop-blur-2xl rounded-full border border-[#3e4850]/20 p-2 shadow-[0_8px_48px_rgba(0,0,0,0.4)] flex items-center gap-4">
          {/* Search icon */}
          <span className="material-symbols-outlined text-[#bec8d2] ml-4">
            search
          </span>

          {/* Input */}
          <input
            ref={inputRef}
            type="text"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            placeholder="Ask about fund expense ratios, exit loads, or SIP amounts..."
            className="flex-1 bg-transparent border-none outline-none text-[#dae2fd] placeholder:text-[#bec8d2]/60 text-base py-3 disabled:opacity-50"
          />

          {/* Send button */}
          <button
            onClick={handleSend}
            disabled={disabled || !value.trim()}
            className="w-12 h-12 rounded-full bg-[#0ea5e9] flex items-center justify-center text-[#00344d] hover:bg-[#89ceff] transition-colors shadow-lg disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <span className="material-symbols-outlined">send</span>
          </button>
        </div>
      </div>
    </footer>
  );
}
