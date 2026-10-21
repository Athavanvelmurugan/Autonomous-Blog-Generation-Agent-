import axios from 'axios';

const API_BASE = '/api';

const client = axios.create({
  timeout: 120000, // 2-minute timeout for multi-agent LLM DAG pipeline
  headers: {
    'Content-Type': 'application/json',
  },
});

export const checkHealth = async () => {
  const response = await client.get('/health');
  return response.data;
};

export const fetchSupportedLanguages = async () => {
  const response = await client.get(`${API_BASE}/languages`);
  return response.data;
};

export const generateBlog = async ({ topic, tone, target_language }) => {
  const response = await client.post(`${API_BASE}/generate-blog`, {
    topic,
    tone,
    target_language,
  });
  return response.data;
};

export const generateBlogStream = async ({ topic, tone, target_language }, onEvent, onError) => {
  try {
    const response = await fetch(`${API_BASE}/generate-blog/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ topic, tone, target_language }),
    });

    if (!response.ok) {
      throw new Error(`Server returned HTTP ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split('\n\n');
      buffer = parts.pop();

      for (const part of parts) {
        const trimmed = part.trim();
        if (trimmed.startsWith('data: ')) {
          try {
            const data = JSON.parse(trimmed.slice(6));
            onEvent(data);
          } catch (e) {
            console.warn('Failed to parse SSE JSON:', e);
          }
        }
      }
    }
  } catch (err) {
    if (onError) {
      onError(err);
    } else {
      throw err;
    }
  }
};

export const fetchBlogHistory = async () => {
  const response = await client.get(`${API_BASE}/blogs`);
  return response.data;
};

export const fetchBlogById = async (id) => {
  const response = await client.get(`${API_BASE}/blogs/${id}`);
  return response.data;
};

export const deleteBlogById = async (id) => {
  await client.delete(`${API_BASE}/blogs/${id}`);
};

export const updateBlogById = async (id, { title, content }) => {
  const response = await client.put(`${API_BASE}/blogs/${id}`, { title, content });
  return response.data;
};

