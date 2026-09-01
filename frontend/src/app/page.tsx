"use client";
import { useState } from "react";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import EmptyState from "@/components/EmptyState";
import ChatHistory from "@/components/ChatHistory";
import InputBar from "@/components/InputBar";
import { useChat } from "@/hooks/useChat";

export default function ChatApp() {
  const { messages, loading, send } = useChat();
  const [hasStarted, setHasStarted] = useState(false);

  const handleSend = (query: string) => {
    if (!hasStarted) setHasStarted(true);
    send(query);
  };

  return (
    <div className="flex min-h-screen bg-[#0b1326] text-[#dae2fd] font-sans overflow-x-hidden">
      {/* Ambient background glows */}
      <div className="fixed inset-0 pointer-events-none -z-10">
        <div className="absolute top-1/4 -right-64 w-96 h-96 bg-[#89ceff]/10 rounded-full blur-[120px] mix-blend-screen" />
        <div className="absolute bottom-1/4 -left-64 w-96 h-96 bg-[#ffb86e]/10 rounded-full blur-[120px] mix-blend-screen" />
      </div>

      <Sidebar onSchemeClick={handleSend} />

      <div className="pl-72 flex flex-col min-h-screen w-full">
        <Header />

        <main className="pt-20 pb-32 flex-1 w-full bg-transparent relative">
          <div className="flex flex-col w-full h-full">
            <div className="flex-1 w-full max-w-[900px] mx-auto px-6 flex flex-col justify-end min-h-[calc(100vh-140px)]">
              {!hasStarted ? (
                <EmptyState onExampleClick={handleSend} />
              ) : (
                <ChatHistory messages={messages} loading={loading} />
              )}
            </div>
          </div>
        </main>

        <InputBar onSend={handleSend} disabled={loading} />
      </div>
    </div>
  );
}
