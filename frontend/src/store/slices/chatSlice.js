/**
 * Chat Redux slice: sessions, messages, WebSocket state.
 */
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../../api/axiosConfig';

// --------------------------------------------------------------------------
// Async thunks
// --------------------------------------------------------------------------

export const fetchChatSessions = createAsyncThunk(
  'chat/fetchSessions',
  async (params = {}, { rejectWithValue }) => {
    try {
      const { data } = await api.get('/chat/sessions/', { params });
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data);
    }
  },
);

export const fetchWaitingSessions = createAsyncThunk(
  'chat/fetchWaiting',
  async (_, { rejectWithValue }) => {
    try {
      const { data } = await api.get('/chat/sessions/waiting/');
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data);
    }
  },
);

export const fetchSessionDetail = createAsyncThunk(
  'chat/fetchSessionDetail',
  async (id, { rejectWithValue }) => {
    try {
      const { data } = await api.get(`/chat/sessions/${id}/`);
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data);
    }
  },
);

export const startChatSession = createAsyncThunk(
  'chat/startSession',
  async (sessionData, { rejectWithValue }) => {
    try {
      const { data } = await api.post('/chat/sessions/', sessionData);
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data);
    }
  },
);

export const acceptChatSession = createAsyncThunk(
  'chat/acceptSession',
  async (id, { rejectWithValue }) => {
    try {
      const { data } = await api.post(`/chat/sessions/${id}/accept/`);
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data);
    }
  },
);

export const endChatSession = createAsyncThunk(
  'chat/endSession',
  async (id, { rejectWithValue }) => {
    try {
      const { data } = await api.post(`/chat/sessions/${id}/end/`);
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data);
    }
  },
);

export const rateChatSession = createAsyncThunk(
  'chat/rateSession',
  async ({ id, rating, ratingComment }, { rejectWithValue }) => {
    try {
      const { data } = await api.post(`/chat/sessions/${id}/rate/`, {
        rating,
        rating_comment: ratingComment,
      });
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data);
    }
  },
);

export const fetchChatStats = createAsyncThunk(
  'chat/fetchStats',
  async (_, { rejectWithValue }) => {
    try {
      const { data } = await api.get('/chat/sessions/stats/');
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
  sessions: [],
  waitingSessions: [],
  activeSession: null,
  messages: [],
  stats: null,
  typingUsers: {},
  loading: false,
  error: null,
};

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    addMessage(state, action) {
      state.messages.push(action.payload);
    },
    setTypingUser(state, action) {
      const { userId, userName, isTyping } = action.payload;
      if (isTyping) {
        state.typingUsers[userId] = userName;
      } else {
        delete state.typingUsers[userId];
      }
    },
    markMessagesRead(state, action) {
      const messageIds = action.payload;
      state.messages = state.messages.map((msg) =>
        messageIds.includes(msg.message_id) ? { ...msg, is_read: true } : msg,
      );
    },
    clearActiveSession(state) {
      state.activeSession = null;
      state.messages = [];
      state.typingUsers = {};
    },
    sessionEnded(state, action) {
      if (state.activeSession?.id === action.payload) {
        state.activeSession = { ...state.activeSession, status: 'closed' };
      }
      state.sessions = state.sessions.map((s) =>
        s.id === action.payload ? { ...s, status: 'closed' } : s,
      );
    },
    removeWaitingSession(state, action) {
      state.waitingSessions = state.waitingSessions.filter(
        (s) => s.id !== action.payload,
      );
    },
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Sessions list
      .addCase(fetchChatSessions.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchChatSessions.fulfilled, (state, action) => {
        state.loading = false;
        state.sessions = action.payload.results || action.payload;
      })
      .addCase(fetchChatSessions.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })

      // Waiting sessions
      .addCase(fetchWaitingSessions.fulfilled, (state, action) => {
        state.waitingSessions = action.payload;
      })

      // Session detail
      .addCase(fetchSessionDetail.fulfilled, (state, action) => {
        state.activeSession = action.payload;
        state.messages = action.payload.messages || [];
      })

      // Start session
      .addCase(startChatSession.fulfilled, (state, action) => {
        state.activeSession = action.payload;
        state.sessions.unshift(action.payload);
      })

      // Accept session
      .addCase(acceptChatSession.fulfilled, (state, action) => {
        state.activeSession = action.payload;
        state.waitingSessions = state.waitingSessions.filter(
          (s) => s.id !== action.payload.id,
        );
      })

      // End session
      .addCase(endChatSession.fulfilled, (state, action) => {
        state.activeSession = action.payload;
      })

      // Rate session
      .addCase(rateChatSession.fulfilled, (state, action) => {
        state.activeSession = action.payload;
      })

      // Stats
      .addCase(fetchChatStats.fulfilled, (state, action) => {
        state.stats = action.payload;
      });
  },
});

export const {
  addMessage,
  setTypingUser,
  markMessagesRead,
  clearActiveSession,
  sessionEnded,
  removeWaitingSession,
  clearError,
} = chatSlice.actions;

// Selectors
export const selectChatSessions = (state) => state.chat.sessions;
export const selectWaitingSessions = (state) => state.chat.waitingSessions;
export const selectActiveSession = (state) => state.chat.activeSession;
export const selectChatMessages = (state) => state.chat.messages;
export const selectTypingUsers = (state) => state.chat.typingUsers;
export const selectChatStats = (state) => state.chat.stats;
export const selectChatLoading = (state) => state.chat.loading;

export default chatSlice.reducer;
