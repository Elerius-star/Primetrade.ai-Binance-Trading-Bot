// Trading Bot Web Interface
let currentSymbol = 'BTCUSDT';
let currentSide = 'BUY';
let currentType = 'MARKET';
let previousPrices = {};
let recentOrders = [];

// ============================================
// 🔗 BACKEND URL - Update this to your Render URL
// ============================================
const API_BASE_URL = 'https://python-trading-bot-c9j0.onrender.com';

// Override fetch to use correct API URL
const originalFetch = window.fetch;
window.fetch = function(url, options) {
    if (typeof url === 'string' && url.startsWith('/api/')) {
        url = API_BASE_URL + url;
    }
    return originalFetch.call(this, url, options);
};

// Check backend status function
async function checkBackendStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/account_info`);
        if (response.ok) {
            const data = await response.json();
            document.getElementById('status-indicator').style.background = '#00ff88';
            document.getElementById('status-text').textContent = 'Connected to Testnet';
            document.getElementById('api-status').textContent = 'Online';
            
            // Check if in mock mode
            if (data.data && data.data.mock_mode) {
                document.getElementById('mode-status').textContent = 'MOCK MODE';
                document.getElementById('mode-status').style.color = '#ffaa00';
            } else {
                document.getElementById('mode-status').textContent = 'LIVE';
                document.getElementById('mode-status').style.color = '#00ff88';
            }
            return true;
        }
    } catch (error) {
        console.error('Backend connection error:', error);
        document.getElementById('status-indicator').style.background = '#ff3366';
        document.getElementById('status-text').textContent = 'Backend Offline';
        document.getElementById('api-status').textContent = 'Offline';
        document.getElementById('mode-status').textContent = 'Offline';
        
        showToast('⚠️ Backend server not responding!', 'error');
        return false;
    }
}

// Toast notification function
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Add recent order to activity
function addRecentOrder(orderData, result) {
    const order = {
        id: result.order_id,
        symbol: orderData.symbol,
        side: orderData.side,
        quantity: orderData.quantity,
        price: result.avg_price || orderData.price || 'Market',
        time: new Date().toLocaleTimeString(),
        status: result.status
    };
    recentOrders.unshift(order);
    if (recentOrders.length > 10) recentOrders.pop();
    updateActivityList();
}

// Update activity list
function updateActivityList() {
    const activityList = document.getElementById('recent-orders');
    if (!activityList) return;
    
    if (recentOrders.length === 0) {
        activityList.innerHTML = '<div class="activity-item">No recent orders</div>';
        return;
    }
    
    activityList.innerHTML = recentOrders.map(order => `
        <div class="activity-item">
            <strong>${order.time}</strong> - ${order.side} ${order.symbol} 
            ${order.quantity} @ ${order.price} 
            <span style="color: ${order.status === 'FILLED' ? '#00ff88' : '#ffaa00'}">
                (${order.status})
            </span>
        </div>
    `).join('');
}

// Initialize page
document.addEventListener('DOMContentLoaded', async () => {
    // Hide loading overlay after delay
    setTimeout(() => {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.classList.add('fade-out');
            setTimeout(() => {
                overlay.style.display = 'none';
            }, 500);
        }
    }, 1000);
    
    initializeNavigation();
    initializeForm();
    updateOrderPreview();
    
    // Check backend connection
    const backendRunning = await checkBackendStatus();
    
    if (backendRunning) {
        loadPrices();
        loadAccountInfo();
        
        // Refresh prices every 5 seconds
        setInterval(loadPrices, 5000);
        setInterval(loadAccountInfo, 10000);
    } else {
        // Show demo mode message
        const symbols = ['btc', 'eth', 'bnb', 'sol'];
        symbols.forEach(symbol => {
            const priceElement = document.getElementById(`${symbol}-price`);
            if (priceElement) priceElement.textContent = 'Offline';
        });
        document.getElementById('total-balance').textContent = 'Backend Offline';
        document.getElementById('available-balance').textContent = 'Start server to trade';
    }
});

function initializeNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.dataset.page;
            
            // Update active states
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
            
            // Show selected page
            document.querySelectorAll('.page').forEach(pageElem => {
                pageElem.classList.remove('active');
            });
            document.getElementById(`${page}-page`).classList.add('active');
            
            // Load page-specific data
            if (page === 'portfolio') {
                loadPortfolio();
            } else if (page === 'history') {
                loadHistory();
            }
        });
    });
}

function initializeForm() {
    // Side buttons
    document.querySelectorAll('.side-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.side-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentSide = btn.dataset.side;
            document.getElementById('side').value = currentSide;
            updateOrderPreview();
        });
    });
    
    // Type buttons
    document.querySelectorAll('.type-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.type-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentType = btn.dataset.type;
            document.getElementById('order-type').value = currentType;
            
            // Show/hide price field for limit orders
            const priceGroup = document.getElementById('price-group');
            if (currentType === 'LIMIT') {
                priceGroup.style.display = 'block';
            } else {
                priceGroup.style.display = 'none';
            }
            updateOrderPreview();
        });
    });
    
    // Symbol change
    document.getElementById('symbol').addEventListener('change', (e) => {
        currentSymbol = e.target.value;
        loadMarketPrice();
        updateOrderPreview();
    });
    
    // Quantity change
    document.getElementById('quantity').addEventListener('input', () => {
        updateOrderPreview();
    });
    
    // Price change
    const priceInput = document.getElementById('price');
    if (priceInput) {
        priceInput.addEventListener('input', () => {
            updateOrderPreview();
        });
    }
    
    // Form submission
    document.getElementById('order-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        await placeOrder();
    });
    
    // Load initial market price
    loadMarketPrice();
}

function updateOrderPreview() {
    const previewDiv = document.getElementById('order-preview');
    const previewDetails = document.getElementById('preview-details');
    
    if (!previewDiv || !previewDetails) return;
    
    const symbol = document.getElementById('symbol').value;
    const side = currentSide;
    const orderType = currentType;
    const quantity = parseFloat(document.getElementById('quantity').value);
    const price = orderType === 'LIMIT' ? parseFloat(document.getElementById('price')?.value) : null;
    const marketPrice = parseFloat(document.getElementById('market-price')?.textContent?.replace(/[^0-9.-]+/g, '') || '0');
    
    if (!quantity || quantity <= 0) {
        previewDiv.style.display = 'none';
        return;
    }
    
    previewDiv.style.display = 'block';
    
    let estimatedTotal = 0;
    if (orderType === 'MARKET' && marketPrice) {
        estimatedTotal = quantity * marketPrice;
    } else if (orderType === 'LIMIT' && price) {
        estimatedTotal = quantity * price;
    }
    
    previewDetails.innerHTML = `
        <strong>Order Type:</strong> ${orderType} ${side}<br>
        <strong>Symbol:</strong> ${symbol}<br>
        <strong>Quantity:</strong> ${quantity}<br>
        ${price ? `<strong>Limit Price:</strong> $${price.toFixed(2)}<br>` : ''}
        <strong>Estimated Total:</strong> $${estimatedTotal.toFixed(2)}<br>
        <small style="color: #ffaa00;">⚠️ Preview only, actual price may vary</small>
    `;
}

async function loadPrices() {
    const symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT'];
    
    for (const symbol of symbols) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/price/${symbol}`);
            const data = await response.json();
            
            if (data.success) {
                const priceElement = document.getElementById(`${symbol.toLowerCase()}-price`);
                if (priceElement) {
                    const currentPrice = data.price;
                    priceElement.textContent = `$${currentPrice.toLocaleString(undefined, {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    })}`;
                    
                    // Calculate and show price change
                    if (previousPrices[symbol]) {
                        const change = currentPrice - previousPrices[symbol];
                        const changePercent = (change / previousPrices[symbol]) * 100;
                        const changeElement = document.getElementById(`${symbol.toLowerCase()}-change`);
                        if (changeElement) {
                            changeElement.textContent = `${change >= 0 ? '▲' : '▼'} ${Math.abs(changePercent).toFixed(2)}%`;
                            changeElement.className = `change ${change >= 0 ? 'positive' : 'negative'}`;
                        }
                    }
                    previousPrices[symbol] = currentPrice;
                }
            }
        } catch (error) {
            console.error(`Failed to load ${symbol} price:`, error);
        }
    }
}

async function loadMarketPrice() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/price/${currentSymbol}`);
        const data = await response.json();
        
        if (data.success) {
            const priceElement = document.getElementById('market-price');
            if (priceElement) {
                priceElement.innerHTML = `
                    <i class="fas fa-chart-line"></i> 
                    Current: $${data.price.toLocaleString(undefined, {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    })}
                `;
                updateOrderPreview();
            }
        }
    } catch (error) {
        console.error('Failed to load market price:', error);
        const priceElement = document.getElementById('market-price');
        if (priceElement) priceElement.textContent = 'Error loading price';
    }
}

async function loadAccountInfo() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/account_info`);
        const data = await response.json();
        
        if (data.success && data.data) {
            let totalBalance = 0;
            let availableBalance = 0;
            let totalPnl = 0;
            
            if (data.data.assets) {
                data.data.assets.forEach(asset => {
                    if (asset.asset === 'USDT') {
                        totalBalance = parseFloat(asset.walletBalance || 0);
                        availableBalance = parseFloat(asset.availableBalance || 0);
                        totalPnl = parseFloat(asset.unrealizedProfit || 0);
                    }
                });
            }
            
            const totalBalanceElem = document.getElementById('total-balance');
            const availableBalanceElem = document.getElementById('available-balance');
            const totalPnlElem = document.getElementById('total-pnl');
            
            if (totalBalanceElem) totalBalanceElem.textContent = `$${totalBalance.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
            if (availableBalanceElem) availableBalanceElem.textContent = `$${availableBalance.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
            if (totalPnlElem) {
                totalPnlElem.textContent = `$${totalPnl.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
                totalPnlElem.style.color = totalPnl >= 0 ? '#00ff88' : '#ff3366';
            }
        }
    } catch (error) {
        console.error('Failed to load account info:', error);
    }
}

async function loadPortfolio() {
    const portfolioContent = document.getElementById('portfolio-content');
    if (!portfolioContent) return;
    
    portfolioContent.innerHTML = '<div class="loading">Loading portfolio data...</div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/account_info`);
        const data = await response.json();
        
        if (data.success && data.data && data.data.assets) {
            let html = '<div class="portfolio-table"><table><thead><tr><th>Asset</th><th>Wallet Balance</th><th>Available Balance</th><th>Unrealized PnL</th></tr></thead><tbody>';
            
            data.data.assets.forEach(asset => {
                const walletBalance = parseFloat(asset.walletBalance || 0);
                if (walletBalance > 0 || asset.asset === 'USDT') {
                    const pnl = parseFloat(asset.unrealizedProfit || 0);
                    html += `
                        <tr>
                            <td><strong>${asset.asset}</strong></td>
                            <td>$${walletBalance.toFixed(2)}</td>
                            <td>$${parseFloat(asset.availableBalance || 0).toFixed(2)}</td>
                            <td class="${pnl >= 0 ? 'profit' : 'loss'}">$${pnl.toFixed(2)}</td>
                        </tr>
                    `;
                }
            });
            
            html += '</tbody></table></div>';
            portfolioContent.innerHTML = html;
        } else {
            portfolioContent.innerHTML = '<div class="info-box"><i class="fas fa-exclamation-triangle"></i><p>Failed to load portfolio data</p></div>';
        }
    } catch (error) {
        console.error('Failed to load portfolio:', error);
        portfolioContent.innerHTML = '<div class="info-box"><i class="fas fa-exclamation-triangle"></i><p>Error loading portfolio data</p></div>';
    }
}

function loadHistory() {
    const historyContent = document.getElementById('history-content');
    if (!historyContent) return;
    
    if (recentOrders.length === 0) {
        historyContent.innerHTML = `
            <div class="info-box">
                <i class="fas fa-info-circle"></i>
                <p>Order history will appear here after placing trades</p>
                <small>Check the logs folder for detailed order history</small>
            </div>
        `;
        return;
    }
    
    historyContent.innerHTML = `
        <div class="portfolio-table">
            <table>
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Symbol</th>
                        <th>Side</th>
                        <th>Quantity</th>
                        <th>Price</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    ${recentOrders.map(order => `
                        <tr>
                            <td>${order.time}</td>
                            <td>${order.symbol}</td>
                            <td style="color: ${order.side === 'BUY' ? '#00ff88' : '#ff3366'}">${order.side}</td>
                            <td>${order.quantity}</td>
                            <td>${typeof order.price === 'number' ? '$' + order.price.toFixed(2) : order.price}</td>
                            <td style="color: ${order.status === 'FILLED' ? '#00ff88' : '#ffaa00'}">${order.status}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

async function placeOrder() {
    const symbol = document.getElementById('symbol').value;
    const side = document.getElementById('side').value;
    const orderType = document.getElementById('order-type').value;
    const quantity = parseFloat(document.getElementById('quantity').value);
    const price = orderType === 'LIMIT' ? parseFloat(document.getElementById('price')?.value) : null;
    
    // Validate inputs
    if (!quantity || quantity <= 0) {
        showOrderResult(false, 'Please enter a valid quantity');
        showToast('Please enter a valid quantity', 'error');
        return;
    }
    
    if (orderType === 'LIMIT' && (!price || price <= 0)) {
        showOrderResult(false, 'Please enter a valid limit price');
        showToast('Please enter a valid limit price', 'error');
        return;
    }
    
    const orderData = {
        symbol,
        side,
        orderType,
        quantity,
        price
    };
    
    showToast('Placing order...', 'info');
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/place_order`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(orderData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showOrderResult(true, `
                <strong>✅ Order Placed Successfully!</strong><br>
                <strong>Order ID:</strong> ${result.order_id}<br>
                <strong>Status:</strong> ${result.status}<br>
                <strong>Executed Quantity:</strong> ${result.executed_qty}<br>
                ${result.avg_price ? `<strong>Average Price:</strong> $${parseFloat(result.avg_price).toFixed(2)}` : ''}
            `);
            showToast('Order placed successfully!', 'success');
            
            // Add to recent orders
            addRecentOrder(orderData, result);
            
            // Reset form
            document.getElementById('quantity').value = '';
            if (document.getElementById('price')) {
                document.getElementById('price').value = '';
            }
            
            // Refresh account info and prices
            loadAccountInfo();
            loadPrices();
        } else {
            showOrderResult(false, `❌ Order Failed: ${result.error}`);
            showToast(`Order failed: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Order placement error:', error);
        showOrderResult(false, `❌ Network error: ${error.message}`);
        showToast(`Network error: ${error.message}`, 'error');
    }
}

function showOrderResult(success, message) {
    const resultDiv = document.getElementById('order-result');
    if (!resultDiv) return;
    
    resultDiv.className = `order-result ${success ? 'success' : 'error'}`;
    resultDiv.innerHTML = `
        <i class="fas ${success ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
        <div style="margin-left: 15px;">${message}</div>
    `;
    resultDiv.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        resultDiv.style.opacity = '0';
        setTimeout(() => {
            resultDiv.style.display = 'none';
            resultDiv.style.opacity = '1';
        }, 500);
    }, 5000);
}

function quickOrder(side) {
    // Navigate to orders page
    const ordersNav = document.querySelector('[data-page="orders"]');
    if (ordersNav) ordersNav.click();
    
    // Set side
    const sideBtn = document.querySelector(`.side-btn[data-side="${side}"]`);
    if (sideBtn) sideBtn.click();
    
    // Set symbol to BTCUSDT for quick orders
    const symbolSelect = document.getElementById('symbol');
    if (symbolSelect) symbolSelect.value = 'BTCUSDT';
    
    // Set quantity to default
    const quantityInput = document.getElementById('quantity');
    if (quantityInput) quantityInput.value = '0.001';
    
    // Scroll to order form
    document.querySelector('.order-form-container')?.scrollIntoView({
        behavior: 'smooth'
    });
    
    showToast(`Quick ${side} order ready. Adjust quantity if needed and submit.`, 'info');
}
