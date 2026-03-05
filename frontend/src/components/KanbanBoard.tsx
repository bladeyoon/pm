"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import {
  closestCenter,
  DndContext,
  DragOverlay,
  PointerSensor,
  pointerWithin,
  useSensor,
  useSensors,
  type CollisionDetection,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { KanbanColumn } from "@/components/KanbanColumn";
import { KanbanCardPreview } from "@/components/KanbanCardPreview";
import { createId, initialData, moveCard, type BoardData } from "@/lib/kanban";

type KanbanBoardProps = {
  onLogout?: () => void;
  username?: string;
};

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

type AIChatResponsePayload = {
  status: string;
  model: string;
  reply: string;
  boardUpdated: boolean;
  board: BoardData | null;
};

export const KanbanBoard = ({ onLogout, username }: KanbanBoardProps) => {
  const [board, setBoard] = useState<BoardData>(() => initialData);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);
  const [isLoadingBoard, setIsLoadingBoard] = useState(Boolean(username));
  const [isSavingBoard, setIsSavingBoard] = useState(false);
  const [persistenceError, setPersistenceError] = useState<string | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatPrompt, setChatPrompt] = useState("");
  const [isSendingChat, setIsSendingChat] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  const pendingSaveRef = useRef<Promise<void> | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 6 },
    })
  );

  const cardsById = useMemo(() => board.cards, [board.cards]);

  const collisionDetectionStrategy: CollisionDetection = (args) => {
    const pointerCollisions = pointerWithin(args);
    if (pointerCollisions.length > 0) {
      return pointerCollisions;
    }
    return closestCenter(args);
  };

  const saveBoard = async (nextBoard: BoardData) => {
    if (!username) {
      return;
    }

    setIsSavingBoard(true);
    try {
      const response = await fetch(`/api/board/${encodeURIComponent(username)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ board: nextBoard }),
        cache: "no-store",
      });

      if (!response.ok) {
        throw new Error(`Save failed: ${response.status}`);
      }
    } finally {
      setIsSavingBoard(false);
    }
  };

  const updateBoard = (updater: (prev: BoardData) => BoardData) => {
    setBoard((prev) => {
      const next = updater(prev);
      if (username) {
        const pendingSave = saveBoard(next)
          .then(() => setPersistenceError(null))
          .catch(() => {
            setPersistenceError(
              "Unable to save board changes right now. Please try again."
            );
          });
        pendingSaveRef.current = pendingSave;
      }
      return next;
    });
  };

  const refreshBoardAfterAIUpdate = async () => {
    if (!username) {
      return;
    }
    try {
      const response = await fetch(`/api/board/${encodeURIComponent(username)}`, {
        cache: "no-store",
      });
      if (!response.ok) {
        throw new Error(`Refresh failed: ${response.status}`);
      }
      const payload = (await response.json()) as { board: BoardData };
      setBoard(payload.board);
      setPersistenceError(null);
    } catch {
      setPersistenceError(
        "Board updated, but refresh failed. Reload if items look out of sync."
      );
    }
  };

  useEffect(() => {
    if (!username) {
      setIsLoadingBoard(false);
      return;
    }

    let isActive = true;
    setIsLoadingBoard(true);
    setPersistenceError(null);

    void fetch(`/api/board/${encodeURIComponent(username)}`, {
      cache: "no-store",
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`Load failed: ${response.status}`);
        }
        return response.json();
      })
      .then((payload: { board: BoardData }) => {
        if (!isActive) {
          return;
        }
        setBoard(payload.board);
      })
      .catch(() => {
        if (!isActive) {
          return;
        }
        setPersistenceError(
          "Unable to load saved board. Showing local board instead."
        );
      })
      .finally(() => {
        if (isActive) {
          setIsLoadingBoard(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [username]);

  const handleDragStart = (event: DragStartEvent) => {
    setActiveCardId(event.active.id as string);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCardId(null);

    if (!over || active.id === over.id) {
      return;
    }

    updateBoard((prev) => ({
      ...prev,
      columns: moveCard(prev.columns, active.id as string, over.id as string),
    }));
  };

  const handleRenameColumn = (columnId: string, title: string) => {
    updateBoard((prev) => ({
      ...prev,
      columns: prev.columns.map((column) =>
        column.id === columnId ? { ...column, title } : column
      ),
    }));
  };

  const handleAddCard = (columnId: string, title: string, details: string) => {
    const id = createId("card");
    updateBoard((prev) => ({
      ...prev,
      cards: {
        ...prev.cards,
        [id]: { id, title, details: details || "No details yet." },
      },
      columns: prev.columns.map((column) =>
        column.id === columnId
          ? { ...column, cardIds: [...column.cardIds, id] }
          : column
      ),
    }));
  };

  const handleDeleteCard = (columnId: string, cardId: string) => {
    updateBoard((prev) => {
      return {
        ...prev,
        cards: Object.fromEntries(
          Object.entries(prev.cards).filter(([id]) => id !== cardId)
        ),
        columns: prev.columns.map((column) =>
          column.id === columnId
            ? {
                ...column,
                cardIds: column.cardIds.filter((id) => id !== cardId),
              }
            : column
        ),
      };
    });
  };

  const activeCard = activeCardId ? cardsById[activeCardId] : null;

  const handleLogoutClick = async () => {
    try {
      if (pendingSaveRef.current) {
        await pendingSaveRef.current;
      }
    } finally {
      onLogout?.();
    }
  };

  const handleSendChat = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!username || isSendingChat) {
      return;
    }

    const prompt = chatPrompt.trim();
    if (!prompt) {
      return;
    }

    const historyForRequest = chatMessages.map((message) => ({
      role: message.role,
      content: message.content,
    }));

    setChatMessages((prev) => [...prev, { role: "user", content: prompt }]);
    setChatPrompt("");
    setChatError(null);
    setIsSendingChat(true);

    try {
      const response = await fetch(`/api/ai/chat/${encodeURIComponent(username)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt,
          conversationHistory: historyForRequest,
        }),
        cache: "no-store",
      });

      if (!response.ok) {
        throw new Error(`AI chat failed: ${response.status}`);
      }

      const payload = (await response.json()) as AIChatResponsePayload;
      if (!payload.reply?.trim()) {
        throw new Error("AI chat reply missing");
      }

      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", content: payload.reply.trim() },
      ]);

      if (payload.boardUpdated) {
        if (payload.board) {
          setBoard(payload.board);
        }
        await refreshBoardAfterAIUpdate();
      }
    } catch {
      setChatError("Unable to get AI response right now. Please try again.");
    } finally {
      setIsSendingChat(false);
    }
  };

  if (isLoadingBoard) {
    return (
      <main className="mx-auto flex min-h-screen max-w-xl items-center justify-center px-6">
        <p className="text-sm font-medium text-[var(--gray-text)]">Loading board...</p>
      </main>
    );
  }

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

      <main className="relative mx-auto flex min-h-screen max-w-[1500px] flex-col gap-10 px-6 pb-16 pt-12">
        <header className="flex flex-col gap-6 rounded-[32px] border border-[var(--stroke)] bg-white/80 p-8 shadow-[var(--shadow)] backdrop-blur">
          {persistenceError ? (
            <div className="rounded-2xl border border-[var(--secondary-purple)]/20 bg-[var(--secondary-purple)]/8 px-4 py-3 text-sm text-[var(--secondary-purple)]">
              {persistenceError}
            </div>
          ) : null}
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
                Single Board Kanban
              </p>
              <h1 className="mt-3 font-display text-4xl font-semibold text-[var(--navy-dark)]">
                Kanban Studio
              </h1>
              <p className="mt-3 max-w-xl text-sm leading-6 text-[var(--gray-text)]">
                Keep momentum visible. Rename columns, drag cards between stages,
                and capture quick notes without getting buried in settings.
              </p>
            </div>
            <div className="rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-5 py-4">
              <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
                Focus
              </p>
              <p className="mt-2 text-lg font-semibold text-[var(--primary-blue)]">
                One board. Five columns. Zero clutter.
              </p>
              {onLogout ? (
                <button
                  type="button"
                  onClick={() => void handleLogoutClick()}
                  disabled={isSavingBoard}
                  className="mt-4 rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-[var(--navy-dark)] transition hover:border-[var(--navy-dark)]"
                >
                  {isSavingBoard ? "Saving..." : "Log out"}
                </button>
              ) : null}
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            {board.columns.map((column) => (
              <div
                key={column.id}
                className="flex items-center gap-2 rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--navy-dark)]"
              >
                <span className="h-2 w-2 rounded-full bg-[var(--accent-yellow)]" />
                {column.title}
              </div>
            ))}
          </div>
        </header>

        <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
          <DndContext
            sensors={sensors}
            collisionDetection={collisionDetectionStrategy}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
          >
            <div className="grid gap-6 lg:grid-cols-5">
              {board.columns.map((column) => (
                <KanbanColumn
                  key={column.id}
                  column={column}
                  cards={column.cardIds.map((cardId) => board.cards[cardId])}
                  onRename={handleRenameColumn}
                  onAddCard={handleAddCard}
                  onDeleteCard={handleDeleteCard}
                />
              ))}
            </div>
            <DragOverlay>
              {activeCard ? (
                <div className="w-[260px]">
                  <KanbanCardPreview card={activeCard} />
                </div>
              ) : null}
            </DragOverlay>
          </DndContext>

          <aside className="rounded-[28px] border border-[var(--stroke)] bg-white/90 p-5 shadow-[var(--shadow)] backdrop-blur">
            <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
              AI Assistant
            </p>
            <h2 className="mt-2 font-display text-2xl font-semibold text-[var(--navy-dark)]">
              Board Chat
            </h2>
            <p className="mt-2 text-sm text-[var(--gray-text)]">
              Ask for board help. Replies can include a direct board update.
            </p>

            <div
              className="mt-4 flex max-h-[420px] min-h-[240px] flex-col gap-3 overflow-y-auto rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] p-3"
              data-testid="ai-chat-messages"
            >
              {chatMessages.length === 0 ? (
                <p className="text-sm text-[var(--gray-text)]">
                  No messages yet. Try: "Summarize what is in progress."
                </p>
              ) : null}

              {chatMessages.map((message, index) => (
                <div
                  key={`${message.role}-${index}`}
                  className={`rounded-2xl px-3 py-2 text-sm ${
                    message.role === "user"
                      ? "ml-8 bg-[var(--primary-blue)] text-white"
                      : "mr-8 border border-[var(--stroke)] bg-white text-[var(--navy-dark)]"
                  }`}
                  data-testid={`ai-chat-${message.role}-message`}
                >
                  {message.content}
                </div>
              ))}

              {isSendingChat ? (
                <div className="mr-8 rounded-2xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--gray-text)]">
                  Thinking...
                </div>
              ) : null}
            </div>

            {chatError ? (
              <p className="mt-3 rounded-xl border border-[var(--secondary-purple)]/20 bg-[var(--secondary-purple)]/8 px-3 py-2 text-sm text-[var(--secondary-purple)]">
                {chatError}
              </p>
            ) : null}

            <form onSubmit={(event) => void handleSendChat(event)} className="mt-4 space-y-3">
              <label className="block text-sm font-medium text-[var(--navy-dark)]">
                Chat prompt
                <textarea
                  value={chatPrompt}
                  onChange={(event) => setChatPrompt(event.target.value)}
                  placeholder="Ask to summarize, prioritize, or update cards..."
                  rows={4}
                  className="mt-1 w-full resize-none rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm outline-none transition focus:border-[var(--primary-blue)]"
                />
              </label>
              <button
                type="submit"
                disabled={isSendingChat || !chatPrompt.trim()}
                className="w-full rounded-full bg-[var(--secondary-purple)] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-white transition disabled:cursor-not-allowed disabled:opacity-60 hover:brightness-110"
              >
                {isSendingChat ? "Sending..." : "Send to AI"}
              </button>
            </form>
          </aside>
        </section>
      </main>
    </div>
  );
};
