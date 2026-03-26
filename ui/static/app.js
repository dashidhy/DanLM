// === GuanDan Game UI ===

let gameState = null;
let gameId = null;
let selectedCards = new Set(); // Set of indices in hand array
let pollTimer = null;
let hintEnabled = false;
let autoPlayEnabled = false;

// Drag-and-drop hand reordering
let localHand = null; // local copy of hand array for reordering
let lastServerHandKey = null; // fingerprint to detect server hand changes (order-independent)
let dragSrcIdx = null; // index of card being dragged
let sortAscending = localStorage.getItem('sortAscending') === 'true'; // persisted preference
let tributeConfirmed = false; // true after user acknowledges tribute info
let selectedTributeIdx = null; // index in localHand selected during tribute phase

// === i18n ===

const I18N = {
    en: {
        // Start screen
        title: 'GuanDan AI',
        subtitle: 'DanZero v3 - AI Poker Platform',
        singleRound: 'Random Single Round',
        fullGame: 'Full Game (2 to A)',
        // Player labels
        you: 'You', next: 'Next', partner: 'Partner', prev: 'Prev',
        // Status bar
        level: 'Level', round: 'Round', us: 'Us', them: 'Them',
        tributeNone: 'Tribute: None', tributeYes: 'Tribute: Yes',
        tributeAnti: 'Tribute: Anti', tributeInteractive: 'Tribute: Interactive',
        tributePhase: 'Tribute Phase',
        yourTurn: 'Your turn',
        thinking: 'thinking...',
        roundOver: 'Round over', gameOver: 'Game over!',
        // Buttons
        reset: 'Reset', menu: 'Menu',
        play: 'Play', clear: 'Clear', pass: 'Pass',
        hintOn: 'AI Hint: ON', hintOff: 'AI Hint: OFF',
        autoOn: 'AI Auto: ON', autoOff: 'AI Auto: OFF',
        confirm: 'Confirm', continue_: 'Continue',
        newRound: 'New Round', nextRound: 'Next Round', newGame: 'New Game',
        // Center messages
        yourTurnBig: 'Your Turn',
        isThinking: 'is thinking...',
        leadPrefix: 'Lead',
        // Overlays
        noTribute: 'No Tribute',
        firstPlayer: 'First player',
        antiTribute: 'Anti-Tribute!',
        holds2BigJoker: 'holds 2× Big Joker',
        eachHoldBigJoker: 'each hold Big Joker',
        singleTribute: 'Single Tribute',
        doubleTribute: 'Double Tribute',
        givesTo: 'gives to',
        tributeComplete: 'Tribute Complete',
        tributeGive: 'Tribute',
        tributeBack: 'Return',
        gaveTo: 'gave',
        toPlayer: 'to',
        returned: 'returned',
        // Result
        victory: 'Victory!', defeat: 'Defeat',
        finishOrder: 'Finish order',
        reward: 'Reward',
        teamLevels: 'Team levels',
        gameWon: 'Game Won!', gameLost: 'Game Lost',
        // Tribute action
        chooseGiveTo: 'Choose a card to give to',
        chooseHighest: 'Choose your highest card to give as tribute',
        chooseReturnTo: 'Choose a card to return to',
        // Card
        joker: 'Joker',
        // Play types
        pt_pass: 'pass',
        pt_single: 'single', pt_double: 'double', pt_triple: 'triple',
        pt_plate: 'plate', pt_tube: 'tube', pt_straight: 'straight',
        pt_fullhouse: 'fullhouse', pt_normalbomb: 'bomb',
        pt_flushbomb: 'straight flush', pt_jokerbomb: 'joker bomb',
        // Misc
        notValidPlay: 'Not a valid play!',
        disambiguate: 'Multiple interpretations — choose one:',
        cancel: 'Cancel',
        sortAsc: 'Sort: →', sortDesc: 'Sort: ←',
        aiAgent: 'AI Agent',
        lang: '中文',
    },
    zh: {
        title: '掼蛋 AI',
        subtitle: 'DanZero v3 - AI 掼蛋平台',
        singleRound: '随机单局',
        fullGame: '完整对局 (2 到 A)',
        you: '自己', next: '下家', partner: '队友', prev: '上家',
        level: '等级', us: '我方', them: '对方',
        tributeNone: '进贡：无', tributeYes: '进贡：有',
        tributeAnti: '进贡：抗贡', tributeInteractive: '进贡：进行中',
        tributePhase: '进贡阶段',
        yourTurn: '你的回合',
        thinking: '思考中...',
        roundOver: '本局结束', gameOver: '游戏结束！',
        reset: '重置', menu: '菜单',
        play: '出牌', clear: '取消', pass: '过',
        hintOn: 'AI提示：开', hintOff: 'AI提示：关',
        autoOn: 'AI托管：开', autoOff: 'AI托管：关',
        confirm: '确认', continue_: '继续',
        newRound: '再来一局', nextRound: '下一局', newGame: '新游戏',
        yourTurnBig: '你的回合',
        isThinking: '思考中...',
        leadPrefix: '领出',
        noTribute: '无进贡',
        firstPlayer: '先手',
        antiTribute: '抗贡！',
        holds2BigJoker: '持有 2 张大王',
        eachHoldBigJoker: '各持有大王',
        singleTribute: '单进贡',
        doubleTribute: '双进贡',
        givesTo: '进贡给',
        tributeComplete: '进贡完成',
        tributeGive: '进贡',
        tributeBack: '还贡',
        gaveTo: '进贡了',
        toPlayer: '给',
        returned: '还贡了',
        victory: '胜利！', defeat: '失败',
        finishOrder: '完成顺序',
        reward: '奖励',
        teamLevels: '队伍等级',
        gameWon: '赢得比赛！', gameLost: '比赛失败',
        chooseGiveTo: '选择一张牌进贡给',
        chooseHighest: '选择你最大的一张牌进贡',
        chooseReturnTo: '选择一张牌还贡给',
        joker: 'Joker',
        pt_pass: '过',
        pt_single: '单张', pt_double: '对子', pt_triple: '三不带',
        pt_plate: '钢板', pt_tube: '三连对', pt_straight: '顺子',
        pt_fullhouse: '三带二', pt_normalbomb: '炸弹',
        pt_flushbomb: '同花顺', pt_jokerbomb: '王炸',
        notValidPlay: '不是合法的出牌！',
        disambiguate: '出牌有多种解释，请选择：',
        cancel: '取消',
        sortAsc: '排序：→', sortDesc: '排序：←',
        aiAgent: 'AI 模型',
        lang: 'EN',
    }
};

let currentLang = localStorage.getItem('lang') || 'en';

function t(key) {
    return (I18N[currentLang] && I18N[currentLang][key]) || I18N.en[key] || key;
}

function tPlayType(type) {
    return t('pt_' + type) || type;
}

function toggleLang() {
    currentLang = currentLang === 'en' ? 'zh' : 'en';
    localStorage.setItem('lang', currentLang);
    applyLang();
}

function applyLang() {
    // Update static HTML elements
    document.getElementById('start-title').textContent = t('title');
    document.getElementById('start-subtitle').textContent = t('subtitle');
    document.getElementById('btn-single-round').textContent = t('singleRound');
    document.getElementById('btn-full-game').textContent = t('fullGame');
    document.getElementById('btn-reset').textContent = t('reset');
    document.getElementById('btn-menu').textContent = t('menu');
    document.getElementById('btn-lang').textContent = t('lang');
    document.getElementById('btn-lang-start').textContent = t('lang');
    document.getElementById('label-agent').textContent = t('aiAgent');
    document.getElementById('btn-info-continue').textContent = t('continue_');
    document.getElementById('btn-back-menu').textContent = t('menu');
    // Player labels in HTML
    document.querySelector('#player-top .player-label').textContent = t('partner');
    document.querySelector('#player-left .player-label').textContent = t('prev');
    document.querySelector('#player-right .player-label').textContent = t('next');
    // Dynamic elements re-render
    if (gameState) render();
}

// === Sound Effects (Web Audio API) ===

const AudioCtx = window.AudioContext || window.webkitAudioContext;
let audioCtx = null;

function getAudioCtx() {
    if (!audioCtx) audioCtx = new AudioCtx();
    return audioCtx;
}

function playTone(freq, duration, type = 'triangle', gain = 0.3) {
    const ctx = getAudioCtx();
    const osc = ctx.createOscillator();
    const g = ctx.createGain();
    osc.type = type;
    osc.frequency.value = freq;
    g.gain.setValueAtTime(gain, ctx.currentTime);
    g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
    osc.connect(g);
    g.connect(ctx.destination);
    osc.start(ctx.currentTime);
    osc.stop(ctx.currentTime + duration);
}

function playNoise(duration, gain = 0.15) {
    const ctx = getAudioCtx();
    const bufSize = ctx.sampleRate * duration;
    const buf = ctx.createBuffer(1, bufSize, ctx.sampleRate);
    const data = buf.getChannelData(0);
    for (let i = 0; i < bufSize; i++) data[i] = Math.random() * 2 - 1;
    const src = ctx.createBufferSource();
    src.buffer = buf;
    const g = ctx.createGain();
    g.gain.setValueAtTime(gain, ctx.currentTime);
    g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
    src.connect(g);
    g.connect(ctx.destination);
    src.start();
}

function sfxPlay() {
    // Card slap: short noise burst + tap tone
    playNoise(0.08, 0.12);
    playTone(800, 0.06, 'square', 0.08);
}

function sfxPass() {
    playTone(300, 0.12, 'sine', 0.08);
}

function sfxBomb() {
    // Punchy impact: sharp attack + quick pitch drop + noise hit
    const ctx = getAudioCtx();
    // Impact hit — sharp sine drop
    const osc1 = ctx.createOscillator();
    const g1 = ctx.createGain();
    osc1.type = 'sine';
    osc1.frequency.setValueAtTime(400, ctx.currentTime);
    osc1.frequency.exponentialRampToValueAtTime(60, ctx.currentTime + 0.15);
    g1.gain.setValueAtTime(0.5, ctx.currentTime);
    g1.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.25);
    osc1.connect(g1);
    g1.connect(ctx.destination);
    osc1.start(ctx.currentTime);
    osc1.stop(ctx.currentTime + 0.25);
    // Sub thump
    const osc2 = ctx.createOscillator();
    const g2 = ctx.createGain();
    osc2.type = 'sine';
    osc2.frequency.value = 55;
    g2.gain.setValueAtTime(0.4, ctx.currentTime);
    g2.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3);
    osc2.connect(g2);
    g2.connect(ctx.destination);
    osc2.start(ctx.currentTime);
    osc2.stop(ctx.currentTime + 0.3);
    // Short noise crack
    playNoise(0.06, 0.25);
}

function sfxFlushBomb() {
    // Ascending chime
    const notes = [523, 659, 784, 988, 1175]; // C5 E5 G5 B5 D6
    notes.forEach((f, i) => {
        setTimeout(() => playTone(f, 0.25, 'sine', 0.25), i * 60);
    });
}

function sfxJokerBomb() {
    // Epic explosion: low rumble + high sparkle + noise
    const ctx = getAudioCtx();
    // Low rumble
    const osc1 = ctx.createOscillator();
    const g1 = ctx.createGain();
    osc1.type = 'sawtooth';
    osc1.frequency.setValueAtTime(100, ctx.currentTime);
    osc1.frequency.exponentialRampToValueAtTime(25, ctx.currentTime + 0.8);
    g1.gain.setValueAtTime(0.5, ctx.currentTime);
    g1.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.8);
    osc1.connect(g1);
    g1.connect(ctx.destination);
    osc1.start(ctx.currentTime);
    osc1.stop(ctx.currentTime + 0.8);
    // High sparkle cascade
    [1047, 1319, 1568, 1976, 2349].forEach((f, i) => {
        setTimeout(() => playTone(f, 0.4, 'sine', 0.2), i * 80);
    });
    playNoise(0.5, 0.25);
}

function sfxForPlayType(type) {
    switch (type) {
        case 'pass': sfxPass(); break;
        case 'jokerbomb': sfxJokerBomb(); break;
        case 'flushbomb': sfxFlushBomb(); break;
        case 'normalbomb': sfxBomb(); break;
        default: sfxPlay(); break;
    }
}

function checkNewPlays(newState) {
    const newTricks = newState.trick_plays || [];
    const oldLen = (gameState && gameState.trick_plays) ? gameState.trick_plays.length : 0;
    // Sound triggers when: new plays added (length grew), or trick reset with new play
    if (newTricks.length > 0 && newTricks.length !== oldLen) {
        const latest = newTricks[newTricks.length - 1];
        sfxForPlayType(latest.type);
    }
}

// === API helpers ===

async function api(endpoint, method = 'GET', body = null) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body) opts.body = JSON.stringify(body);
    const url = method === 'GET' && body === null ? endpoint : endpoint;
    const resp = await fetch(url, opts);
    if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: 'Unknown error' }));
        console.error('API error:', err);
        return null;
    }
    return resp.json();
}

// === Agent selection ===

async function loadAgents() {
    const agents = await api('/api/agents', 'GET');
    if (!agents) return;
    const select = document.getElementById('agent-select');
    select.innerHTML = '';
    for (const a of agents) {
        const opt = document.createElement('option');
        opt.value = a.key;
        opt.textContent = a.name;
        if (a.key === 'danzero_v1t') opt.selected = true;
        select.appendChild(opt);
    }
}

// Load agents on page init
loadAgents();

// Heartbeat: ping server every 30s so it knows the browser is still open.
// Server auto-exits if no heartbeat received within IDLE_TIMEOUT.
setInterval(() => {
    fetch('/api/heartbeat').catch(() => {});
}, 30000);

// === Game lifecycle ===

async function startGame(mode) {
    const agent = document.getElementById('agent-select').value;
    const state = await api('/api/new-game', 'POST', { mode, agent });
    if (!state) return;
    gameId = state.game_id;
    gameState = state;
    selectedCards.clear();
    tributeConfirmed = false;
    hintEnabled = false;
    autoPlayEnabled = false;

    document.getElementById('start-screen').classList.remove('active');
    document.getElementById('game-screen').classList.add('active');

    render();
    showRoundStartOverlay();
}

function backToMenu() {
    stopPolling();
    gameState = null;
    gameId = null;
    localHand = null;
    lastServerHandKey = null;
    tributeConfirmed = false;
    selectedTributeIdx = null;

    document.getElementById('game-screen').classList.remove('active');
    document.getElementById('start-screen').classList.add('active');
    document.getElementById('result-overlay').classList.add('hidden');
    document.getElementById('info-overlay').classList.add('hidden');
}

async function resetGame() {
    if (!gameState) return;
    stopPolling();
    document.getElementById('result-overlay').classList.add('hidden');
    document.getElementById('info-overlay').classList.add('hidden');
    selectedCards.clear();
    localHand = null;
    lastServerHandKey = null;
    tributeConfirmed = false;
    selectedTributeIdx = null;


    const mode = gameState.mode;
    const state = await api('/api/new-game', 'POST', { mode });
    if (!state) return;
    gameId = state.game_id;
    gameState = state;

    render();
    showRoundStartOverlay();
}

async function newRound() {
    document.getElementById('result-overlay').classList.add('hidden');
    document.getElementById('info-overlay').classList.add('hidden');
    selectedCards.clear();
    localHand = null;
    lastServerHandKey = null;
    tributeConfirmed = false;
    selectedTributeIdx = null;


    let state;
    if (gameState && gameState.mode === 'full_game') {
        state = await api('/api/next-round', 'POST', { game_id: gameId });
    } else {
        state = await api('/api/new-round', 'POST', { game_id: gameId });
    }
    if (!state) return;
    gameState = state;
    render();
    showRoundStartOverlay();
}

// === Round Info Overlays ===

function _miniJokerHTML() {
    return `<div class="card mini suit-joker joker-big" style="display:inline-flex;cursor:default"><div class="card-rank" style="color:#d32f2f">${t('joker')}</div><div class="card-suit" style="color:#d32f2f">🃏</div></div>`;
}

function _miniCardHTML(cardInfo) {
    if (!cardInfo) return '?';
    const tmp = document.createElement('div');
    tmp.appendChild(createCardElement(cardInfo, true));
    const el = tmp.firstChild;
    el.style.display = 'inline-flex';
    el.style.cursor = 'default';
    el.style.verticalAlign = 'middle';
    return el.outerHTML;
}

function _tributeRecordHTML(giverLabel, verb, cardInfo, receiverLabel) {
    return `<div style="display:flex;align-items:center;justify-content:center;gap:8px;margin:6px 0">
        <span>${giverLabel}</span>
        <span style="opacity:0.7">${verb}</span>
        ${_miniCardHTML(cardInfo)}
        <span style="opacity:0.7">${t('toPlayer')}</span>
        <span>${receiverLabel}</span>
    </div>`;
}

function _showOverlay(title, html, onContinue) {
    document.getElementById('info-title').textContent = title;
    document.getElementById('info-title').className = '';
    document.getElementById('info-details').innerHTML = html;
    const btn = document.getElementById('btn-info-continue');
    btn.onclick = () => {
        document.getElementById('info-overlay').classList.add('hidden');
        onContinue();
    };
    document.getElementById('info-overlay').classList.remove('hidden');
}

function _antiTributeHTML(holders) {
    let html = `<p style="color:#e8b930">${t('antiTribute')}</p>`;
    if (holders.length === 1) {
        html += `<p>${playerLabel(holders[0])} ${t('holds2BigJoker')}</p>`;
        html += '<div style="display:flex;justify-content:center;gap:4px;margin:8px 0">';
        for (let i = 0; i < 2; i++) html += _miniJokerHTML();
        html += '</div>';
    } else if (holders.length === 2) {
        html += `<p>${playerLabel(holders[0])}, ${playerLabel(holders[1])} ${t('eachHoldBigJoker')}</p>`;
        html += '<div style="display:flex;justify-content:center;gap:16px;margin:8px 0">';
        for (const h of holders) {
            html += `<div style="text-align:center"><div style="font-size:0.75rem;opacity:0.7;margin-bottom:2px">${playerLabel(h)}</div>${_miniJokerHTML()}</div>`;
        }
        html += '</div>';
    }
    return html;
}

function showRoundStartOverlay() {
    const info = gameState.round_start_info;
    if (!info) { beginPlay(); return; }

    const title = `${t('level')} ${levelName(info.level)}`;
    let html = '';

    if (info.tribute_type === 'none') {
        html += `<p>${t('noTribute')}</p>`;
        html += `<p>${t('firstPlayer')}: ${playerLabel(info.first_player)}</p>`;
        _showOverlay(title, html, beginPlay);
        return;
    }

    if (info.tribute_type === 'anti') {
        html += _antiTributeHTML(info.anti_holders || []);
        html += `<p>${t('firstPlayer')}: ${playerLabel(info.first_player)}</p>`;
        _showOverlay(title, html, beginPlay);
        return;
    }

    // Single/double tribute
    if (info.tribute_type === 'single') {
        html += `<p style="color:#e8b930">${t('singleTribute')}</p>`;
        html += `<p>${playerLabel(info.givers[0])} ${t('givesTo')} ${playerLabel(info.receivers[0])}</p>`;
    } else if (info.tribute_type === 'double') {
        html += `<p style="color:#e8b930">${t('doubleTribute')}</p>`;
        html += `<p>${playerLabel(info.givers[0])}, ${playerLabel(info.givers[1])} ${t('givesTo')} ${playerLabel(info.receivers[0])}, ${playerLabel(info.receivers[1])}</p>`;
    }

    // tribute_give_done: server paused after give, show give records then continue to back
    if (gameState.phase === 'tribute_give_done' && gameState.tribute_records && gameState.tribute_records.length > 0) {
        _showOverlay(title, html, () => showTributeGiveOverlay());
    } else if (gameState.phase === 'playing' && gameState.tribute_records && gameState.tribute_records.length > 0) {
        // All tribute already done (e.g. interactive tribute completion)
        _showOverlay(title, html, () => showTributeGiveOverlay());
    } else {
        // Interactive tribute phase — user picks cards
        _showOverlay(title, html, () => {
            tributeConfirmed = false;
            render();
        });
    }
}

function showTributeGiveOverlay() {
    const records = gameState.tribute_records;

    // Show all give records
    let html = '';
    for (const r of records) {
        if (r.action === 'give') {
            html += _tributeRecordHTML(playerLabel(r.giver), t('gaveTo'), r.card_info, playerLabel(r.receiver));
        }
    }

    if (gameState.phase === 'tribute_give_done') {
        // Server paused after give — call continue-tribute to execute back phase
        _showOverlay(t('tributeGive'), html, async () => {
            const state = await api('/api/continue-tribute', 'POST', { game_id: gameId });
            if (state) {
                gameState = state;
                render();
            }
            // Only show back overlay if back phase is complete.
            // If human still needs to back (phase=tribute_back), let render()
            // show the tribute UI — back overlay will be shown later via
            // tributeSubmitCard → showPostTributeOverlay.
            if (gameState.phase !== 'tribute_back' && gameState.phase !== 'tribute_give') {
                showTributeBackOverlay();
            }
        });
    } else {
        // All tribute already done (playing phase) — just step through overlays
        _showOverlay(t('tributeGive'), html, () => showTributeBackOverlay());
    }
}

function showTributeBackOverlay() {
    const records = gameState.tribute_records;
    const info = gameState.round_start_info;

    // Show all back records
    let html = '';
    for (const r of records) {
        if (r.action === 'back') {
            html += _tributeRecordHTML(playerLabel(r.giver), t('returned'), r.card_info, playerLabel(r.receiver));
        }
    }

    const firstPlayer = info ? info.first_player : gameState.current_player;
    if (firstPlayer !== undefined && firstPlayer !== null) {
        html += `<p style="margin-top:0.5rem">${t('firstPlayer')}: ${playerLabel(firstPlayer)}</p>`;
    }

    _showOverlay(t('tributeBack'), html, beginPlay);
}

function showPostTributeOverlay() {
    const records = gameState.tribute_records;
    const info = gameState.round_start_info;
    if (!records || records.length === 0) { beginPlay(); return; }

    const isAnti = records[0].giver === records[0].receiver;
    if (isAnti) {
        let html = _antiTributeHTML(info && info.anti_holders || []);
        const firstPlayer = info ? info.first_player : gameState.current_player;
        if (firstPlayer !== undefined && firstPlayer !== null) {
            html += `<p style="margin-top:0.5rem">${t('firstPlayer')}: ${playerLabel(firstPlayer)}</p>`;
        }
        _showOverlay(t('tributeComplete'), html, beginPlay);
    } else {
        // Show back records then begin play (give records were already shown via tribute_give_done)
        showTributeBackOverlay();
    }
}

function beginPlay() {
    tributeConfirmed = true;
    // Notify server and start polling
    api('/api/confirm-tribute', 'POST', { game_id: gameId }).then(state => {
        if (state) {
            gameState = state;
            render();
        }
        startPolling();
    });
}

// === Polling for AI turns ===

function startPolling() {
    stopPolling();
    pollTimer = setInterval(pollState, 1000);
}

function stopPolling() {
    if (pollTimer) {
        clearInterval(pollTimer);
        pollTimer = null;
    }
}

async function pollState() {
    if (!gameId) return;
    const state = await api(`/api/state?game_id=${gameId}`);
    if (!state) {
        // Session lost (e.g. server restarted) — stop polling, go back to menu
        stopPolling();
        backToMenu();
        return;
    }

    const changed = JSON.stringify(state) !== JSON.stringify(gameState);
    if (changed) {
        checkNewPlays(state);
        gameState = state;
        render();
    }
}

// === Actions ===

async function playSelected() {
    if (!gameState || !gameState.is_human_turn) return;

    // Build sorted list of selected card_ints
    const hand = localHand || gameState.hand;
    const selCardInts = [];
    selectedCards.forEach(idx => {
        if (idx < hand.length) selCardInts.push(hand[idx].card_int);
    });
    selCardInts.sort((a, b) => a - b);

    // Find ALL matching legal plays (same card_ints, possibly different type/rank)
    const matches = [];
    for (const play of gameState.legal_plays) {
        const playInts = [...play.card_ints].sort((a, b) => a - b);
        if (playInts.length === selCardInts.length &&
            playInts.every((v, i) => v === selCardInts[i])) {
            matches.push(play);
        }
    }

    if (matches.length === 0) {
        showMessage(t('notValidPlay'));
        return;
    }

    if (matches.length === 1) {
        await executePlay(matches[0].index);
        return;
    }

    // Ambiguous — show disambiguation picker
    showDisambiguationPicker(matches);
}

function showDisambiguationPicker(matches) {
    const overlay = document.getElementById('disambig-overlay');
    const container = document.getElementById('disambig-options');
    document.getElementById('disambig-title').textContent = t('disambiguate');
    container.innerHTML = '';

    for (const play of matches) {
        const option = document.createElement('div');
        option.className = 'disambig-option';
        option.onclick = async () => {
            overlay.classList.add('hidden');
            await executePlay(play.index);
        };

        // Cards row
        const cardsRow = document.createElement('div');
        cardsRow.className = 'disambig-cards';
        for (const card of play.cards) {
            cardsRow.appendChild(createCardElement(card, true));
        }
        option.appendChild(cardsRow);

        // Label: play type + rank
        const label = document.createElement('div');
        label.className = 'disambig-label';
        const typeStr = t('pt_' + play.type) || play.type;
        label.textContent = play.rank ? `${typeStr} ${play.rank}` : typeStr;
        option.appendChild(label);

        container.appendChild(option);
    }

    overlay.classList.remove('hidden');

    // Cancel button
    const cancelBtn = document.getElementById('btn-disambig-cancel');
    cancelBtn.textContent = t('cancel');
    cancelBtn.onclick = () => {
        overlay.classList.add('hidden');
    };
}

async function executePlay(actionIndex) {
    const state = await api('/api/play', 'POST', { game_id: gameId, action_index: actionIndex });
    if (!state) return;
    checkNewPlays(state);
    gameState = state;
    selectedCards.clear();
    render();
}

async function playPass() {
    if (!gameState || !gameState.is_human_turn) return;
    const state = await api('/api/pass', 'POST', { game_id: gameId });
    if (!state) return;
    checkNewPlays(state);
    gameState = state;
    selectedCards.clear();
    render();
}

async function toggleHint() {
    hintEnabled = !hintEnabled;
    const state = await api('/api/hint', 'POST', { game_id: gameId, enabled: hintEnabled });
    if (state) {
        gameState = state;
        render();
    }
}

async function toggleAutoPlay() {
    autoPlayEnabled = !autoPlayEnabled;
    const state = await api('/api/auto-play', 'POST', { game_id: gameId, enabled: autoPlayEnabled });
    if (state) {
        gameState = state;
        render();
    }
}

function toggleSortOrder() {
    sortAscending = !sortAscending;
    localStorage.setItem('sortAscending', sortAscending);
    // Re-sort from server hand (which is always sorted descending)
    const serverHand = gameState.hand || [];
    if (sortAscending) {
        localHand = serverHand.slice().reverse();
    } else {
        localHand = serverHand.slice();
    }
    selectedCards.clear();
    // Re-render appropriate hand view
    if (gameState && (gameState.phase === 'tribute_give' || gameState.phase === 'tribute_back')) {
        renderTributeHand();
        renderTributeActionBar();
    } else {
        renderHand();
        renderActionBar();
    }
}

function selectHintPlay(cardInts) {
    // Auto-select cards matching a hint
    selectedCards.clear();
    const hand = localHand || gameState.hand;
    const needed = [...cardInts];

    for (let i = 0; i < hand.length; i++) {
        const idx = needed.indexOf(hand[i].card_int);
        if (idx >= 0) {
            selectedCards.add(i);
            needed.splice(idx, 1);
        }
    }
    renderHand();
    renderActionBar();
}

function clearSelection() {
    selectedCards.clear();
    renderHand();
    renderActionBar();
}

// === Rendering ===

function render() {
    if (!gameState) return;

    renderStatusBar();
    renderOpponents();
    renderTrick();
    renderHints();
    renderResult();
    renderTributeCards();

    // Tribute phase: special rendering
    if (gameState.phase === 'tribute_give' || gameState.phase === 'tribute_back') {
        renderTributeHand();
        renderTributeActionBar();
    } else {
        renderHand();
        renderActionBar();
    }
}

function renderStatusBar() {
    const s = gameState;
    document.getElementById('status-level').textContent = `${t('level')}: ${levelName(s.round_level)}`;
    document.getElementById('status-round').textContent = currentLang === 'zh'
        ? `第 ${s.round_number} 局`
        : `${t('round')}: ${s.round_number}`;
    document.getElementById('status-teams').textContent =
        `${t('us')}: ${levelName(s.team_levels[0])} vs ${t('them')}: ${levelName(s.team_levels[1])}`;

    // Show tribute status
    const tributeEl = document.getElementById('status-tribute');
    if (tributeEl) {
        const records = s.tribute_records;
        if (s.phase === 'tribute_give' || s.phase === 'tribute_back' || s.phase === 'tribute_give_done') {
            tributeEl.textContent = t('tributeInteractive');
            tributeEl.style.color = '#e8b930';
        } else if (records && records.length > 0) {
            const isAnti = records[0].giver === records[0].receiver;
            tributeEl.textContent = isAnti ? t('tributeAnti') : t('tributeYes');
            tributeEl.style.color = '#e8b930';
        } else {
            tributeEl.textContent = t('tributeNone');
            tributeEl.style.color = '';
        }
    }

    let turnText = '';
    if (s.phase === 'tribute_give' || s.phase === 'tribute_back' || s.phase === 'tribute_give_done') {
        turnText = t('tributePhase');
    } else if (s.phase === 'playing') {
        if (s.is_human_turn) turnText = t('yourTurn');
        else turnText = `${playerLabel(s.current_player)} ${t('thinking')}`;
    } else if (s.phase === 'round_over') {
        turnText = t('roundOver');
    } else if (s.phase === 'game_over') {
        turnText = t('gameOver');
    }
    document.getElementById('status-turn').textContent = turnText;
}

function playerLabel(seat) {
    const keys = { 0: 'you', 1: 'next', 2: 'partner', 3: 'prev' };
    return keys[seat] ? t(keys[seat]) : `P${seat}`;
}

function levelName(lvl) {
    const names = { 11: 'J', 12: 'Q', 13: 'K', 14: 'A' };
    return names[lvl] || String(lvl);
}

function renderOpponents() {
    const opponents = gameState.opponents;
    const seatMap = { 1: 'right', 2: 'top', 3: 'left' };

    for (const opp of opponents) {
        const el = document.getElementById(`player-${seatMap[opp.seat]}`);
        if (!el) continue;

        // Active turn indicator
        el.classList.toggle('active-turn', gameState.current_player === opp.seat);

        // Card count
        const countEl = el.querySelector('.player-card-count');
        countEl.textContent = opp.finished ? '' : `${opp.card_count}`;
        countEl.classList.toggle('warn', opp.warn_low);

        // Card backs (actual count, overlapping handles space)
        const backsEl = el.querySelector('.player-cards-back');
        const numBacks = opp.finished ? 0 : opp.card_count;
        backsEl.innerHTML = '';
        for (let i = 0; i < numBacks; i++) {
            const back = document.createElement('div');
            back.className = 'card-back';
            backsEl.appendChild(back);
        }

        // Status
        const statusEl = el.querySelector('.player-status');
        if (opp.finished) {
            statusEl.textContent = `#${opp.finish_rank}`;
        } else {
            statusEl.textContent = '';
        }
    }

    // Human active indicator
    const bottomEl = document.getElementById('player-bottom');
    bottomEl.classList.toggle('active-turn', gameState.current_player === 0);
}

function handFingerprint(hand) {
    // Order-independent fingerprint: sorted card_ints
    return hand.map(c => c.card_int).sort((a, b) => a - b).join(',');
}

function syncLocalHand() {
    // Build an order-independent fingerprint to detect actual card changes
    const serverHand = gameState.hand || [];
    const key = handFingerprint(serverHand);

    if (key !== lastServerHandKey) {
        lastServerHandKey = key;
        selectedCards.clear();

        if (localHand && localHand.length > 0) {
            // Preserve user's custom order: remove played cards, add new cards
            // Build count map of server hand
            const serverCounts = {};
            for (const c of serverHand) {
                serverCounts[c.card_int] = (serverCounts[c.card_int] || 0) + 1;
            }

            // Walk localHand, keep cards that still exist in server hand
            const kept = [];
            const usedCounts = {};
            for (const c of localHand) {
                const ci = c.card_int;
                const used = usedCounts[ci] || 0;
                if (used < (serverCounts[ci] || 0)) {
                    // Find the matching server card (may have updated info like is_wild)
                    const match = serverHand.find(sc => sc.card_int === ci);
                    kept.push(match || c);
                    usedCounts[ci] = used + 1;
                }
            }

            // Add any new cards from server not in localHand (e.g., tribute received)
            const keptCounts = {};
            for (const c of kept) {
                keptCounts[c.card_int] = (keptCounts[c.card_int] || 0) + 1;
            }
            const newCards = [];
            const addedCounts = {};
            for (const c of serverHand) {
                const ci = c.card_int;
                const have = (keptCounts[ci] || 0) + (addedCounts[ci] || 0);
                if (have < (serverCounts[ci] || 0)) {
                    newCards.push(c);
                    addedCounts[ci] = (addedCounts[ci] || 0) + 1;
                }
            }

            localHand = sortAscending ? [...newCards, ...kept] : [...kept, ...newCards];
        } else {
            // First time — use server order
            if (sortAscending) {
                localHand = serverHand.slice().reverse();
            } else {
                localHand = serverHand.slice();
            }
        }
    }
}

function renderHand() {
    syncLocalHand();

    const area = document.getElementById('hand-area');
    area.innerHTML = '';

    if (!localHand || localHand.length === 0) return;

    localHand.forEach((card, idx) => {
        const el = createCardElement(card, false);
        el.classList.toggle('selected', selectedCards.has(idx));
        el.setAttribute('draggable', 'true');
        el.dataset.idx = idx;

        // Click to select/deselect
        el.addEventListener('click', (e) => {
            // Ignore if this was the end of a drag
            if (el.dataset.wasDragged === 'true') {
                el.dataset.wasDragged = 'false';
                return;
            }
            if (!gameState.is_human_turn) return;
            if (selectedCards.has(idx)) {
                selectedCards.delete(idx);
            } else {
                selectedCards.add(idx);
            }
            renderHand();
            renderActionBar();
        });

        // Drag start
        el.addEventListener('dragstart', (e) => {
            dragSrcIdx = idx;
            el.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
        });

        // Drag over (allow drop)
        el.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            el.classList.add('drag-over');
        });

        el.addEventListener('dragleave', () => {
            el.classList.remove('drag-over');
        });

        // Drop — move card from dragSrcIdx to this position
        el.addEventListener('drop', (e) => {
            e.preventDefault();
            el.classList.remove('drag-over');
            if (dragSrcIdx === null || dragSrcIdx === idx) return;

            // Move the card in localHand
            const [moved] = localHand.splice(dragSrcIdx, 1);
            localHand.splice(idx, 0, moved);

            // Remap selected cards
            selectedCards.clear();

            dragSrcIdx = null;
            renderHand();
        });

        el.addEventListener('dragend', () => {
            el.classList.remove('dragging');
            el.dataset.wasDragged = 'true';
            dragSrcIdx = null;
        });

        area.appendChild(el);
    });
}

function createCardElement(card, mini = false) {
    const el = document.createElement('div');
    el.className = `card suit-${card.suit}`;
    if (mini) el.classList.add('mini');

    if (card.suit === 'joker') {
        el.classList.add(card.rank === 'B' ? 'joker-big' : 'joker-small');
    }

    // Badge: W for wild, L for level card (top-left)
    if (card.is_wild) {
        const badge = document.createElement('div');
        badge.className = 'card-badge badge-wild';
        badge.textContent = 'W';
        el.appendChild(badge);
    } else if (card.is_level) {
        const badge = document.createElement('div');
        badge.className = 'card-badge badge-level';
        badge.textContent = 'L';
        el.appendChild(badge);
    }

    const rankEl = document.createElement('div');
    rankEl.className = 'card-rank';
    if (card.suit === 'joker') {
        rankEl.textContent = t('joker');
    } else {
        rankEl.textContent = card.rank;
    }
    el.appendChild(rankEl);

    const suitEl = document.createElement('div');
    suitEl.className = 'card-suit';
    suitEl.textContent = card.suit_symbol;
    el.appendChild(suitEl);

    return el;
}

function renderTrick() {
    const tricks = gameState.trick_plays || [];
    const slotMap = { 0: 'trick-bottom', 1: 'trick-right', 2: 'trick-top', 3: 'trick-left' };
    // Top/bottom are horizontal (team axis), left/right are vertical (opponent axis)
    const isVertical = { 'trick-left': true, 'trick-right': true };

    // Clear all slots
    for (const id of Object.values(slotMap)) {
        document.getElementById(id).innerHTML = '';
    }

    const leadPlayer = gameState.lead_player;
    // Find the index of the last non-pass play from lead player (the actual leading hand)
    let leadIdx = -1;
    for (let i = tricks.length - 1; i >= 0; i--) {
        if (!tricks[i].is_pass && tricks[i].player === leadPlayer) { leadIdx = i; break; }
    }

    for (let ti = 0; ti < tricks.length; ti++) {
        const play = tricks[ti];
        const slotId = slotMap[play.player];
        const slot = document.getElementById(slotId);
        if (!slot) continue;

        const isLeading = ti === leadIdx;
        const entryClass = isVertical[slotId] ? 'trick-play-entry-v' : 'trick-play-entry-h';
        const entry = document.createElement('div');
        entry.className = entryClass;
        if (isLeading) entry.classList.add('trick-leading');

        const label = document.createElement('div');
        label.className = 'trick-label';
        label.textContent = playerLabel(play.player);

        const contentEl = document.createElement('div');
        if (play.is_pass) {
            contentEl.className = 'trick-pass';
            contentEl.textContent = t('pass');
        } else {
            contentEl.className = 'trick-cards';
            for (const c of play.cards) {
                contentEl.appendChild(createCardElement(c, true));
            }
        }
        // For right slot: content before label; otherwise label before content
        if (slotId === 'trick-right') {
            entry.appendChild(contentEl);
            entry.appendChild(label);
        } else {
            entry.appendChild(label);
            entry.appendChild(contentEl);
        }

        slot.appendChild(entry);
    }

    // Center message
    const msgEl = document.getElementById('center-message');
    msgEl.className = '';
    const lead = gameState.lead_player;
    const leadText = (lead !== null && lead !== undefined && gameState.phase === 'playing')
        ? `${t('leadPrefix')}: ${playerLabel(lead)}` : '';

    if (gameState.phase === 'playing' && gameState.is_human_turn && !autoPlayEnabled) {
        msgEl.innerHTML = `<div class="center-lead">${leadText}</div><div class="center-main your-turn">${t('yourTurnBig')}</div>`;
    } else if (gameState.phase === 'playing' && !gameState.is_human_turn && !autoPlayEnabled) {
        msgEl.innerHTML = `<div class="center-lead">${leadText}</div><div class="center-main">${playerLabel(gameState.current_player)} ${t('isThinking')}</div>`;
    } else {
        msgEl.innerHTML = '';
    }
}

function renderHints() {
    const area = document.getElementById('hint-area');
    const hints = gameState.hints || [];

    if (!hintEnabled || hints.length === 0 || !gameState.is_human_turn) {
        area.classList.add('hidden');
        return;
    }

    area.classList.remove('hidden');
    area.innerHTML = '';

    for (const hint of hints) {
        const item = document.createElement('div');
        item.className = 'hint-item';
        item.addEventListener('click', () => selectHintPlay(hint.card_ints));

        // Cards
        const cardsDiv = document.createElement('div');
        cardsDiv.className = 'hint-cards';
        if (hint.type === 'pass') {
            const passEl = document.createElement('div');
            passEl.className = 'hint-pass-icon';
            passEl.innerHTML = '🚫';
            cardsDiv.appendChild(passEl);
        } else {
            for (const c of hint.cards) {
                cardsDiv.appendChild(createCardElement(c, true));
            }
        }
        item.appendChild(cardsDiv);

        // Type + rank
        const typeEl = document.createElement('div');
        typeEl.className = 'hint-type';
        const typeStr = tPlayType(hint.type);
        typeEl.textContent = hint.rank ? `${typeStr} ${hint.rank}` : typeStr;
        item.appendChild(typeEl);

        // Q-value
        const qEl = document.createElement('div');
        qEl.className = 'hint-q-value';
        qEl.textContent = `Q: ${hint.q_value.toFixed(3)}`;
        item.appendChild(qEl);

        area.appendChild(item);
    }
}

function renderActionBar() {
    // Ensure buttons are visible (may have been hidden during tribute)
    document.getElementById('btn-play').classList.remove('hidden');
    document.getElementById('btn-pass').classList.remove('hidden');
    document.getElementById('btn-hint').classList.remove('hidden');
    document.getElementById('btn-auto').classList.remove('hidden');
    document.getElementById('btn-sort').classList.remove('hidden');

    const isMyTurn = gameState.is_human_turn && gameState.phase === 'playing';

    // Check if pass is a legal play (it's not available when leading)
    const hasPass = gameState.legal_plays && gameState.legal_plays.some(p => p.type === 'pass');

    document.getElementById('btn-play').disabled = !isMyTurn || selectedCards.size === 0;
    const clearBtn = document.getElementById('btn-clear');
    clearBtn.disabled = selectedCards.size === 0;
    clearBtn.textContent = t('clear');
    document.getElementById('btn-pass').disabled = !isMyTurn || !hasPass;
    document.getElementById('btn-pass').textContent = t('pass');

    const hintBtn = document.getElementById('btn-hint');
    hintBtn.textContent = hintEnabled ? t('hintOn') : t('hintOff');
    hintBtn.classList.toggle('active', hintEnabled);

    const autoBtn = document.getElementById('btn-auto');
    autoBtn.textContent = autoPlayEnabled ? t('autoOn') : t('autoOff');
    autoBtn.classList.toggle('active', autoPlayEnabled);

    document.getElementById('btn-sort').textContent = sortAscending ? t('sortAsc') : t('sortDesc');
    document.getElementById('btn-play').textContent = t('play');
}

function renderResult() {
    const overlay = document.getElementById('result-overlay');
    const result = gameState.result;

    if (!result || (gameState.phase !== 'round_over' && gameState.phase !== 'game_over')) {
        overlay.classList.add('hidden');
        return;
    }

    overlay.classList.remove('hidden');

    const titleEl = document.getElementById('result-title');
    if (result.human_won) {
        titleEl.textContent = t('victory');
        titleEl.className = 'win';
    } else {
        titleEl.textContent = t('defeat');
        titleEl.className = 'lose';
    }

    const detailsEl = document.getElementById('result-details');
    const fo = result.finish_order;
    const orderStr = fo.map((p, i) => `#${i + 1}: ${playerLabel(p)}`).join(' | ');

    let html = `<p>${t('finishOrder')}: ${orderStr}</p>`;
    html += `<p>${t('reward')}: ${result.rewards['0']}</p>`;

    if (result.team_levels) {
        const us = result.team_levels[0] === 14 ? 'A' : result.team_levels[0];
        const them = result.team_levels[1] === 14 ? 'A' : result.team_levels[1];
        html += `<p>${t('teamLevels')}: ${t('us')} ${us} vs ${t('them')} ${them}</p>`;
    }

    if (gameState.phase === 'game_over') {
        html += `<p style="font-size:1.3rem;margin-top:1rem">${result.human_won ? t('gameWon') : t('gameLost')}</p>`;
    }

    detailsEl.innerHTML = html;

    // Button text
    const newRoundBtn = document.getElementById('btn-new-round');
    if (gameState.phase === 'game_over') {
        newRoundBtn.textContent = t('newGame');
        newRoundBtn.onclick = backToMenu;
    } else if (gameState.mode === 'full_game') {
        newRoundBtn.textContent = t('nextRound');
        newRoundBtn.onclick = newRound;
    } else {
        newRoundBtn.textContent = t('newRound');
        newRoundBtn.onclick = newRound;
    }
}

function showMessage(msg) {
    const el = document.getElementById('center-message');
    el.textContent = msg;
    setTimeout(() => {
        if (el.textContent === msg) el.textContent = '';
    }, 2000);
}

// === Tribute Phase ===

function cardDisplayStr(cardInfo) {
    if (cardInfo.suit === 'joker') {
        return t('joker');
    }
    return cardInfo.rank + cardInfo.suit_symbol;
}

function renderTributeHand() {
    syncLocalHand();

    const area = document.getElementById('hand-area');
    area.innerHTML = '';

    if (!localHand || localHand.length === 0) return;

    const legalInts = new Set(
        (gameState.tribute_legal_cards || []).map(c => c.card_int)
    );

    localHand.forEach((card, idx) => {
        const el = createCardElement(card, false);
        el.setAttribute('draggable', 'true');
        el.dataset.idx = idx;

        // Highlight legal tribute cards
        if (legalInts.has(card.card_int)) {
            el.classList.add('tribute-legal');
            if (selectedTributeIdx === idx) {
                el.classList.add('selected');
            }
            el.addEventListener('click', (e) => {
                if (el.dataset.wasDragged === 'true') {
                    el.dataset.wasDragged = 'false';
                    return;
                }
                // Toggle selection
                selectedTributeIdx = (selectedTributeIdx === idx) ? null : idx;
                renderTributeHand();
                renderTributeActionBar();
            });
        }

        // Drag start
        el.addEventListener('dragstart', (e) => {
            dragSrcIdx = idx;
            el.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
        });

        // Drag over (allow drop)
        el.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            el.classList.add('drag-over');
        });

        el.addEventListener('dragleave', () => {
            el.classList.remove('drag-over');
        });

        // Drop — move card
        el.addEventListener('drop', (e) => {
            e.preventDefault();
            el.classList.remove('drag-over');
            if (dragSrcIdx === null || dragSrcIdx === idx) return;

            const [moved] = localHand.splice(dragSrcIdx, 1);
            localHand.splice(idx, 0, moved);

            dragSrcIdx = null;
            renderTributeHand();
        });

        el.addEventListener('dragend', () => {
            el.classList.remove('dragging');
            el.dataset.wasDragged = 'true';
            dragSrcIdx = null;
        });

        area.appendChild(el);
    });
}

function renderTributeActionBar() {
    const action = gameState.tribute_action;
    const target = gameState.tribute_target;

    // Hide most buttons during tribute, show Sort and Confirm
    document.getElementById('btn-pass').classList.add('hidden');
    document.getElementById('btn-hint').classList.add('hidden');
    document.getElementById('btn-auto').classList.add('hidden');
    document.getElementById('btn-sort').classList.remove('hidden');
    document.getElementById('btn-sort').textContent = sortAscending ? t('sortAsc') : t('sortDesc');

    // Repurpose the Play button as Confirm
    const playBtn = document.getElementById('btn-play');
    playBtn.classList.remove('hidden');
    playBtn.textContent = t('confirm');
    playBtn.disabled = selectedTributeIdx === null;
    playBtn.onclick = async () => {
        if (selectedTributeIdx === null) return;
        await tributeSubmitCard(localHand[selectedTributeIdx].card_int);
    };

    // Show tribute message in center
    const msgEl = document.getElementById('center-message');
    if (action === 'give') {
        msgEl.innerHTML = target !== null
            ? `${t('chooseGiveTo')} ${playerLabel(target)}`
            : t('chooseHighest');
    } else if (action === 'back') {
        msgEl.innerHTML = `${t('chooseReturnTo')} ${playerLabel(target)}`;
    }
}

async function tributeSubmitCard(cardInt) {
    selectedTributeIdx = null;
    const state = await api('/api/tribute-action', 'POST', {
        game_id: gameId, card_int: cardInt,
    });
    if (!state) return;
    gameState = state;

    // Restore normal button visibility when tribute ends
    if (state.phase !== 'tribute_give' && state.phase !== 'tribute_back') {
        const playBtn = document.getElementById('btn-play');
        playBtn.textContent = t('play');
        playBtn.onclick = () => playSelected();
        playBtn.classList.remove('hidden');
        document.getElementById('btn-pass').classList.remove('hidden');
        document.getElementById('btn-hint').classList.remove('hidden');
        document.getElementById('btn-auto').classList.remove('hidden');
        document.getElementById('btn-sort').classList.remove('hidden');
    }

    render();

    // After give phase completes (server paused), show give results overlay
    if (state.phase === 'tribute_give_done' && !tributeConfirmed) {
        showTributeGiveOverlay();
    }
    // After all tribute completes, show post-tribute overlay
    else if (state.phase === 'playing' && !tributeConfirmed) {
        showPostTributeOverlay();
    }
}

// === Persistent Tribute Card Display ===

function renderTributeCards() {
    // Render tribute received cards persistently in each player's area
    const records = gameState && gameState.tribute_records;
    const seatMap = { 1: 'player-right', 2: 'player-top', 3: 'player-left' };

    // Clear all tribute card areas
    for (const elId of Object.values(seatMap)) {
        const el = document.getElementById(elId);
        if (el) el.querySelector('.player-tribute-cards').innerHTML = '';
    }
    document.getElementById('my-tribute-cards').innerHTML = '';

    if (!records || records.length === 0) return;

    // Check anti-tribute (giver === receiver means anti)
    const isAnti = records[0].giver === records[0].receiver;
    if (isAnti) {
        // Show big joker cards at the holder's position
        const info = gameState.round_start_info;
        const holders = info && info.anti_holders || [];
        const bigJokerInfo = { card_int: 53, rank: 'B', suit: 'joker', suit_symbol: '🃏', is_wild: false, is_level: false };
        for (const holder of holders) {
            if (holder === 0) continue; // skip human
            const playerEl = document.getElementById(seatMap[holder]);
            if (!playerEl) continue;
            const container = playerEl.querySelector('.player-tribute-cards');
            if (!container) continue;
            const count = holders.length === 1 ? 2 : 1;
            for (let i = 0; i < count; i++) {
                const wrapper = document.createElement('div');
                wrapper.className = 'tribute-card-item';
                const label = document.createElement('div');
                label.className = 'tribute-label';
                label.textContent = '🃏';
                wrapper.appendChild(label);
                const cardEl = createCardElement(bigJokerInfo, true);
                cardEl.style.cursor = 'default';
                wrapper.appendChild(cardEl);
                container.appendChild(wrapper);
            }
        }
        return;
    }

    // Build per-seat received cards: { seat: [{card_info, from, action}] }
    // During in-progress tribute, records accumulate one at a time.
    // Each record has a "giver" and "receiver" — use that directly.
    const received = {};
    for (const r of records) {
        const seat = r.receiver;
        if (seat === undefined || seat === null || seat < 0) continue;
        if (!received[seat]) received[seat] = [];
        // Determine action: if giver gave to receiver and receiver != giver's teammate's
        // opponent, it's a "give"; otherwise "back". Simple heuristic: first half = give, second = back.
        // But during partial records we don't know. Just label all as 'give' for now —
        // the label arrow direction is cosmetic.
        received[seat].push({ card_info: r.card_info, from: r.giver, action: 'give' });
    }

    // Render for each player (skip human — no need to show own received cards)
    for (const [seat, items] of Object.entries(received)) {
        const seatNum = parseInt(seat);
        if (seatNum === 0) continue;
        let container;
        {
            const playerEl = document.getElementById(seatMap[seatNum]);
            if (!playerEl) continue;
            container = playerEl.querySelector('.player-tribute-cards');
        }
        if (!container) continue;

        for (const item of items) {
            if (!item.card_info) continue;
            const wrapper = document.createElement('div');
            wrapper.className = 'tribute-card-item';

            const arrow = item.action === 'give' ? '←' : '↩';
            const label = document.createElement('div');
            label.className = 'tribute-label';
            label.textContent = `${arrow}${playerLabel(item.from)}`;
            wrapper.appendChild(label);

            const cardEl = createCardElement(item.card_info, true);
            cardEl.style.cursor = 'default';
            wrapper.appendChild(cardEl);

            container.appendChild(wrapper);
        }
    }
}

// showTributeConfirmation removed — replaced by showRoundStartOverlay + showPostTributeOverlay
