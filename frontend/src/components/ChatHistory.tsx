"use client";
import { useEffect, useRef } from "react";
import type { Message } from "@/types/chat";
import UserBubble from "./UserBubble";
import BotBubble from "./BotBubble";
import TypingIndicator from "./TypingIndicator";

interface ChatHistoryProps {
  messages: Message[];
  loading: boolean;
}

export default function ChatHistory({ messages, loading }: ChatHistoryProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  return (
    <div className="w-full space-y-8 pb-10">
      {messages.map((msg, i) =>
        msg.role === "user" ? (
          <UserBubble key={i} content={msg.content} timestamp={msg.timestamp} />
        ) : (
          <BotBubble key={i} content={msg.content} timestamp={msg.timestamp} />
        )
      )}
      {loading && <TypingIndicator />}
      <div ref={bottomRef} />
    </div>
  );
}
