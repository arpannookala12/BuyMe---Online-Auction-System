document.addEventListener('DOMContentLoaded', function() {
    const socket = io();
    
    // Get user ID from data attribute
    const userId = document.body.dataset.userId;
    
    // Set up notification listeners
    setupNotificationListeners(socket);
    
    // Join user's personal room for notifications
    if (userId) {
        socket.emit('join_user_room', { user_id: userId });
        console.log('Joined user room:', userId);
    }
    
    // Join auction room if on auction page
    const auctionId = document.querySelector('[data-auction-id]')?.dataset.auctionId;
    if (auctionId) {
        socket.emit('join_auction', { auction_id: auctionId });
    }
    
    // Handle new question event
    socket.on('new_question', function(data) {
        // If on auction page, update questions section
        const questionsContainer = document.querySelector('.questions-container');
        if (questionsContainer) {
            // Reload questions section
            fetch(`/auction/${data.auction_id}/questions`)
                .then(response => response.text())
                .then(html => {
                    questionsContainer.innerHTML = html;
                });
        }
        
        // Show notification for customer reps
        if (document.body.dataset.isCustomerRep === 'true') {
            showNotification('New Question', 
                `New question from ${data.user_username} on auction "${data.auction_title}"`,
                'info',
                `/auction/${data.auction_id}`
            );
        }
    });
    
    // Handle new answer event
    socket.on('new_answer', function(data) {
        const questionId = data.question_id;
        const questionItem = document.querySelector(`.question-item[data-question-id="${questionId}"]`);
        
        if (questionItem) {
            // Update question status badge
            const statusBadge = questionItem.querySelector('.badge');
            statusBadge.className = 'badge bg-success';
            statusBadge.textContent = 'Answered';
            
            // Add answer to the answers list
            const answersList = questionItem.querySelector('.answers-list') || document.createElement('div');
            if (!answersList.classList.contains('answers-list')) {
                answersList.className = 'answers-list ms-4';
                questionItem.appendChild(answersList);
            }
            
            const answerItem = document.createElement('div');
            answerItem.className = 'answer-item mb-2 p-2 bg-light rounded';
            answerItem.innerHTML = `
                <div class="answer-header d-flex justify-content-between align-items-center mb-1">
                    <span class="fw-bold">
                        ${data.answer_username}
                        <span class="badge bg-info">Customer Rep</span>
                    </span>
                    <span class="text-muted">${new Date(data.answer_timestamp).toLocaleString()}</span>
                </div>
                <div class="answer-text">${data.answer_text}</div>
            `;
            
            answersList.appendChild(answerItem);
            
            // Remove answer form if it exists
            const answerForm = questionItem.querySelector('.answer-form');
            if (answerForm) {
                answerForm.remove();
            }
            
            // Show notification if this is the user's question
            if (data.question_user_id === userId) {
                showNotification({
                    title: 'Question Answered',
                    message: `Your question has been answered on auction: "${data.auction_title}"`,
                    type: 'question_answered',
                    link: `/auction/${data.auction_id}`
                });
            }
        }
    });
    
    // Handle question answered notification
    socket.on('question_answered', function(data) {
        showNotification('Question Answered', 
            `Your question has been answered on auction "${data.auction_title}"`,
            'info',
            `/auction/${data.auction_id}`
        );
    });
    
    // Handle new question notification
    socket.on('new_question', function(data) {
        showNotification('New Question', 
            `A new question has been posted on auction "${data.auction_title}"`,
            'info',
            `/auction/${data.auction_id}`
        );
    });
    
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
    socket.on('outbid_notification', function(data) {
        showNotification('You Have Been Outbid', 
            `You have been outbid on auction "${data.auction_title}". New bid: $${data.new_highest_bid.toFixed(2)}`,
            'warning',
            `/auction/${data.auction_id}`
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
        console.log('Received user_notification:', data);
        showNotification(data.title, data.message, data.type || 'info', data.link);
    });
    
    // Helper function to show notifications
    function showNotification(title, message, type = 'info', link = null) {
        console.log('Showing notification:', title, message);
        const notificationsArea = document.getElementById('global-notifications');
        if (!notificationsArea) {
            console.error('Notifications area not found');
            return;
        }
        
        const notificationDiv = document.createElement('div');
        notificationDiv.className = `alert alert-${type} alert-dismissible fade show`;
        notificationDiv.setAttribute('role', 'alert');
        notificationDiv.style.boxShadow = '0 4px 8px rgba(0,0,0,0.2)';
        notificationDiv.style.animation = 'pulse 2s';
        
        const iconClass = {
            'success': 'bi-check-circle-fill',
            'danger': 'bi-exclamation-triangle-fill',
            'warning': 'bi-exclamation-circle-fill',
            'info': 'bi-info-circle-fill'
        }[type] || 'bi-bell-fill';
        
        let content = `
            <div class="d-flex align-items-center">
                <div class="me-3">
                    <i class="bi ${iconClass} fs-3 text-${type}"></i>
                </div>
                <div>
                    <strong>${title}</strong><br>
                    ${message}
                </div>
            </div>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        notificationDiv.innerHTML = content;
        
        // Add click handler for the notification if a link is provided
        if (link) {
            notificationDiv.classList.add('cursor-pointer');
            notificationDiv.addEventListener('click', function(event) {
                // Don't navigate if clicking the close button
                if (!event.target.classList.contains('btn-close') && !event.target.closest('.btn-close')) {
                    window.location.href = link;
                }
            });
        }
        
        // Add to DOM
        notificationsArea.prepend(notificationDiv);
        
        // Auto-remove after 8 seconds
        setTimeout(function() {
            if (notificationDiv.parentElement) {
                notificationDiv.remove();
            }
        }, 8000);
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

    // Handle new questions
    socket.on('new_question', function(data) {
        const questionsList = document.getElementById('questions-list');
        if (questionsList) {
            const questionItem = document.createElement('div');
            questionItem.className = 'question-item mb-3';
            questionItem.dataset.questionId = data.question_id;
            questionItem.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <p class="mb-1">${data.question_text}</p>
                        <small class="text-muted">
                            Asked by ${data.user_username} on ${new Date(data.timestamp).toLocaleString()}
                        </small>
                    </div>
                    <span class="badge bg-warning">Unanswered</span>
                </div>
            `;
            questionsList.appendChild(questionItem);
        }
    });

    // Handle new answers
    socket.on('new_answer', function(data) {
        const questionItem = document.querySelector(`.question-item[data-question-id="${data.question_id}"]`);
        if (questionItem) {
            // Update status badge
            const statusBadge = questionItem.querySelector('.badge');
            statusBadge.className = 'badge bg-success';
            statusBadge.textContent = 'Answered';
            
            // Add answer to answers list
            let answersList = questionItem.querySelector('.answers-list');
            if (!answersList) {
                answersList = document.createElement('div');
                answersList.className = 'answers-list ms-4 mt-2';
                questionItem.appendChild(answersList);
            }
            
            const answerItem = document.createElement('div');
            answerItem.className = 'answer-item mb-2 p-2 bg-light rounded';
            answerItem.innerHTML = `
                <div class="answer-header d-flex justify-content-between align-items-center mb-1">
                    <span class="fw-bold">
                        ${data.answer_username}
                        <span class="badge bg-info">Customer Rep</span>
                    </span>
                    <span class="text-muted">${new Date(data.answer_timestamp).toLocaleString()}</span>
                </div>
                <div class="answer-text">${data.answer_text}</div>
            `;
            answersList.appendChild(answerItem);
        }
    });

    // Handle question form submission
    const askQuestionForm = document.getElementById('ask-question-form');
    if (askQuestionForm) {
        askQuestionForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const questionText = document.getElementById('question-text').value;
            const auctionId = document.querySelector('[data-auction-id]').dataset.auctionId;
            
            fetch(`/auction/${auctionId}/question`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: questionText
                }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Clear the form
                    askQuestionForm.reset();
                }
            });
        });
    }

    function setupNotificationListeners(socket) {
        // Listen for general notifications
        socket.on('notification', function(data) {
            showGenericNotification(data);
        });
        
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

    // Function to show a generic notification
    function showGenericNotification(data) {
        const notificationsArea = document.getElementById('global-notifications');
        if (notificationsArea) {
            const notificationDiv = document.createElement('div');
            notificationDiv.className = 'alert alert-info alert-dismissible fade show';
            notificationDiv.setAttribute('role', 'alert');
            
            notificationDiv.innerHTML = `
                <strong>${data.title}</strong><br>
                ${data.message}
                <a href="${data.link}" class="alert-link ms-2">View</a>
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            
            notificationsArea.appendChild(notificationDiv);
            
            // Auto-remove after 8 seconds
            setTimeout(function() {
                if (notificationDiv.parentElement) {
                    notificationDiv.remove();
                }
            }, 8000);
        }
    }

    // Listen for new auction notifications matching alerts
    socket.on('new_auction_alert', function(data) {
        showNewAuctionNotification(data);
    });
    
    // Function to show a notification for new auctions matching alerts
    function showNewAuctionNotification(data) {
        const notificationsArea = document.getElementById('global-notifications');
        if (notificationsArea) {
            const notificationDiv = document.createElement('div');
            notificationDiv.className = 'alert alert-success alert-dismissible fade show';
            notificationDiv.setAttribute('role', 'alert');
            notificationDiv.style.boxShadow = '0 4px 8px rgba(0,0,0,0.2)';
            notificationDiv.style.animation = 'pulse 2s';
            
            notificationDiv.innerHTML = `
                <div class="d-flex align-items-center">
                    <div class="me-3">
                        <i class="bi bi-bell-fill fs-3 text-primary"></i>
                    </div>
                    <div>
                        <strong>Alert Match: New Auction!</strong><br>
                        ${data.message}<br>
                        <a href="/auction/${data.auction_id}" class="btn btn-sm btn-primary mt-2">View Auction</a>
                    </div>
                </div>
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            
            notificationsArea.appendChild(notificationDiv);
            
            // Keep this alert visible longer (15 seconds)
            setTimeout(function() {
                if (notificationDiv.parentElement) {
                    notificationDiv.remove();
                }
            }, 15000);
        }
    }
    
    // Function to show a notification for outbid events
    function showOutbidNotification(data) {
        const notificationsArea = document.getElementById('global-notifications');
        if (notificationsArea) {
            const notificationDiv = document.createElement('div');
            notificationDiv.className = 'alert alert-warning alert-dismissible fade show';
            notificationDiv.setAttribute('role', 'alert');
            notificationDiv.style.boxShadow = '0 4px 8px rgba(0,0,0,0.2)';
            notificationDiv.style.animation = 'pulse 2s';
            
            notificationDiv.innerHTML = `
                <div class="d-flex align-items-center">
                    <div class="me-3">
                        <i class="bi bi-exclamation-triangle-fill fs-3 text-warning"></i>
                    </div>
                    <div>
                        <strong>You Have Been Outbid!</strong><br>
                        Your bid of $${data.your_bid.toFixed(2)} on "${data.auction_title}" has been outbid.<br>
                        New highest bid: $${data.new_highest_bid.toFixed(2)}<br>
                        <a href="/auction/${data.auction_id}" class="btn btn-sm btn-warning mt-2">Bid Again</a>
                    </div>
                </div>
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            
            notificationsArea.appendChild(notificationDiv);
            
            // Keep this alert visible longer (15 seconds)
            setTimeout(function() {
                if (notificationDiv.parentElement) {
                    notificationDiv.remove();
                }
            }, 15000);
        }
    }
}); 