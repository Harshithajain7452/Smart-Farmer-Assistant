/* Farmer chatbot front-end: async messaging with typing indicator. */
(function () {
  const win = document.getElementById('chatWindow');
  const form = document.getElementById('chatForm');
  const input = document.getElementById('chatInput');
  if (!form) return;

  function scroll() { win.scrollTop = win.scrollHeight; }

  function bubble(text, who) {
    const div = document.createElement('div');
    div.className = 'chat-bubble ' + (who === 'user' ? 'chat-user' : 'chat-bot');
    div.textContent = text;
    win.appendChild(div);
    scroll();
    return div;
  }

  function typing() {
    const div = document.createElement('div');
    div.className = 'chat-bubble chat-bot typing';
    div.innerHTML = '<span></span><span></span><span></span>';
    win.appendChild(div);
    scroll();
    return div;
  }

  function send(text) {
    if (!text.trim()) return;
    bubble(text, 'user');
    input.value = '';
    const dots = typing();
    fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text })
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        dots.remove();
        bubble(data.success ? data.reply : (data.error || 'Something went wrong.'), 'bot');
      })
      .catch(function () {
        dots.remove();
        bubble('Network error — please check your connection and try again.', 'bot');
      });
  }

  form.addEventListener('submit', function (e) { e.preventDefault(); send(input.value); });

  document.querySelectorAll('[data-quick-prompt]').forEach(function (btn) {
    btn.addEventListener('click', function () { send(btn.textContent.trim()); });
  });

  const clearBtn = document.getElementById('clearChat');
  if (clearBtn) {
    clearBtn.addEventListener('click', function () {
      if (!confirm('Clear your entire chat history?')) return;
      fetch('/api/chat/clear', { method: 'POST' }).then(function () { location.reload(); });
    });
  }
  scroll();
})();
