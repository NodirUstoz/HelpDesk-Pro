/**
 * TicketList: Paginated, filterable table of support tickets.
 */
import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Link } from 'react-router-dom';
import {
  fetchTickets,
  setFilters,
  selectTickets,
  selectTicketPagination,
  selectTicketLoading,
  selectTicketFilters,
} from '../../store/slices/ticketSlice';
import { formatRelativeTime, priorityColor } from '../../utils/formatters';

const TicketList = () => {
  const dispatch = useDispatch();
  const tickets = useSelector(selectTickets);
  const pagination = useSelector(selectTicketPagination);
  const loading = useSelector(selectTicketLoading);
  const filters = useSelector(selectTicketFilters);
  const [searchInput, setSearchInput] = useState('');

  useEffect(() => {
    dispatch(fetchTickets({ ...filters, page: pagination.currentPage }));
  }, [dispatch, filters, pagination.currentPage]);

  const handleFilterChange = (key, value) => {
    dispatch(setFilters({ [key]: value }));
  };

  const handleSearch = (e) => {
    e.preventDefault();
    dispatch(setFilters({ search: searchInput }));
  };

  const handlePageChange = (page) => {
    dispatch(fetchTickets({ ...filters, page }));
  };

  return (
    <div className="ticket-list">
      <div className="ticket-list__header">
        <h2>Support Tickets</h2>
        <Link to="/tickets/new" className="btn btn-primary">
          New Ticket
        </Link>
      </div>

      {/* Filters bar */}
      <div className="ticket-list__filters">
        <form onSubmit={handleSearch} className="search-form">
          <input
            type="text"
            placeholder="Search tickets..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="search-input"
          />
          <button type="submit" className="btn btn-sm">Search</button>
        </form>

        <select
          value={filters.status}
          onChange={(e) => handleFilterChange('status', e.target.value)}
          className="filter-select"
        >
          <option value="">All Statuses</option>
          <option value="open">Open</option>
          <option value="in-progress">In Progress</option>
          <option value="waiting-for-customer">Waiting for Customer</option>
          <option value="resolved">Resolved</option>
          <option value="closed">Closed</option>
        </select>

        <select
          value={filters.priority}
          onChange={(e) => handleFilterChange('priority', e.target.value)}
          className="filter-select"
        >
          <option value="">All Priorities</option>
          <option value="urgent">Urgent</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>

        <select
          value={filters.ordering}
          onChange={(e) => handleFilterChange('ordering', e.target.value)}
          className="filter-select"
        >
          <option value="-created_at">Newest First</option>
          <option value="created_at">Oldest First</option>
          <option value="-updated_at">Recently Updated</option>
          <option value="priority__level">Priority (High to Low)</option>
        </select>
      </div>

      {/* Ticket table */}
      {loading ? (
        <div className="loading-spinner">Loading tickets...</div>
      ) : (
        <>
          <table className="ticket-table">
            <thead>
              <tr>
                <th>Ticket #</th>
                <th>Subject</th>
                <th>Customer</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Agent</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {tickets.length === 0 ? (
                <tr>
                  <td colSpan="7" className="empty-state">
                    No tickets found matching your criteria.
                  </td>
                </tr>
              ) : (
                tickets.map((ticket) => (
                  <tr key={ticket.id} className={ticket.is_escalated ? 'escalated' : ''}>
                    <td>
                      <Link to={`/tickets/${ticket.id}`} className="ticket-number">
                        {ticket.ticket_number}
                      </Link>
                    </td>
                    <td className="ticket-subject">
                      <Link to={`/tickets/${ticket.id}`}>{ticket.subject}</Link>
                      {ticket.sla_response_breached && (
                        <span className="badge badge-danger" title="SLA Breached">SLA</span>
                      )}
                      {ticket.is_escalated && (
                        <span className="badge badge-warning" title="Escalated">ESC</span>
                      )}
                    </td>
                    <td>{ticket.customer_name}</td>
                    <td>
                      <span
                        className="priority-badge"
                        style={{ backgroundColor: ticket.priority_detail?.color || '#6B7280' }}
                      >
                        {ticket.priority_detail?.name || 'None'}
                      </span>
                    </td>
                    <td>
                      <span
                        className="status-badge"
                        style={{ backgroundColor: ticket.status_detail?.color || '#6B7280' }}
                      >
                        {ticket.status_detail?.name || 'None'}
                      </span>
                    </td>
                    <td>{ticket.agent_name || <span className="text-muted">Unassigned</span>}</td>
                    <td className="text-muted">{formatRelativeTime(ticket.created_at)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>

          {/* Pagination */}
          {pagination.totalPages > 1 && (
            <div className="pagination">
              <button
                onClick={() => handlePageChange(pagination.currentPage - 1)}
                disabled={pagination.currentPage <= 1}
                className="btn btn-sm"
              >
                Previous
              </button>
              <span className="pagination-info">
                Page {pagination.currentPage} of {pagination.totalPages}
                {' '}({pagination.count} total)
              </span>
              <button
                onClick={() => handlePageChange(pagination.currentPage + 1)}
                disabled={pagination.currentPage >= pagination.totalPages}
                className="btn btn-sm"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default TicketList;
