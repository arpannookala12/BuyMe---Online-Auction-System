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