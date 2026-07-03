const sectorNames = ["XLK","XLY","XLP","XLE","XLF","XLI","XLV","XLB","XLU","XLC","XLRE"];
const defaultZ = [1.2, 0.8, -0.2, 0.0, -0.5, 0.3, 0.1, -0.4, 0.6, -0.1, 0.9];
const wasmBuildPath = 'sector_heatmap.wasm';
const fallbackColors = ['#0B3D91','#1E90FF','#3CB371','#FFD700','#FF8C00','#8A2BE2','#DC143C','#2F4F4F','#708090','#B22222','#4B0082'];

function zscore(values) {
    const filtered = values.filter(v => Number.isFinite(v));
    if (!filtered.length) return values.map(() => 0);
    const mean = filtered.reduce((sum, v) => sum + v, 0) / filtered.length;
    const variance = filtered.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / filtered.length;
    const stddev = Math.sqrt(variance) || 1;
    return values.map(v => Number.isFinite(v) ? (v - mean) / stddev : 0);
}

function renderHeatmap(data) {
    const placeholder = document.getElementById('heatmap-placeholder');
    placeholder.innerHTML = '';

    const grid = document.createElement('div');
    grid.className = 'heatmap-grid';

    data.sectors.forEach(sector => {
        const card = document.createElement('div');
        card.className = 'heatmap-card';
        card.style.borderColor = sector.color;

        const title = document.createElement('div');
        title.className = 'heatmap-card-title';
        title.textContent = sector.name;

        const value = document.createElement('div');
        value.className = 'heatmap-card-value';
        value.textContent = sector.z.toFixed(2);
        value.style.color = sector.z >= 0 ? '#8ef0a0' : '#ff8282';

        const bar = document.createElement('div');
        bar.className = 'heatmap-card-bar';
        bar.style.background = sector.color;
        bar.style.width = `${Math.min(100, Math.abs(sector.z) * 18)}%`;

        card.appendChild(title);
        card.appendChild(value);
        card.appendChild(bar);
        grid.appendChild(card);
    });

    placeholder.appendChild(grid);
}

function renderTradeTicket(orders) {
    const ticket = document.getElementById('order-ticket-placeholder');
    ticket.innerHTML = '';

    orders.forEach(order => {
        const item = document.createElement('div');
        item.className = 'ticket-item';
        item.innerHTML = `<strong>${order.ticker}</strong> — ${order.action}<span>${order.weight}</span>`;
        ticket.appendChild(item);
    });
}

function renderScorecard(ratios) {
    const scorecard = document.getElementById('scorecard-placeholder');
    scorecard.innerHTML = '';

    Object.entries(ratios).forEach(([key, value]) => {
        const row = document.createElement('div');
        row.className = 'scorecard-row';
        row.innerHTML = `<strong>${key}</strong><span>${value}</span>`;
        scorecard.appendChild(row);
    });
}

function renderStatus(message) {
    const heatmapStatus = document.getElementById('heatmap-status');
    const orderTicketStatus = document.getElementById('order-ticket-status');
    heatmapStatus.textContent = message;
    orderTicketStatus.textContent = message;
}

function loadWasmModule() {
    if (typeof WarRoomModule === 'function') {
        return WarRoomModule({
            locateFile: path => path.endsWith('.wasm') ? wasmBuildPath : path
        });
    }
    return Promise.reject(new Error('WASM module loader not found'));
}

function renderFallback(reason) {
    const z = zscore(defaultZ);
    const sectors = sectorNames.map((name, index) => ({
        name,
        z: z[index],
        color: fallbackColors[index]
    }));

    renderHeatmap({ sectors });
    renderTradeTicket([
        { ticker: 'XLK', action: 'BUY', weight: '15%' },
        { ticker: 'XLY', action: 'BUY', weight: '13%' },
        { ticker: 'XLB', action: 'HOLD', weight: '0%' }
    ]);
    renderScorecard({
        'Institutional Signal': 'Neutral-to-Bullish',
        'Current Liquidity': 'Balanced',
        'Volatility Warning': 'Moderate',
        'Execution Risk': 'Low'
    });
    renderStatus('WASM fallback active: ' + (reason || 'live module unavailable'));
}

function initPage() {
    renderStatus('Initializing heatmap engine…');

    loadWasmModule()
        .then(module => {
            renderStatus('WASM module loaded');
            const json = module.build_sector_heatmap(defaultZ);
            const data = JSON.parse(json);

            renderHeatmap(data);
            renderTradeTicket([
                { ticker: 'XLK', action: 'BUY', weight: '18%' },
                { ticker: 'XLY', action: 'BUY', weight: '16%' },
                { ticker: 'XLB', action: 'HOLD', weight: '0%' }
            ]);
            renderScorecard({
                'WASM Mode': 'Active',
                'Data Source': 'C++ Engine',
                'UI Experience': 'High Fidelity',
                'Crash Safety': 'Enabled'
            });
        })
        .catch(error => {
            console.warn('WASM load failed:', error);
            renderFallback(error.message);
        });
}

window.addEventListener('DOMContentLoaded', initPage);

