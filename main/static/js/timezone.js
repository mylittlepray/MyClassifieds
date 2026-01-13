(function () {
  function getCookie(name) {
    const m = document.cookie.match(new RegExp('(^|;\\s*)' + name + '=([^;]*)'));
    return m ? decodeURIComponent(m[2]) : null;
  }

  const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
  if (!tz) return;

  const key = "tz_sent";
  if (localStorage.getItem(key) === tz) return;

  fetch(window.SET_TZ_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: "timezone=" + encodeURIComponent(tz),
    credentials: "include",
  })
    .then((r) => {
      if (!r.ok) return;
      localStorage.setItem(key, tz);
      location.reload();
    })
    .catch(() => {});
})();
