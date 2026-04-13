import { http, HttpResponse } from 'msw';

export const handlers = [
  // Health endpoint mock
  http.get('http://localhost:8000/health', () => {
    return HttpResponse.json({ status: 'ok' });
  }),

  // API health endpoint mock
  http.get('http://localhost:8000/api/v1/health', () => {
    return HttpResponse.json({
      status: 'ok',
      version: '0.1.0',
    });
  }),

  // LLM health endpoint mock
  http.get('http://localhost:8000/api/v1/health/llm', () => {
    return HttpResponse.json({
      status: 'healthy',
      tutor_model: 'ollama/qwen2.5:72b',
      assessment_model: 'ollama/qwen2.5:32b',
      ollama_status: 'disconnected',
    });
  }),

  // Ready probe mock
  http.get('http://localhost:8000/api/v1/health/ready', () => {
    return HttpResponse.json({ status: 'ready' });
  }),

  // Live probe mock
  http.get('http://localhost:8000/api/v1/health/live', () => {
    return HttpResponse.json({ status: 'alive' });
  }),
];
