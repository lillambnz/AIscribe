/**
 * Cloudflare Worker - Rate Limiting for AIscribe API
 *
 * Protects authentication and sensitive endpoints from abuse
 */

export interface Env {
  RATE_LIMIT: KVNamespace;
  JWT_SECRET: string;
}

interface RateLimitConfig {
  maxRequests: number;
  windowSeconds: number;
}

const RATE_LIMITS: Record<string, RateLimitConfig> = {
  '/v1/auth/login': { maxRequests: 5, windowSeconds: 60 },
  '/v1/auth/register': { maxRequests: 3, windowSeconds: 300 },
  '/v1/encounters': { maxRequests: 100, windowSeconds: 60 },
  '/v1/billing/subscribe': { maxRequests: 10, windowSeconds: 3600 },
};

export default {
  async fetch(
    request: Request,
    env: Env,
    ctx: ExecutionContext
  ): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;
    const clientIP = request.headers.get('CF-Connecting-IP') || 'unknown';

    // Check if this path has rate limiting
    const rateLimit = Object.entries(RATE_LIMITS).find(([pattern, _]) =>
      path.startsWith(pattern)
    );

    if (rateLimit) {
      const [, config] = rateLimit;
      const key = `ratelimit:${path}:${clientIP}`;

      // Get current count from KV
      const currentCount = parseInt((await env.RATE_LIMIT.get(key)) || '0');

      if (currentCount >= config.maxRequests) {
        return new Response(
          JSON.stringify({
            error: 'Rate limit exceeded',
            message: `Too many requests. Please try again in ${config.windowSeconds} seconds.`,
          }),
          {
            status: 429,
            headers: {
              'Content-Type': 'application/json',
              'Retry-After': config.windowSeconds.toString(),
            },
          }
        );
      }

      // Increment counter
      await env.RATE_LIMIT.put(
        key,
        (currentCount + 1).toString(),
        { expirationTtl: config.windowSeconds }
      );
    }

    // Forward request to origin
    return fetch(request);
  },
};
