/**
 * Streamlit redirect component (v2 API).
 */

export default function RedirectComponent({
  data,
  setTriggerValue,
}) {
  const url = data?.url;
  const deleteCookie = data?.delete_cookie;
  if (!url) return;

  // Cookie削除が指定されている場合、リダイレクト前に削除
  if (deleteCookie) {
    // job_recommender_session Cookieを削除（全パス・ドメインで）
    document.cookie = 'job_recommender_session=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC; SameSite=Lax';
    // ドメインルートでも削除を試行
    const domain = window.location.hostname;
    document.cookie = `job_recommender_session=; path=/; domain=${domain}; expires=Thu, 01 Jan 1970 00:00:00 UTC; SameSite=Lax`;
  }

  // Use parent window to ensure same-tab navigation from Streamlit container.
  window.parent.location.href = url;
  setTriggerValue("redirected", { url, cookie_deleted: deleteCookie });
}
