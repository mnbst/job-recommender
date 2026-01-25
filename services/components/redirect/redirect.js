/**
 * Streamlit redirect component (v2 API).
 */

export default function RedirectComponent({
  data,
  setTriggerValue,
}) {
  const url = data?.url;
  if (!url) return;

  // Use parent window to ensure same-tab navigation from Streamlit container.
  window.parent.location.href = url;
  setTriggerValue("redirected", { url });
}
