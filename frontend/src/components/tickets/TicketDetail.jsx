/**
 * TicketDetail: Full ticket view with messages, assignment, and actions.
 */
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import {
  fetchTicketDetail,
  assignTicket,
  closeTicket,
  addTicketMessage,
  selectCurrentTicket,
  selectTicketLoading,
} from '../../store/slices/ticketSlice';
import { selectUser, selectIsAgent } from '../../store/slices/authSlice';
import TicketTimeline from './TicketTimeline';
import { formatDateTime } from '../../utils/formatters';

const TicketDetail = () => {
  const { id } = useParams();
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const ticket = useSelector(selectCurrentTicket);
  const loading = useSelector(selectTicketLoading);
  const user = useSelector(selectUser);
  const isAgent = useSelector(selectIsAgent);

  const [replyBody, setReplyBody] = useState('');
  const [isNote, setIsNote] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    dispatch(fetchTicketDetail(id));
  }, [dispatch, id]);

  const handleReply = async (e) => {
    e.preventDefault();
    if (!replyBody.trim()) return;

    setSubmitting(true);
    await dispatch(
      addTicketMessage({
        ticketId: id,
        messageData: {
          body: replyBody,
          message_type: isNote ? 'note' : 'reply',
          is_customer_visible: !isNote,
          ticket: id,
        },
      }),
    );
    setReplyBody('');
    setSubmitting(false);
    dispatch(fetchTicketDetail(id));
  };

  const handleClose = async () => {
    if (window.confirm('Are you sure you want to close this ticket?')) {
      await dispatch(closeTicket(id));
      dispatch(fetchTicketDetail(id));
    }
  };

  const handleAssignToMe = async () => {
    await dispatch(assignTicket({ id, data: { assigned_agent: user.id } }));
    dispatch(fetchTicketDetail(id));
  };

  if (loading || !ticket) {
    return <div className="loading-spinner">Loading ticket...</div>;
  }

  const isClosed = ticket.status_detail?.is_closed;

  return (
    <div className="ticket-detail">
      {/* Header */}
      <div className="ticket-detail__header">
        <div className="ticket-detail__title">
          <button onClick={() => navigate(-1)} className="btn btn-sm btn-back">
            Back
          </button>
          <h2>
            <span className="ticket-number">{ticket.ticket_number}</span>
            {ticket.subject}
          </h2>
        </div>

        {isAgent && (
          <div className="ticket-detail__actions">
            {!ticket.assigned_agent && (
              <button onClick={handleAssignToMe} className="btn btn-primary btn-sm">
                Assign to Me
              </button>
            )}
            {!isClosed && (
              <button onClick={handleClose} className="btn btn-danger btn-sm">
                Close Ticket
              </button>
            )}
          </div>
        )}
      </div>

      {/* Sidebar info */}
      <div className="ticket-detail__content">
        <div className="ticket-detail__sidebar">
          <div className="info-card">
            <h4>Details</h4>
            <dl>
              <dt>Status</dt>
              <dd>
                <span
                  className="status-badge"
                  style={{ backgroundColor: ticket.status_detail?.color }}
                >
                  {ticket.status_detail?.name}
                </span>
              </dd>

              <dt>Priority</dt>
              <dd>
                <span
                  className="priority-badge"
                  style={{ backgroundColor: ticket.priority_detail?.color }}
                >
                  {ticket.priority_detail?.name}
                </span>
              </dd>

              <dt>Channel</dt>
              <dd>{ticket.channel}</dd>

              <dt>Customer</dt>
              <dd>
                {ticket.customer_detail?.first_name} {ticket.customer_detail?.last_name}
                <br />
                <span className="text-muted">{ticket.customer_detail?.email}</span>
              </dd>

              <dt>Assigned Agent</dt>
              <dd>
                {ticket.agent_detail
                  ? `${ticket.agent_detail.first_name} ${ticket.agent_detail.last_name}`
                  : 'Unassigned'}
              </dd>

              <dt>Created</dt>
              <dd>{formatDateTime(ticket.created_at)}</dd>

              <dt>Updated</dt>
              <dd>{formatDateTime(ticket.updated_at)}</dd>
            </dl>
          </div>

          {/* SLA info */}
          {(ticket.sla_response_due || ticket.sla_resolution_due) && (
            <div className="info-card">
              <h4>SLA</h4>
              <dl>
                {ticket.sla_response_due && (
                  <>
                    <dt>Response Due</dt>
                    <dd className={ticket.sla_response_breached ? 'text-danger' : ''}>
                      {formatDateTime(ticket.sla_response_due)}
                      {ticket.sla_response_breached && ' (BREACHED)'}
                    </dd>
                  </>
                )}
                {ticket.sla_resolution_due && (
                  <>
                    <dt>Resolution Due</dt>
                    <dd className={ticket.sla_resolution_breached ? 'text-danger' : ''}>
                      {formatDateTime(ticket.sla_resolution_due)}
                      {ticket.sla_resolution_breached && ' (BREACHED)'}
                    </dd>
                  </>
                )}
                {ticket.first_response_at && (
                  <>
                    <dt>First Response</dt>
                    <dd>{formatDateTime(ticket.first_response_at)}</dd>
                  </>
                )}
              </dl>
            </div>
          )}

          {/* Tags */}
          {ticket.tags_detail?.length > 0 && (
            <div className="info-card">
              <h4>Tags</h4>
              <div className="tag-list">
                {ticket.tags_detail.map((tag) => (
                  <span key={tag.id} className="tag" style={{ borderColor: tag.color }}>
                    {tag.name}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Main content: description + messages timeline */}
        <div className="ticket-detail__main">
          <div className="ticket-description">
            <h4>Description</h4>
            <p>{ticket.description}</p>
          </div>

          <TicketTimeline messages={ticket.messages || []} currentUserId={user?.id} />

          {/* Reply form */}
          {!isClosed && (
            <form onSubmit={handleReply} className="reply-form">
              <div className="reply-form__header">
                <h4>{isNote ? 'Internal Note' : 'Reply'}</h4>
                {isAgent && (
                  <label className="toggle-note">
                    <input
                      type="checkbox"
                      checked={isNote}
                      onChange={(e) => setIsNote(e.target.checked)}
                    />
                    Internal Note
                  </label>
                )}
              </div>
              <textarea
                value={replyBody}
                onChange={(e) => setReplyBody(e.target.value)}
                placeholder={isNote ? 'Add an internal note...' : 'Write your reply...'}
                rows={4}
                required
                className={`reply-textarea ${isNote ? 'note-mode' : ''}`}
              />
              <button type="submit" disabled={submitting} className="btn btn-primary">
                {submitting ? 'Sending...' : isNote ? 'Add Note' : 'Send Reply'}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default TicketDetail;
