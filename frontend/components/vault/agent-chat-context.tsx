"use client";

import dynamic from "next/dynamic";
import { SparklesIcon } from "lucide-react";
import { createContext, useContext, useState, type ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const AgentChatDialog = dynamic(
  () => import("./agent-chat").then((module) => module.AgentChatDialog),
  { ssr: false },
);

type AgentChatContextValue = {
  openChat: () => void;
};

const AgentChatContext = createContext<AgentChatContextValue | null>(null);

function useAgentChat(): AgentChatContextValue {
  const context = useContext(AgentChatContext);

  if (!context) {
    throw new Error("AgentChatTrigger must be used within AgentChatProvider.");
  }

  return context;
}

/**
 * The shell's lightweight half of the assistant.
 *
 * The dialog is a large client module (Streamdown, Shiki and the transcript
 * surface). Loading it on every catalogue visit delayed LCP for a surface most
 * visitors never open, so it is imported on the first click. The provider stays
 * mounted after that, which keeps the transcript when the dialog closes.
 */
export function AgentChatProvider({
  signedIn = true,
  userName = null,
  children,
}: {
  signedIn?: boolean;
  userName?: string | null;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  function openChat() {
    setMounted(true);
    setOpen(true);
  }

  return (
    <AgentChatContext.Provider value={{ openChat }}>
      {children}
      {mounted ? (
        <AgentChatDialog
          open={open}
          onOpenChange={setOpen}
          signedIn={signedIn}
          userName={userName}
        />
      ) : null}
    </AgentChatContext.Provider>
  );
}

/** The one control that opens the conversation. */
export function AgentChatTrigger({ className }: { className?: string }) {
  const { openChat } = useAgentChat();

  return (
    <Button
      type="button"
      className={cn(className, "cursor-pointer")}
      aria-label="Ask AI"
      onClick={openChat}
    >
      <SparklesIcon data-icon="inline-start" />
      <span className="group-data-[collapsible=icon]:hidden">Ask AI</span>
    </Button>
  );
}

/**
 * A conversation with its own trigger.
 *
 * For a surface outside the shell (and for the tests): the product renders the
 * provider once in `AppShell` and places triggers in the sidebar and the floating
 * mobile control.
 */
export function AgentChat({
  signedIn = true,
  userName = null,
  className,
}: {
  signedIn?: boolean;
  userName?: string | null;
  className?: string;
}) {
  return (
    <AgentChatProvider signedIn={signedIn} userName={userName}>
      <AgentChatTrigger className={className} />
    </AgentChatProvider>
  );
}
