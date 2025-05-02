// Test script for notifications
document.addEventListener('DOMContentLoaded', function() {
    // Only run in development environments with query param ?test-notifications=true
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('test-notifications') !== 'true') {
        return;
    }
    
    console.log('Notification test script loaded');
    
    // Add test buttons to page
    const testContainer = document.createElement('div');
    testContainer.className = 'card mt-3';
    testContainer.innerHTML = `
        <div class="card-header bg-warning">
            <h5>Socket Notification Testing <small>(Development Only)</small></h5>
        </div>
        <div class="card-body">
            <div class="mb-3">
                <button id="test-alert-match" class="btn btn-primary">Test Alert Match</button>
                <button id="test-question-answered" class="btn btn-success">Test Question Answered</button>
                <button id="test-outbid" class="btn btn-danger">Test Outbid</button>
            </div>
            <div class="mb-3">
                <h6>Socket Status: <span id="socket-status">Checking...</span></h6>
            </div>
        </div>
    `;
    
    // Add to body
    document.querySelector('.container').prepend(testContainer);
    
    // Set up socket status
    const socket = io();
    const socketStatus = document.getElementById('socket-status');
    
    socket.on('connect', function() {
        socketStatus.textContent = 'Connected';
        socketStatus.className = 'text-success';
    });
    
    socket.on('disconnect', function() {
        socketStatus.textContent = 'Disconnected';
        socketStatus.className = 'text-danger';
    });
    
    // Set up test buttons
    document.getElementById('test-alert-match').addEventListener('click', function() {
        // Simulate an alert match notification
        const notificationData = {
            title: 'Alert Match (Test)',
            message: 'Test notification - a new auction matches your alert criteria',
            type: 'alert_match',
            link: '/auction/browse'
        };
        
        // Manually trigger notification handler
        const notificationsArea = document.getElementById('global-notifications');
        if (notificationsArea) {
            const notificationDiv = document.createElement('div');
            notificationDiv.className = 'alert alert-info alert-dismissible fade show';
            notificationDiv.setAttribute('role', 'alert');
            
            notificationDiv.innerHTML = `
                <strong>${notificationData.title}</strong><br>
                ${notificationData.message}
                <a href="${notificationData.link}" class="alert-link ms-2">View</a>
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            
            notificationsArea.appendChild(notificationDiv);
        }
    });
    
    document.getElementById('test-question-answered').addEventListener('click', function() {
        // Simulate a question answered notification
        const notificationData = {
            title: 'Question Answered (Test)',
            message: 'Test notification - your question has been answered',
            type: 'question_answered',
            link: '/auction/browse'
        };
        
        // Manually trigger notification handler
        const notificationsArea = document.getElementById('global-notifications');
        if (notificationsArea) {
            const notificationDiv = document.createElement('div');
            notificationDiv.className = 'alert alert-success alert-dismissible fade show';
            notificationDiv.setAttribute('role', 'alert');
            
            notificationDiv.innerHTML = `
                <strong>${notificationData.title}</strong><br>
                ${notificationData.message}
                <a href="${notificationData.link}" class="alert-link ms-2">View</a>
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            
            notificationsArea.appendChild(notificationDiv);
        }
    });
    
    document.getElementById('test-outbid').addEventListener('click', function() {
        // Simulate an outbid notification
        const notificationData = {
            title: 'You Have Been Outbid (Test)',
            message: 'Test notification - someone has outbid you on an auction',
            type: 'outbid',
            link: '/auction/browse'
        };
        
        // Manually trigger notification handler
        const notificationsArea = document.getElementById('global-notifications');
        if (notificationsArea) {
            const notificationDiv = document.createElement('div');
            notificationDiv.className = 'alert alert-warning alert-dismissible fade show';
            notificationDiv.setAttribute('role', 'alert');
            
            notificationDiv.innerHTML = `
                <strong>${notificationData.title}</strong><br>
                ${notificationData.message}
                <a href="${notificationData.link}" class="alert-link ms-2">View</a>
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            
            notificationsArea.appendChild(notificationDiv);
        }
    });
}); 