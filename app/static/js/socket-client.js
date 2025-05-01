document.addEventListener('DOMContentLoaded', function() {
    const socket = io();
    
    // Get user ID from data attribute
    const userId = document.body.dataset.userId;
    
    // Join user's personal room for notifications
    if (userId) {
        socket.emit('join_user_room', { user_id: userId });
    }
    
    // Join auction room if on auction page
    const auctionId = document.querySelector('[data-auction-id]')?.dataset.auctionId;
    if (auctionId) {
        socket.emit('join_auction_room', { auction_id: auctionId });
    }
    
    // Handle new bid event
    socket.on('new_bid', function(data) {
        // Update bid history table
        const tbody = document.getElementById('bid-history-body');
        if (tbody) {
            const newRow = document.createElement('tr');
            newRow.innerHTML = `
                <td>${data.bidder_username}</td>
                <td>$${data.amount.toFixed(2)}</td>
                <td>${new Date(data.created_at).toLocaleString()}</td>
                <td>
                    ${data.is_auto_bid ? 
                        '<span class="badge bg-info">Auto</span>' : 
                        '<span class="badge bg-primary">Manual</span>'
                    }
                </td>
                ${data.is_customer_rep ? 
                    '<td><form action="/auctions/' + data.auction_id + '/remove-bid/' + data.bid_id + '" method="POST" class="d-inline">' +
                    '<button type="submit" class="btn btn-danger btn-sm" onclick="return confirm(\'Are you sure you want to remove this bid?\')">Remove</button>' +
                    '</form></td>' : 
                    ''
                }
            `;
            tbody.insertBefore(newRow, tbody.firstChild);

            // Update bid count
            const bidCountElement = document.querySelector('[data-bid-count]');
            if (bidCountElement) {
                const currentCount = parseInt(bidCountElement.dataset.bidCount) + 1;
                bidCountElement.dataset.bidCount = currentCount;
                bidCountElement.textContent = `Number of bids: ${currentCount}`;
            }
        }
        
        // Update current price
        const currentPriceElement = document.querySelector('.text-primary');
        if (currentPriceElement) {
            currentPriceElement.textContent = `$${data.amount.toFixed(2)}`;
        }
        
        // Update minimum bid amount
        const bidAmountInput = document.getElementById('bid_amount');
        if (bidAmountInput) {
            const minAmount = data.amount + parseFloat(bidAmountInput.dataset.minIncrement);
            bidAmountInput.min = minAmount.toFixed(2);
            bidAmountInput.value = minAmount.toFixed(2);
        }
    });
    
    // Handle outbid notifications
    socket.on('outbid', function(data) {
        showNotification('You Have Been Outbid', 
            `You have been outbid on auction "${data.auction_title}". New bid: $${data.new_bid_amount.toFixed(2)}`,
            'warning',
            `/auctions/${data.auction_id}`
        );
    });
    
    // Handle auto-bid notifications
    socket.on('auto_bid', function(data) {
        showNotification('Auto-bid Placed', 
            `Your auto-bid of $${data.amount.toFixed(2)} was placed on auction "${data.auction_title}"`,
            'info',
            `/auctions/${data.auction_id}`
        );
    });
    
    // Handle auto-bid limit reached notifications
    socket.on('auto_bid_limit', function(data) {
        showNotification('Auto-bid Limit Reached', 
            `Your auto-bid limit of $${data.limit.toFixed(2)} has been reached for auction "${data.auction_title}"`,
            'warning',
            `/auctions/${data.auction_id}`
        );
    });
    
    // Handle auction ended notifications
    socket.on('auction_ended', function(data) {
        showNotification('Auction Ended', 
            data.winner ? 
                `The auction "${data.auction_title}" has ended. Winner: ${data.winner}` :
                `The auction "${data.auction_title}" has ended. No winner was determined.`,
            'info',
            `/auctions/${data.auction_id}`
        );
        
        // Update auction status if on auction page
        const countdownTimer = document.getElementById('countdown-timer');
        if (countdownTimer) {
            countdownTimer.innerHTML = 'Auction has ended';
            
            // Update winner information
            const winnerInfo = document.createElement('div');
            winnerInfo.className = 'alert alert-info';
            winnerInfo.innerHTML = data.winner ? 
                `Winner: ${data.winner}` : 
                'No winner - reserve not met';
            
            const statusDiv = document.querySelector('.card-body .mb-3:nth-child(2)');
            if (statusDiv) {
                statusDiv.appendChild(winnerInfo);
            }
            
            // Disable bid form
            const bidForm = document.querySelector('form[action*="place_bid"]');
            if (bidForm) {
                bidForm.style.display = 'none';
            }

            // Reload the page after 100ms
            setTimeout(() => {
                window.location.reload();
            }, 100);
        }
    });

    // Handle user notifications (for profile updates)
    socket.on('user_notification', function(data) {
        // Update notifications list if on profile page
        const notificationsList = document.getElementById('notifications-list');
        if (notificationsList) {
            const notificationItem = document.createElement('div');
            notificationItem.className = 'alert alert-info alert-dismissible fade show';
            notificationItem.innerHTML = `
                <strong>${data.title}</strong>
                <p>${data.message}</p>
                <a href="${data.link}" class="btn btn-sm btn-primary">View</a>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            notificationsList.insertBefore(notificationItem, notificationsList.firstChild);

            // Update unread count
            const unreadBadge = document.querySelector('.notifications-badge');
            if (unreadBadge) {
                const currentCount = parseInt(unreadBadge.textContent) + 1;
                unreadBadge.textContent = currentCount;
                unreadBadge.style.display = currentCount > 0 ? 'inline' : 'none';
            }
        }

        // Show notification popup
        showNotification(data.title, data.message, data.type || 'info', data.link);
    });
    
    // Helper function to show notifications
    function showNotification(title, message, type, link) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show`;
        notification.innerHTML = `
            <strong>${title}</strong>
            <p>${message}</p>
            <a href="${link}" class="btn btn-sm btn-primary">View</a>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.getElementById('global-notifications');
        if (container) {
            container.appendChild(notification);
            
            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => notification.remove(), 150);
            }, 5000);
        }
    }
    
    // Leave rooms when page is unloaded
    window.addEventListener('beforeunload', function() {
        if (auctionId) {
            socket.emit('leave_auction_room', { auction_id: auctionId });
        }
        if (userId) {
            socket.emit('leave_user_room', { user_id: userId });
        }
    });
}); 