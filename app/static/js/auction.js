document.addEventListener('DOMContentLoaded', function() {
    // Get the end time from the data attribute
    const endTimeElement = document.querySelector('[data-end-time]');
    if (!endTimeElement) return;

    const endTime = new Date(endTimeElement.dataset.endTime).getTime();
    const timerElement = document.getElementById('countdown-timer');
    const auctionStatusElement = document.getElementById('auction-status');

    function updateTimer() {
        const now = new Date().getTime();
        const distance = endTime - now;

        if (distance <= 0) {
            // Auction has ended
            timerElement.innerHTML = 'Auction has ended';
            if (auctionStatusElement) {
                auctionStatusElement.innerHTML = 'Auction has ended';
            }
            return;
        }

        // Calculate time units
        const hours = Math.floor(distance / (1000 * 60 * 60));
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);

        // Display the result
        timerElement.innerHTML = `${hours}h ${minutes}m ${seconds}s`;
    }

    // Update the timer immediately and then every second
    updateTimer();
    setInterval(updateTimer, 1000);
});

// Socket.io notification handling
const socket = io();

socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('notification', (data) => {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${data.type === 'error' ? 'danger' : 'info'} alert-dismissible fade show`;
    notification.innerHTML = `
        <strong>${data.title}</strong>
        <p>${data.message}</p>
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    // Add notification to the container
    const container = document.getElementById('global-notifications');
    if (container) {
        container.appendChild(notification);
    }

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 150);
    }, 5000);
});

function initAuctionSocket(auctionId) {
    const socket = io();
    
    // Join auction room
    socket.emit('join_auction', { auction_id: auctionId });
    
    // Handle new questions
    socket.on('new_question', function(data) {
        const questionsContainer = document.querySelector('.questions-container');
        if (questionsContainer) {
            // Reload questions section
            fetch(`/auction/${auctionId}/questions`)
                .then(response => response.text())
                .then(html => {
                    questionsContainer.innerHTML = html;
                });
        }
    });
    
    // Handle new answers
    socket.on('new_answer', function(data) {
        const questionsContainer = document.querySelector('.questions-container');
        if (questionsContainer) {
            // Reload questions section
            fetch(`/auction/${auctionId}/questions`)
                .then(response => response.text())
                .then(html => {
                    questionsContainer.innerHTML = html;
                });
        }
    });
    
    // Handle notifications
    socket.on('notification', function(data) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${data.type === 'error' ? 'danger' : 'info'} alert-dismissible fade show`;
        notification.innerHTML = `
            <strong>${data.title}</strong>
            <p>${data.message}</p>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Add notification to the container
        const container = document.getElementById('global-notifications');
        if (container) {
            container.appendChild(notification);
        }

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 150);
        }, 5000);
    });
    
    // Handle new bids
    socket.on('new_bid', function(data) {
        // Update current price
        const currentPrice = document.querySelector('.current-price');
        if (currentPrice) {
            currentPrice.textContent = `$${data.amount.toFixed(2)}`;
        }
        
        // Update bid history
        const bidHistory = document.querySelector('.bid-history');
        if (bidHistory) {
            const bidItem = document.createElement('div');
            bidItem.className = 'bid-item';
            bidItem.innerHTML = `
                <span class="bidder">${data.username}</span>
                <span class="bid-amount">$${data.amount.toFixed(2)}</span>
                <span class="bid-time">${new Date(data.timestamp).toLocaleString()}</span>
            `;
            bidHistory.insertBefore(bidItem, bidHistory.firstChild);
        }
    });
    
    // Handle auction end
    socket.on('auction_ended', function(data) {
        // Update auction status
        const auctionStatus = document.querySelector('.auction-status');
        if (auctionStatus) {
            auctionStatus.textContent = 'Auction Ended';
            auctionStatus.classList.add('ended');
        }
        
        // Disable bid form
        const bidForm = document.querySelector('#bid-form');
        if (bidForm) {
            bidForm.style.display = 'none';
        }
    });
    
    // Handle auction cancellation
    socket.on('auction_cancelled', function(data) {
        // Update auction status
        const auctionStatus = document.querySelector('.auction-status');
        if (auctionStatus) {
            auctionStatus.textContent = 'Auction Cancelled';
            auctionStatus.classList.add('cancelled');
        }
        
        // Disable bid form
        const bidForm = document.querySelector('#bid-form');
        if (bidForm) {
            bidForm.style.display = 'none';
        }
    });
} 