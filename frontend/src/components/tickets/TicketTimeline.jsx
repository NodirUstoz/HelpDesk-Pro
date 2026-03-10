/**
 * TicketTimeline: Chronological display of ticket messages and system events.
 */
import React, { useRef, useEffect } from 'react';
import { formatDateTime } from '../../utils/formatters';

const TicketTimeline = ({ messages, currentUserId }) => {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  if (!messages || messages.length === 0) {
    return (
      <div className="ticket-timeline empty">
        <p className="text-muted">No messages yet.</p>
      </div>
    );
  }

  const getMessageClass = (message) => {
    if (message.message_type === 'system') return 'timeline-item--system';
    if (message.message_type === 'note') return 'timeline-item--note';
    if (message.sender === currentUserId) return 'timeline-item--self';
    return 'timeline-item--other';
  };

  const getMessageLabel = (message) => {
    if (message.message_type === 'system') return 'System';
    if (message.message_type === 'note') return 'Internal Note';
    return null;
  };

  const getInitials = (name) => {
    if (!name) return '?';
    return name
      .split(' ')
      .map((part) => part[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <div className="ticket-timeline">
      <h4>Conversation</h4>
      <div className="timeline-list">
        {messages.map((message) => {
          const senderName =
            message.sender_detail?.first_name && message.sender_detail?.last_name
              ? `${message.sender_detail.first_name} ${message.sender_detail.last_name}`
              : message.sender_detail?.email || 'System';

          return (
            <div key={message.id} className={`timeline-item ${getMessageClass(message)}`}>
              {message.message_type !== 'system' && (
                <div className="timeline-item__avatar">
                  <div className="avatar-circle">{getInitials(senderName)}</div>
                </div>
              )}

              <div className="timeline-item__content">
                <div className="timeline-item__header">
                  <span className="sender-name">{senderName}</span>
                  {getMessageLabel(message) && (
                    <span className="message-label">{getMessageLabel(message)}</span>
                  )}
                  <span className="timestamp">{formatDateTime(message.created_at)}</span>
                </div>
                <div className="timeline-item__body">
                  {message.body.split('\n').map((line, idx) => (
                    <React.Fragment key={idx}>
                      {line}
                      {idx < message.body.split('\n').length - 1 && <br />}
                    </React.Fragment>
                  ))}
                </div>

                {/* Attachments */}
                {message.attachments && message.attachments.length > 0 && (
                  <div className="timeline-item__attachments">
                    {message.attachments.map((att) => (
                      <a
                        key={att.id}
                        href={att.file}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="attachment-link"
                      >
                        <span className="attachment-icon">&#128206;</span>
                        {att.filename}
                        <span className="attachment-size">
                          ({(att.file_size / 1024).toFixed(1)} KB)
                        </span>
                      </a>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};

export default TicketTimeline;
