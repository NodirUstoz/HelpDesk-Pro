/**
 * Ticket Redux slice: list, detail, create, update tickets.
 */
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import ticketApi from '../../api/ticketApi';

// --------------------------------------------------------------------------
// Async thunks
// --------------------------------------------------------------------------

export const fetchTickets = createAsyncThunk(
  'tickets/fetchTickets',
  async (params = {}, { rejectWithValue }) => {
    try {
      const { data } = await ticketApi.list(params);
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data);
    }
  },
);

export const fetchTicketDetail = createAsyncThunk(
  'tickets/fetchTicketDetail',
  async (id, { rejectWithValue }) => {
    try {
      const { data } = await ticketApi.get(id);
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data);
    }
  },
);

export const createTicket = createAsyncThunk(
  'tickets/createTicket',
  async (ticketData, { rejectWithValue }) => {
    try {
      const { data } = await ticketApi.create(ticketData);
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data);
    }
  },
);

export const updateTicket = createAsyncThunk(
  'tickets/updateTicket',
  async ({ id, data: ticketData }, { rejectWithValue }) => {
    try {
      const { data } = await ticketApi.update(id, ticketData);
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data);
    }
  },
);

export const assignTicket = createAsyncThunk(
  'tickets/assignTicket',
  async ({ id, data: assignData }, { rejectWithValue }) => {
    try {
      const { data } = await ticketApi.assign(id, assignData);
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data);
    }
  },
);

export const closeTicket = createAsyncThunk(
  'tickets/closeTicket',
  async (id, { rejectWithValue }) => {
    try {
      const { data } = await ticketApi.close(id);
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data);
    }
  },
);

export const fetchTicketStats = createAsyncThunk(
  'tickets/fetchStats',
  async (_, { rejectWithValue }) => {
    try {
      const { data } = await ticketApi.getStats();
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data);
    }
  },
);

export const addTicketMessage = createAsyncThunk(
  'tickets/addMessage',
  async ({ ticketId, messageData }, { rejectWithValue }) => {
    try {
      const { data } = await ticketApi.createMessage(ticketId, messageData);
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data);
    }
  },
);

// --------------------------------------------------------------------------
// Slice
// --------------------------------------------------------------------------

const initialState = {
  tickets: [],
  currentTicket: null,
  stats: null,
  pagination: {
    count: 0,
    totalPages: 0,
    currentPage: 1,
    pageSize: 20,
  },
  filters: {
    status: '',
    priority: '',
    assigned_agent: '',
    search: '',
    ordering: '-created_at',
  },
  loading: false,
  detailLoading: false,
  error: null,
};

const ticketSlice = createSlice({
  name: 'tickets',
  initialState,
  reducers: {
    setFilters(state, action) {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters(state) {
      state.filters = initialState.filters;
    },
    clearCurrentTicket(state) {
      state.currentTicket = null;
    },
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch tickets
      .addCase(fetchTickets.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchTickets.fulfilled, (state, action) => {
        state.loading = false;
        state.tickets = action.payload.results || action.payload;
        if (action.payload.count !== undefined) {
          state.pagination = {
            count: action.payload.count,
            totalPages: action.payload.total_pages,
            currentPage: action.payload.current_page,
            pageSize: action.payload.page_size,
          };
        }
      })
      .addCase(fetchTickets.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })

      // Fetch ticket detail
      .addCase(fetchTicketDetail.pending, (state) => {
        state.detailLoading = true;
      })
      .addCase(fetchTicketDetail.fulfilled, (state, action) => {
        state.detailLoading = false;
        state.currentTicket = action.payload;
      })
      .addCase(fetchTicketDetail.rejected, (state, action) => {
        state.detailLoading = false;
        state.error = action.payload;
      })

      // Create ticket
      .addCase(createTicket.fulfilled, (state, action) => {
        state.tickets.unshift(action.payload);
      })

      // Update ticket / assign / close
      .addCase(updateTicket.fulfilled, (state, action) => {
        const idx = state.tickets.findIndex((t) => t.id === action.payload.id);
        if (idx !== -1) state.tickets[idx] = action.payload;
        if (state.currentTicket?.id === action.payload.id) {
          state.currentTicket = action.payload;
        }
      })
      .addCase(assignTicket.fulfilled, (state, action) => {
        if (state.currentTicket?.id === action.payload.id) {
          state.currentTicket = action.payload;
        }
      })
      .addCase(closeTicket.fulfilled, (state, action) => {
        if (state.currentTicket?.id === action.payload.id) {
          state.currentTicket = action.payload;
        }
      })

      // Stats
      .addCase(fetchTicketStats.fulfilled, (state, action) => {
        state.stats = action.payload;
      })

      // Add message
      .addCase(addTicketMessage.fulfilled, (state, action) => {
        if (state.currentTicket) {
          state.currentTicket.messages = [
            ...(state.currentTicket.messages || []),
            action.payload,
          ];
        }
      });
  },
});

export const { setFilters, clearFilters, clearCurrentTicket, clearError } =
  ticketSlice.actions;

// Selectors
export const selectTickets = (state) => state.tickets.tickets;
export const selectCurrentTicket = (state) => state.tickets.currentTicket;
export const selectTicketStats = (state) => state.tickets.stats;
export const selectTicketPagination = (state) => state.tickets.pagination;
export const selectTicketLoading = (state) => state.tickets.loading;
export const selectTicketFilters = (state) => state.tickets.filters;

export default ticketSlice.reducer;
