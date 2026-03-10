/**
 * Auth Redux slice: login, logout, registration, user state.
 */
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../../api/axiosConfig';

// --------------------------------------------------------------------------
// Async thunks
// --------------------------------------------------------------------------

export const loginUser = createAsyncThunk(
  'auth/login',
  async ({ email, password }, { rejectWithValue }) => {
    try {
      const { data } = await api.post('/auth/login/', { email, password });
      localStorage.setItem('tokens', JSON.stringify(data.tokens));
      localStorage.setItem('user', JSON.stringify(data.user));
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data || { detail: 'Login failed' });
    }
  },
);

export const registerUser = createAsyncThunk(
  'auth/register',
  async (formData, { rejectWithValue }) => {
    try {
      const { data } = await api.post('/auth/register/', formData);
      localStorage.setItem('tokens', JSON.stringify(data.tokens));
      localStorage.setItem('user', JSON.stringify(data.user));
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data || { detail: 'Registration failed' });
    }
  },
);

export const logoutUser = createAsyncThunk('auth/logout', async () => {
  const tokens = JSON.parse(localStorage.getItem('tokens') || '{}');
  try {
    await api.post('/auth/logout/', { refresh: tokens.refresh });
  } catch {
    // Ignore errors on logout
  }
  localStorage.removeItem('tokens');
  localStorage.removeItem('user');
});

export const fetchCurrentUser = createAsyncThunk(
  'auth/fetchCurrentUser',
  async (_, { rejectWithValue }) => {
    try {
      const { data } = await api.get('/auth/me/');
      localStorage.setItem('user', JSON.stringify(data));
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data);
    }
  },
);

export const changePassword = createAsyncThunk(
  'auth/changePassword',
  async ({ oldPassword, newPassword }, { rejectWithValue }) => {
    try {
      const { data } = await api.post('/auth/password/change/', {
        old_password: oldPassword,
        new_password: newPassword,
      });
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data);
    }
  },
);

// --------------------------------------------------------------------------
// Slice
// --------------------------------------------------------------------------

const storedUser = localStorage.getItem('user');
const storedTokens = localStorage.getItem('tokens');

const initialState = {
  user: storedUser ? JSON.parse(storedUser) : null,
  tokens: storedTokens ? JSON.parse(storedTokens) : null,
  isAuthenticated: !!storedTokens,
  loading: false,
  error: null,
};

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError(state) {
      state.error = null;
    },
    setUser(state, action) {
      state.user = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      // Login
      .addCase(loginUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload.user;
        state.tokens = action.payload.tokens;
        state.isAuthenticated = true;
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })

      // Register
      .addCase(registerUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(registerUser.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload.user;
        state.tokens = action.payload.tokens;
        state.isAuthenticated = true;
      })
      .addCase(registerUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })

      // Logout
      .addCase(logoutUser.fulfilled, (state) => {
        state.user = null;
        state.tokens = null;
        state.isAuthenticated = false;
        state.error = null;
      })

      // Fetch current user
      .addCase(fetchCurrentUser.fulfilled, (state, action) => {
        state.user = action.payload;
      })

      // Change password
      .addCase(changePassword.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(changePassword.fulfilled, (state) => {
        state.loading = false;
      })
      .addCase(changePassword.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export const { clearError, setUser } = authSlice.actions;

// Selectors
export const selectUser = (state) => state.auth.user;
export const selectIsAuthenticated = (state) => state.auth.isAuthenticated;
export const selectAuthLoading = (state) => state.auth.loading;
export const selectAuthError = (state) => state.auth.error;
export const selectIsAgent = (state) =>
  state.auth.user?.role === 'agent' || state.auth.user?.role === 'admin';
export const selectIsAdmin = (state) => state.auth.user?.role === 'admin';

export default authSlice.reducer;
