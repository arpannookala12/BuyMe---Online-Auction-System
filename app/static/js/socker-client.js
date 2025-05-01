// Initialize Socket.IO when the page loads
document.addEventListener('DOMContentLoaded', function() {
    // Check if the user is logged in (simplified - actual implementation would be more robust)
    const isLoggedIn = document.querySelector('.dropdown-toggle') !== null;
    
    if (isLoggedIn) {
        // Initialize Socket.IO
        const socket = io();
        
        // Set up global event listeners
        setupGlobalListeners(socket);
        
        // Set up page-specific listeners
        setupPageSpecificListeners(socket);
        
        // Handle any notifications
        setupNotificationListeners(socket);
    }
});

function setupGlobalListeners(socket) {
    // Handle connection events
    socket.on('connect', function() {
        console.log('Connected to BuyMe real-time services');
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from BuyMe real-time services');
    });
    
    socket.on('error', function(error) {
        console.error('Socket.IO error:', error);
    });
}

function setupPageSpecificListeners(socket) {
    // Check if we're on an auction page
    const auctionIdElement = document.getElementById('auction-id');
    if (auctionIdElement) {
        const auctionId = auctionIdElement.value;
        
        // Join the auction room
        socket.emit('join_auction', {
            auction_id: auctionId
        });
        
        // Set up bid form submission
        const bidForm = document.getElementById('bid-form');
        if (bidForm) {
            bidForm.addEventListener('submit', function(event) {
                event.preventDefault();
                
                const bidAmount = parseFloat(document.getElementById('bid_amount').value);
                let autoBidLimit = document.getElementById('auto_bid_limit')?.value;
                autoBidLimit = autoBidLimit ? parseFloat(autoBidLimit) : null;
                
                socket.emit('new_bid', {
                    auction_id: auctionId,
                    bid_amount: bidAmount,
                    auto_bid_limit: autoBidLimit
                });
            });
        }
        
        // Listen for bid updates
        socket.on('bid_update', function(data) {
            updateAuctionUI(data);
        });
    }
}

function setupNotificationListeners(socket) {
    // Listen for outbid notifications
    socket.on('outbid_notification', function(data) {
        showOutbidNotification(data);
    });
    
    // Listen for new auction notifications matching alerts
    socket.on('new_auction_alert', function(data) {
        showNewAuctionNotification(data);
    });
    
    // Listen for auction ending soon notifications
    socket.on('auction_ending_notification', function(data) {
        showAuctionEndingNotification(data);
    });
}

function updateAuctionUI(data) {
    // Update current price
    const currentPriceElements = document.querySelectorAll('.current-price');
    currentPriceElements.forEach(function(element) {
        element.textContent = '$' + data.current_price.toFixed(2);
    });
    
    // Update bid count
    const bidCountElements = document.querySelectorAll('.bid-count');
    bidCountElements.forEach(function(element) {
        element.textContent = data.num_bids;
    });
    
    // Update next minimum bid amount
    const minBidElements = document.querySelectorAll('.min-bid');
    minBidElements.forEach(function(element) {
        element.textContent = '$' + data.next_min_bid.toFixed(2);
    });
    
    // Update bid form if it exists
    const bidAmountInput = document.getElementById('bid_amount');
    if (bidAmountInput) {
        bidAmountInput.min = data.next_min_bid.toFixed(2);
        bidAmountInput.value = '';
        
        const bidAmountHelp = document.getElementById('bid-amount-help');
        if (bidAmountHelp) {
            bidAmountHelp.textContent = `Minimum bid: $${data.next_min_bid.toFixed(2)}`;
        }
    }
    
    // Show notification about the new bid
    const bidNotificationArea = document.getElementById('bid-notification');
    if (bidNotificationArea) {
        const notificationDiv = document.createElement('div');
        notificationDiv.className = 'alert alert-success alert-dismissible fade show';
        notificationDiv.setAttribute('role', 'alert');
        
        notificationDiv.innerHTML = `
            New bid: $${data.current_price.toFixed(2)} by ${data.highest_bidder_username}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        bidNotificationArea.appendChild(notificationDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(function() {
            notificationDiv.remove();
        }, 5000);
    }
    
    // Optionally refresh the bid history section via AJAX
    const bidHistorySection = document.getElementById('bid-history');
    if (bidHistorySection) {
        // This would be implemented with a fetch call to get updated bid history
        // fetch(`/api/auction/${data.auction_id}/bids`)...
    }
}

function showOutbidNotification(data) {
    const notificationsArea = document.getElementById('global-notifications');
    if (notificationsArea) {
        const notificationDiv = document.createElement('div');
        notificationDiv.className = 'alert alert-warning alert-dismissible fade show';
        notificationDiv.setAttribute('role', 'alert');
        
        notificationDiv.innerHTML = `
            You've been outbid on "${data.auction_title}"!
            New highest bid: $${data.new_highest_bid.toFixed(2)}
            <a href="/auction/${data.auction_id}" class="alert-link">Place a new bid</a>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        notificationsArea.appendChild(notificationDiv);
    }
    
    // Play a notification sound if browser allows
    playNotificationSound();
}

function showNewAuctionNotification(data) {
    const notificationsArea = document.getElementById('global-notifications');
    if (notificationsArea) {
        const notificationDiv = document.createElement('div');
        notificationDiv.className = 'alert alert-info alert-dismissible fade show';
        notificationDiv.setAttribute('role', 'alert');
        
        notificationDiv.innerHTML = `
            New auction matching your alert: "${data.auction_title}"
            <a href="/auction/${data.auction_id}" class="alert-link">View Auction</a>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        notificationsArea.appendChild(notificationDiv);
    }
}

function showAuctionEndingNotification(data) {
    const notificationsArea = document.getElementById('global-notifications');
    if (notificationsArea) {
        const notificationDiv = document.createElement('div');
        notificationDiv.className = 'alert alert-warning alert-dismissible fade show';
        notificationDiv.setAttribute('role', 'alert');
        
        notificationDiv.innerHTML = `
            Auction ending soon: "${data.auction_title}" (${data.time_left} left)
            <a href="/auction/${data.auction_id}" class="alert-link">View Auction</a>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        notificationsArea.appendChild(notificationDiv);
    }
}

function playNotificationSound() {
    try {
        // Create a simple beep sound
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 800;
        gainNode.gain.value = 0.1;
        
        oscillator.start();
        setTimeout(function() {
            oscillator.stop();
        }, 200);
    } catch (e) {
        console.log('Audio notification failed:', e);
    }
}