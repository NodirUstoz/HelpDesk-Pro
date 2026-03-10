/**
 * Redux store configuration.
 */
import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import ticketReducer from './slices/ticketSlice';
import chatReducer from './slices/chatSlice';

const store = configureStore({
  reducer: {
    auth: authReducer,
    tickets: ticketReducer,
    chat: chatReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['chat/addMessage', 'chat/setWebSocket'],
        ignoredPaths: ['chat.webSocket'],
      },
    }),
  devTools: process.env.NODE_ENV !== 'production',
});

export default store;
