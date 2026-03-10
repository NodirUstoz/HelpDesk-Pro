/**
 * TicketForm: Create a new support ticket.
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { createTicket } from '../../store/slices/ticketSlice';
import ticketApi from '../../api/ticketApi';

const TicketForm = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    subject: '',
    description: '',
    channel: 'web',
    priority: '',
    tags: [],
  });
  const [priorities, setPriorities] = useState([]);
  const [tags, setTags] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState({});

  useEffect(() => {
    const loadOptions = async () => {
      try {
        const [priorityRes, tagRes] = await Promise.all([
          ticketApi.listPriorities(),
          ticketApi.listTags(),
        ]);
        setPriorities(priorityRes.data.results || priorityRes.data);
        setTags(tagRes.data.results || tagRes.data);
      } catch (err) {
        console.error('Failed to load form options:', err);
      }
    };
    loadOptions();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: '' }));
  };

  const handleTagToggle = (tagId) => {
    setFormData((prev) => ({
      ...prev,
      tags: prev.tags.includes(tagId)
        ? prev.tags.filter((t) => t !== tagId)
        : [...prev.tags, tagId],
    }));
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.subject.trim()) newErrors.subject = 'Subject is required';
    if (!formData.description.trim()) newErrors.description = 'Description is required';
    if (formData.subject.length > 300) newErrors.subject = 'Subject must be under 300 characters';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setSubmitting(true);
    try {
      const result = await dispatch(createTicket(formData)).unwrap();
      navigate(`/tickets/${result.id}`);
    } catch (err) {
      setErrors({ form: err?.detail || 'Failed to create ticket. Please try again.' });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="ticket-form-container">
      <h2>Create New Ticket</h2>

      {errors.form && <div className="alert alert-danger">{errors.form}</div>}

      <form onSubmit={handleSubmit} className="ticket-form">
        {/* Subject */}
        <div className="form-group">
          <label htmlFor="subject">Subject *</label>
          <input
            id="subject"
            type="text"
            name="subject"
            value={formData.subject}
            onChange={handleChange}
            placeholder="Brief description of your issue"
            className={errors.subject ? 'input-error' : ''}
            maxLength={300}
          />
          {errors.subject && <span className="error-text">{errors.subject}</span>}
        </div>

        {/* Description */}
        <div className="form-group">
          <label htmlFor="description">Description *</label>
          <textarea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            placeholder="Provide details about your issue, including any steps to reproduce"
            rows={6}
            className={errors.description ? 'input-error' : ''}
          />
          {errors.description && <span className="error-text">{errors.description}</span>}
        </div>

        {/* Priority */}
        <div className="form-group">
          <label htmlFor="priority">Priority</label>
          <select
            id="priority"
            name="priority"
            value={formData.priority}
            onChange={handleChange}
          >
            <option value="">Select priority</option>
            {priorities.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>

        {/* Channel */}
        <div className="form-group">
          <label htmlFor="channel">Channel</label>
          <select
            id="channel"
            name="channel"
            value={formData.channel}
            onChange={handleChange}
          >
            <option value="web">Web Form</option>
            <option value="email">Email</option>
            <option value="chat">Live Chat</option>
            <option value="phone">Phone</option>
          </select>
        </div>

        {/* Tags */}
        {tags.length > 0 && (
          <div className="form-group">
            <label>Tags</label>
            <div className="tag-selector">
              {tags.map((tag) => (
                <button
                  key={tag.id}
                  type="button"
                  className={`tag-option ${formData.tags.includes(tag.id) ? 'selected' : ''}`}
                  style={{ borderColor: tag.color }}
                  onClick={() => handleTagToggle(tag.id)}
                >
                  {tag.name}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Submit */}
        <div className="form-actions">
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="btn btn-secondary"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={submitting}
            className="btn btn-primary"
          >
            {submitting ? 'Creating...' : 'Create Ticket'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default TicketForm;
