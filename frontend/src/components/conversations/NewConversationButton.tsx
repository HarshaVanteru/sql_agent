import { PlusIcon } from '@/components/icons/PlusIcon';
import { IconButton } from '@/components/ui';

interface NewConversationButtonProps {
  onClick: () => void;
  disabled: boolean;
}

/**
 * Starts a fresh conversation against the same database.
 *
 * Needed the moment picking a database resumes its last conversation: without
 * it there is no way back out of that thread, and every new question would
 * carry the old one's context whether or not it was meant to.
 */
export function NewConversationButton({ onClick, disabled }: NewConversationButtonProps) {
  return (
    <IconButton label="New conversation" onClick={onClick} disabled={disabled}>
      <PlusIcon />
    </IconButton>
  );
}
