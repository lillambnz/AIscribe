/**
 * Cloudflare Worker - CORS Handler for AIscribe
 *
 * Handles CORS for API requests with proper security
 */

export interface Env {
  ALLOWED_ORIGINS: string;
}

const DEFAULT_ALLOWED_ORIGINS = [
  'https://aiscribe.com.au',
  'https://www.aiscribe.com.au',
  'http://localhost:3000', // Development
];

export default {
  async fetch(
    request: Request,
    env: Env,
    ctx: ExecutionContext
  ): Promise<Response> {
    const origin = request.headers.get('Origin');
    const allowedOrigins = env.ALLOWED_ORIGINS
      ? env.ALLOWED_ORIGINS.split(',')
      : DEFAULT_ALLOWED_ORIGINS;

    // Handle preflight requests
    if (request.method === 'OPTIONS') {
      if (origin && allowedOrigins.includes(origin)) {
        return new Response(null, {
          status: 204,
          headers: {
            'Access-Control-Allow-Origin': origin,
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Max-Age': '86400',
            'Access-Control-Allow-Credentials': 'true',
          },
        });
      }

      return new Response(null, { status: 403 });
    }

    // Forward request and add CORS headers to response
    const response = await fetch(request);

    if (origin && allowedOrigins.includes(origin)) {
      const newResponse = new Response(response.body, response);
      newResponse.headers.set('Access-Control-Allow-Origin', origin);
      newResponse.headers.set('Access-Control-Allow-Credentials', 'true');
      return newResponse;
    }

    return response;
  },
};
