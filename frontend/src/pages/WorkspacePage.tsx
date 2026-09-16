import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { ChatPanel } from '@/components/chat/ChatPanel';
import { ConnectionDialog } from '@/components/connections/ConnectionDialog';
import { TargetDatabase } from '@/components/connections/TargetDatabase';
import { ConversationList } from '@/components/conversations/ConversationList';
import { NewQueryButton } from '@/components/conversations/NewQueryButton';
import { AppHeader } from '@/components/layout/AppHeader';
import { AppSidebar } from '@/components/layout/AppSidebar';
import { SidebarBrand } from '@/components/layout/SidebarBrand';
import { SidebarFooter } from '@/components/layout/SidebarFooter';
import { Button, EmptyState } from '@/components/ui';
import { useAppParams } from '@/hooks/useAppParams';
import { useConnections, useDeleteConnection } from '@/hooks/useConnections';
import { useConversations } from '@/hooks/useConversations';
import { useEndSession } from '@/hooks/useEndSession';
import { useSession } from '@/hooks/useSession';
import { useTimeRemaining } from '@/hooks/useTimeRemaining';

/** "Calm_Moss_6490" -> "CM", for the question bubbles. */
function initialsOf(name: string): string {
  const parts = name.split(/[\s_-]+/).filter(Boolean);
  return (parts.slice(0, 2).map((part) => part[0]).join('') || '?').toUpperCase();
}

export function WorkspacePage() {
  const navigate = useNavigate();
  const [connectOpen, setConnectOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  const { data: session } = useSession();
  const params = useAppParams();
  const { sessionId, connectionId, conversationId, syncSession, selectConnection, selectConversation } =
    params;

  const connections = useConnections();
  const conversations = useConversations(connectionId);
  const time = useTimeRemaining(session?.createdAt, session?.expiresAt);

  const endSession = useEndSession(() => {
    params.clear();
    navigate('/', { replace: true });
  });

  const deleteConnection = useDeleteConnection((deletedId) => {
    if (deletedId === connectionId) selectConnection(null);
  });

  // The cookie is the authority on which session this is. If the URL disagrees
  // -- a stale bookmark, a link from someone else -- the URL is corrected.
  useEffect(() => {
    if (session && sessionId !== session.sessionId) syncSession(session.sessionId);
  }, [session, sessionId, syncSession]);

  const list = connections.data ?? [];
  const selected = useMemo(
    () => list.find((connection) => connection.id === connectionId) ?? null,
    [list, connectionId],
  );

  // Picking a database reopens where that database was left off.
  //
  // Selecting a connection cannot carry a conversation with it -- the old one
  // belonged to a different database -- so the id is cleared and the most
  // recent conversation is restored once the list arrives. Once per selection,
  // tracked here, or "New query" would be undone the instant it was pressed. A
  // conversation already named in the URL is left alone: that is a deep link,
  // and it is more specific than "the latest".
  const resumedFor = useRef<string | null>(null);
  useEffect(() => {
    if (!connectionId) {
      resumedFor.current = null;
      return;
    }
    if (resumedFor.current === connectionId || !conversations.isSuccess) return;
    resumedFor.current = connectionId;

    const mostRecent = conversations.data?.[0];
    if (mostRecent && !conversationId) selectConversation(mostRecent.id);
  }, [connectionId, conversationId, conversations.isSuccess, conversations.data, selectConversation]);

  // A connection id in the URL that no longer exists (deleted, or from an
  // expired session) would otherwise leave the panel pointing at nothing.
  // Never while a fetch is in flight: mid-refetch the list is not yet the
  // answer, and clearing then would throw away a valid selection.
  useEffect(() => {
    if (connectionId && connections.isSuccess && !connections.isFetching && !selected) {
      selectConnection(null);
    }
  }, [connectionId, connections.isSuccess, connections.isFetching, selected, selectConnection]);

  // Stable, because NewQueryButton binds a keyboard shortcut to it.
  const startNewQuery = useCallback(() => {
    selectConversation(null);
    setMenuOpen(false);
  }, [selectConversation]);

  const name = session?.name ?? '';

  return (
    <div className="flex h-dvh flex-col overflow-hidden bg-paper">
      <div className="flex min-h-0 min-w-0 flex-1 overflow-hidden">
        <AppSidebar open={menuOpen} onClose={() => setMenuOpen(false)}>
          <SidebarBrand />

          <div className="px-4 pb-1">
            <NewQueryButton onClick={startNewQuery} disabled={!selected || !conversationId} />
          </div>

          <TargetDatabase
            connections={list}
            loading={connections.isPending}
            selectedId={connectionId}
            deletingId={deleteConnection.isPending ? deleteConnection.variables : null}
            onSelect={(id) => {
              // Re-clicking the open database would otherwise clear the
              // conversation and bounce through the empty state.
              if (id !== connectionId) selectConnection(id);
              setMenuOpen(false);
            }}
            onDelete={(id) => deleteConnection.mutate(id)}
            onConnect={() => setConnectOpen(true)}
          />

          {/* The history is the only thing here that grows, so it takes the
              slack and scrolls, and the footer below stays on the floor. */}
          <div className="min-h-0 flex-1 overflow-y-auto px-2 py-3">
            {selected ? (
              <ConversationList
                conversations={conversations.data ?? []}
                loading={conversations.isPending}
                selectedId={conversationId}
                onSelect={(id) => {
                  selectConversation(id);
                  setMenuOpen(false);
                }}
              />
            ) : (
              <p className="px-2.5 py-3 text-[0.8125rem] text-muted">
                Pick a database to see what was asked of it.
              </p>
            )}
          </div>

          {session && (
            <SidebarFooter
              name={name}
              sessionId={session.sessionId}
              onEndSession={() => endSession.mutate()}
              ending={endSession.isPending}
            />
          )}
        </AppSidebar>

        <div className="flex min-h-0 min-w-0 flex-1 flex-col">
          <AppHeader
            sessionId={session?.sessionId ?? ''}
            connectionName={selected?.name ?? null}
            time={time}
            onOpenMenu={() => setMenuOpen(true)}
            onEndSession={() => endSession.mutate()}
            endingSession={endSession.isPending}
          />

          {selected ? (
            <ChatPanel
              // Remounting on either change resets the composer and scroll
              // position, so a new chat never opens mid-way down an old one.
              key={`${selected.id}:${conversationId ?? 'new'}`}
              connection={selected}
              conversationId={conversationId}
              userInitials={initialsOf(name)}
              onConversationStarted={selectConversation}
            />
          ) : (
            <div className="flex min-h-0 min-w-0 flex-1 items-center justify-center">
              <EmptyState
                title={list.length === 0 ? 'No database connected yet' : 'Pick a database'}
                description={
                  list.length === 0
                    ? 'Connect one with a read-only account and start asking questions about it.'
                    : 'Choose one from the sidebar to start asking questions.'
                }
                action={
                  list.length === 0 ? (
                    <Button onClick={() => setConnectOpen(true)}>Connect a database</Button>
                  ) : null
                }
              />
            </div>
          )}
        </div>
      </div>

      <ConnectionDialog
        open={connectOpen}
        onClose={() => setConnectOpen(false)}
        onConnected={(connection) => selectConnection(connection.id)}
      />
    </div>
  );
}
