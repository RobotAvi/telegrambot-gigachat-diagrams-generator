import api from './api';

export const authService = {
  async login(email, password) {
    const response = await api.post('/auth/login', {
      username: email, // FastAPI OAuth2 expects username
      password,
    }, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      transformRequest: [(data) => {
        return Object.keys(data)
          .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(data[key])}`)
          .join('&');
      }],
    });
    return response;
  },

  async register(userData) {
    const response = await api.post('/auth/register', userData);
    return response;
  },

  async getCurrentUser() {
    const response = await api.get('/auth/me');
    return response;
  },

  async updateProfile(userData) {
    const response = await api.put('/users/profile', userData);
    return response;
  },

  async changePassword(currentPassword, newPassword) {
    const response = await api.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
    return response;
  },

  async requestPasswordReset(email) {
    const response = await api.post('/auth/password-reset-request', { email });
    return response;
  },

  async resetPassword(token, newPassword) {
    const response = await api.post('/auth/password-reset', {
      token,
      new_password: newPassword,
    });
    return response;
  },
};