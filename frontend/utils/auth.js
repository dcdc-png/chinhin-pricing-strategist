/**
 * utils/auth.js
 * Azure Static Web Apps built-in authentication helpers.
 *
 * These work automatically when deployed to Azure SWA.
 * For local development, use the SWA CLI:
 *   npx @azure/static-web-apps-cli start http://localhost:3000 --run "npm run dev"
 *   Then open http://localhost:4280
 */

const IS_LOCAL =
  typeof window !== 'undefined' &&
  (window.location.hostname === 'localhost' ||
    window.location.hostname === '127.0.0.1') &&
  window.location.port !== '4280'; // port 4280 = SWA CLI running, auth IS available


/**
 * Fetch the currently authenticated user from /.auth/me
 * Returns a user object or null if not authenticated.
 *
 * @returns {Promise<{userId: string, userDetails: string, userRoles: string[], identityProvider: string} | null>}
 */
export async function getUser() {
  try {
    const res = await fetch('/.auth/me');
    if (!res.ok) return null;
    const data = await res.json();
    return data?.clientPrincipal ?? null;
  } catch {
    // Network error or endpoint not available locally
    return null;
  }
}

/**
 * Redirect the user to Microsoft login via Azure SWA's built-in AAD provider.
 * After login, the user is sent to /dashboard.
 */
export function signIn() {
  const redirectUri = encodeURIComponent('/dashboard');
  window.location.href = `/.auth/login/aad?post_login_redirect_uri=${redirectUri}`;
}

/**
 * Sign the user out and redirect back to the home (login) page.
 */
export function signOut() {
  const redirectUri = encodeURIComponent('/');
  window.location.href = `/.auth/logout?post_logout_redirect_uri=${redirectUri}`;
}

/**
 * Returns true if the current environment is local dev (not SWA).
 * Useful for showing helpful warnings in the UI during development.
 */
export function isLocalDev() {
  return IS_LOCAL;
}
