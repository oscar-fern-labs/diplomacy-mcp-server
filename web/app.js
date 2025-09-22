(() => {
  let ws = null;
  let gameCode = ;
  let playerName = ;

  const $ = (id) => document.getElementById(id);
  const wsStatus = $(ws-status);
  const currentCode = $(current-code);
  const boardEl = $(board);
  const messagesEl = $(messages);
  const phasesEl = $(phases);

  const backendBase = location.origin; // same origin

  function connectWS() {
    if (ws && ws.readyState === WebSocket.OPEN) return;
    ws = new WebSocket((location.protocol === https: ? wss:// : ws://) + location.host + /mcp);
    ws.onopen = () => {
      wsStatus.textContent = connected;
      send({ id: 1, method: initialize });
    };
    ws.onclose = () => { wsStatus.textContent = disconnected; };
    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        if (data.method === event) {
          // notification
          if (data.params?.type === chat_message) {
            appendMsg(`[chat] ${data.params.from}: ${data.params.message}`);
          }
          if (data.params?.type === phase_advanced) {
            appendMsg(`[phase] -> ${data.params.season} ${data.params.year} ${data.params.phase_type}`);
            refreshBoard();
            refreshPhases();
          }
        } else if (data.result) {
          // standard replies can be logged if needed
        }
      } catch {}
    };
  }

  function send(obj) {
    ws?.send(JSON.stringify({ jsonrpc: 2.0, ...obj }));
  }

  async function refreshBoard() {
    if (!gameCode) return;
    try {
      const r = await fetch(`${backendBase}/games/${gameCode}/board`);
      const j = await r.json();
      boardEl.textContent = JSON.stringify(j.game.current_phase || j.game, null, 2);
    } catch (e) { console.error(e); }
  }

  async function refreshMessages() {
    if (!gameCode) return;
    try {
      const r = await fetch(`${backendBase}/games/${gameCode}/messages`);
      const j = await r.json();
      messagesEl.innerHTML = ;
      j.messages.forEach(m => {
        const li = document.createElement(li);
        li.textContent = `${m.created_at} ${m.sender_name || anon}: ${m.content}`;
        messagesEl.appendChild(li);
      });
    } catch (e) { console.error(e); }
  }

  async function refreshPhases() {
    if (!gameCode) return;
    try {
      const r = await fetch(`${backendBase}/games/${gameCode}/phases`);
      const j = await r.json();
      phasesEl.innerHTML = ;
      j.phases.forEach(p => {
        const li = document.createElement(li);
        li.textContent = `#${p.index_in_game}: ${p.season} ${p.year} ${p.phase_type}`;
        phasesEl.appendChild(li);
      });
    } catch (e) { console.error(e); }
  }

  function appendMsg(line) {
    const li = document.createElement(li);
    li.textContent = line;
    messagesEl.appendChild(li);
  }

  $(btn-connect).onclick = () => connectWS();

  $(btn-create).onclick = () => {
    connectWS();
    send({ id: 2, method: game.create, params: { name: Web
