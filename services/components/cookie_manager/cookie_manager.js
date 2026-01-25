/**
 * Streamlit Cookie Manager Component (v2 API)
 *
 * Provides cookie get/set/delete operations via document.cookie
 */

/**
 * Parse document.cookie into an object
 * @returns {Object<string, string>}
 */
function parseCookies() {
  const cookies = {};
  if (!document.cookie) return cookies;

  document.cookie.split(";").forEach((cookie) => {
    const [name, ...valueParts] = cookie.trim().split("=");
    if (name) {
      cookies[name] = decodeURIComponent(valueParts.join("="));
    }
  });
  return cookies;
}

/**
 * Set a cookie
 * @param {string} name
 * @param {string} value
 * @param {Object} options
 */
function setCookie(name, value, options = {}) {
  let cookieString = `${encodeURIComponent(name)}=${encodeURIComponent(value)}`;

  if (options.expires) {
    const date = new Date(options.expires);
    cookieString += `; expires=${date.toUTCString()}`;
  }

  if (options.maxAge !== undefined) {
    cookieString += `; max-age=${options.maxAge}`;
  }

  cookieString += `; path=${options.path || "/"}`;

  if (options.domain) {
    cookieString += `; domain=${options.domain}`;
  }

  if (options.secure) {
    cookieString += "; secure";
  }

  if (options.sameSite) {
    cookieString += `; samesite=${options.sameSite}`;
  }

  document.cookie = cookieString;
}

/**
 * Delete a cookie
 * @param {string} name
 * @param {string} path
 */
function deleteCookie(name, path = "/") {
  document.cookie = `${encodeURIComponent(name)}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=${path}`;
}

/**
 * Main component function
 * @param {Object} args - Component arguments from Streamlit
 */
export default function CookieManagerComponent({
  setStateValue,
  setTriggerValue,
  data,
}) {
  const action = data?.action;
  const cookies = parseCookies();

  // Always send current cookies on mount
  setStateValue("cookies", cookies);

  if (!action) {
    return;
  }

  switch (action) {
    case "get": {
      const name = data.name;
      const value = cookies[name] || null;
      setStateValue("result", value);
      setTriggerValue("action_complete", { action: "get", name, value });
      break;
    }

    case "set": {
      const { name, value, expires, maxAge, path, domain, secure, sameSite } =
        data;
      setCookie(name, value, {
        expires,
        maxAge,
        path,
        domain,
        secure,
        sameSite,
      });
      // Update cookies state after set
      const updatedCookies = parseCookies();
      setStateValue("cookies", updatedCookies);
      setTriggerValue("action_complete", { action: "set", name, success: true });
      break;
    }

    case "delete": {
      const name = data.name;
      const path = data.path || "/";
      deleteCookie(name, path);
      // Update cookies state after delete
      const updatedCookies = parseCookies();
      setStateValue("cookies", updatedCookies);
      setTriggerValue("action_complete", {
        action: "delete",
        name,
        success: true,
      });
      break;
    }

    case "get_all": {
      setStateValue("result", cookies);
      setTriggerValue("action_complete", { action: "get_all", cookies });
      break;
    }
  }
}
