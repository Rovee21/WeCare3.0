import createClient, { type Middleware } from 'openapi-fetch';
import type { paths } from '../generated/schema';
import { BASE_URL, getToken } from '../services/api';

const authMiddleware: Middleware = {
  async onRequest({ request }) {
    const token = await getToken();
    if (token) {
      request.headers.set('Authorization', `Token ${token}`);
    }
    return request;
  },
};

// The OpenAPI schema's path keys already include the `/api` prefix (e.g. `/api/sessions/`),
// so the client's base URL must be the bare origin, not BASE_URL (which already ends in `/api`).
const API_ROOT = BASE_URL.replace(/\/api\/?$/, '');

export const apiClient = createClient<paths>({ baseUrl: API_ROOT });
apiClient.use(authMiddleware);

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

type FetchResult<T> = {
  data?: T;
  error?: unknown;
  response: Response;
};

/** Unwraps an openapi-fetch result, throwing an ApiError on failure to match the old apiFetch contract. */
export function unwrap<T>({ data, error, response }: FetchResult<T>): T {
  if (error !== undefined) {
    const detail =
      error && typeof error === 'object' && 'detail' in (error as Record<string, unknown>)
        ? String((error as Record<string, unknown>).detail)
        : `HTTP ${response.status}`;
    throw new ApiError(detail, response.status);
  }
  if (response.status === 204) {
    return null as T;
  }
  return data as T;
}
