import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { ChatPanel } from '@/components/chat/ChatPanel';
import { ConnectionDialog } from '@/components/connections/ConnectionDialog';
import { ConnectionList } from '@/components/connections/ConnectionList';
import { ConversationList } from '@/components/conversations/ConversationList';
import { PlusIcon } from '@/components/icons/PlusIcon';
import { AppHeader } from '@/components/layout/AppHeader';
import { AppSidebar } from '@/components/layout/AppSidebar';
import { SidebarSection } from '@/components/layout/SidebarSection';
import { SessionMeter } from '@/components/session/SessionMeter';
import { Button, EmptyState, IconButton } from '@/components/ui';
import { useAppParams } from '@/hooks/useAppParams';
import { useConnections, useDeleteConnection } from '@/hooks/useConnections';
import { useConversations } from '@/hooks/useConversations';
import { useEndSession } from '@/hooks/useEndSession';
import { useSession } from '@/hooks/useSession';
import { useTimeRemaining } from '@/hooks/useTimeRemaining';

export function WorkspacePage() {
  const navigate = useNavigate();
  const [connectOpen, setConnectOpen] = useState(false);

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

  // A connection id in the URL that no longer exists (deleted, or from an
  // expired session) would otherwise leave the panel pointing at nothing.
  useEffect(() => {
    if (connectionId && connections.isSuccess && !selected) selectConnection(null);
  }, [connectionId, connections.isSuccess, selected, selectConnection]);

  return (
    <div className="flex min-h-dvh flex-col bg-paper">
      <SessionMeter time={time} />
      <AppHeader
        name={session?.name ?? ''}
        time={time}
        onEndSession={() => endSession.mutate()}
        endingSession={endSession.isPending}
      />

      <div className="flex min-h-0 flex-1">
        <AppSidebar>
          <SidebarSection
            title="Databases"
            action={
              <IconButton label="Connect a database" onClick={() => setConnectOpen(true)}>
                <PlusIcon />
              </IconButton>
            }
          >
            <ConnectionList
              connections={list}
              loading={connections.isPending}
              selectedId={connectionId}
              deletingId={deleteConnection.isPending ? deleteConnection.variables : null}
              onSelect={selectConnection}
              onDelete={(id) => deleteConnection.mutate(id)}
            />
          </SidebarSection>

          <SidebarSection title="History">
            {selected ? (
              <ConversationList
                conversations={conversations.data ?? []}
                loading={conversations.isPending}
                selectedId={conversationId}
                onSelect={selectConversation}
              />
            ) : (
              <p className="px-2 py-3 text-[0.8125rem] text-slate">
                Pick a database to see what was asked of it.
              </p>
            )}
          </SidebarSection>
        </AppSidebar>

        {selected ? (
          <ChatPanel
            // Remounting on either change resets the composer and scroll
            // position, so a new chat never opens mid-way down an old one.
            key={`${selected.id}:${conversationId ?? 'new'}`}
            connection={selected}
            conversationId={conversationId}
            onConversationStarted={selectConversation}
          />
        ) : (
          <div className="flex flex-1 items-center justify-center">
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

      <ConnectionDialog
        open={connectOpen}
        onClose={() => setConnectOpen(false)}
        onConnected={(connection) => selectConnection(connection.id)}
      />
    </div>
  );
}
