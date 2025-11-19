// Initialize Socket.IO connection
const socket = io();

let rooms = [];

// Load rooms on page load
document.addEventListener('DOMContentLoaded', function () {
    loadRooms();
});

// Socket.IO event listeners
socket.on('room_update', function (data) {
    loadRooms();
});

socket.on('supply_update', function (data) {
    loadRooms();
});

// Load all rooms from server
async function loadRooms() {
    try {
        const response = await fetch('/api/rooms');
        rooms = await response.json();
        renderRooms();
    } catch (error) {
        console.error('Error loading rooms:', error);
    }
}

// Render rooms in the grid
function renderRooms() {
    const grid = document.getElementById('roomsGrid');

    if (rooms.length === 0) {
        grid.innerHTML = '<div class="no-rooms">No rooms created yet. Click "Add New Room" to get started!</div>';
        return;
    }

    grid.innerHTML = rooms.map(room => {
        const status = getRoomStatus(room);
        const supplies = room.supplies || getDefaultSupplies();

        return `
            <div class="room-card status-${status}">
                <div class="room-header">
                    <div class="room-info">
                        <h3>${room.name}</h3>
                        <div class="room-id">ID: ${room.id}</div>
                        <div class="room-meta">${room.type} • ${room.location || 'No location'}</div>
                    </div>
                    <div class="room-actions">
                        <button class="btn-icon" onclick="editRoom('${room.id}')" title="Edit Room">
                            <span class="material-symbols-outlined">settings</span>
                        </button>
                    </div>
                </div>
                
                <div class="supplies">
                    ${Object.entries(supplies).map(([key, supply]) => `
                        <div class="supply-item">
                            <span class="supply-name">
                                <span class="material-symbols-outlined">${getSupplyIcon(key)}</span>
                                <span>${supply.name}</span>
                            </span>
                            <div class="supply-actions">
                                <span class="supply-status status-${supply.status}">${supply.status.toUpperCase()}</span>
                                ${supply.status === 'empty' ?
                `<button class="btn-resolve" onclick="resolveSupply('${room.id}', '${key}')">
                    <span class="material-symbols-outlined">check_circle</span>
                    Mark Full
                </button>`
                : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }).join('');
}

// Get room overall status based on supplies
function getRoomStatus(room) {
    const supplies = room.supplies || getDefaultSupplies();
    const statuses = Object.values(supplies).map(s => s.status);

    if (statuses.includes('empty')) return 'alert';
    if (statuses.includes('low')) return 'warning';
    return 'ok';
}

// Get default supplies for a new room
function getDefaultSupplies() {
    return {
        toilet_paper: { name: 'Toilet Paper', status: 'full' },
        soap: { name: 'Soap', status: 'full' },
        towel: { name: 'Paper Towel', status: 'full' },
        trash: { name: 'Trash Bin', status: 'full' }
    };
}

// Get icon for supply type
function getSupplyIcon(type) {
    const icons = {
        toilet_paper: 'laps',
        soap: 'soap',
        towel: 'dry',
        trash: 'delete'
    };
    return icons[type] || 'inventory_2';
}

// Modal functions
function showAddRoomModal() {
    document.getElementById('addRoomModal').style.display = 'block';
}

function closeAddRoomModal() {
    document.getElementById('addRoomModal').style.display = 'none';
    document.getElementById('addRoomForm').reset();
}

function closeEditRoomModal() {
    document.getElementById('editRoomModal').style.display = 'none';
    document.getElementById('editRoomForm').reset();
}

// Close modal when clicking outside
window.onclick = function (event) {
    const addModal = document.getElementById('addRoomModal');
    const editModal = document.getElementById('editRoomModal');
    if (event.target == addModal) {
        closeAddRoomModal();
    }
    if (event.target == editModal) {
        closeEditRoomModal();
    }
}

// Add new room
document.getElementById('addRoomForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const roomData = {
        name: document.getElementById('roomName').value,
        type: document.getElementById('roomType').value,
        location: document.getElementById('roomLocation').value,
        supplies: getDefaultSupplies()
    };

    try {
        const response = await fetch('/api/rooms', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(roomData)
        });

        if (response.ok) {
            closeAddRoomModal();
            loadRooms();
        } else {
            alert('Error creating room');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error creating room');
    }
});

// Edit room
function editRoom(roomId) {
    const room = rooms.find(r => r.id === roomId);
    if (!room) return;

    document.getElementById('editRoomId').value = room.id;
    document.getElementById('editRoomName').value = room.name;
    document.getElementById('editRoomType').value = room.type;
    document.getElementById('editRoomLocation').value = room.location || '';
    document.getElementById('editRoomIdDisplay').value = room.id;

    document.getElementById('editRoomModal').style.display = 'block';
}

// Update room
document.getElementById('editRoomForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const roomId = document.getElementById('editRoomId').value;
    const roomData = {
        name: document.getElementById('editRoomName').value,
        type: document.getElementById('editRoomType').value,
        location: document.getElementById('editRoomLocation').value
    };

    try {
        const response = await fetch(`/api/rooms/${roomId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(roomData)
        });

        if (response.ok) {
            closeEditRoomModal();
            loadRooms();
        } else {
            alert('Error updating room');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error updating room');
    }
});

// Delete room
async function deleteRoom() {
    const roomId = document.getElementById('editRoomId').value;

    if (!confirm('Are you sure you want to delete this room? This action cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch(`/api/rooms/${roomId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            closeEditRoomModal();
            loadRooms();
        } else {
            alert('Error deleting room');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error deleting room');
    }
}

// Resolve supply (mark as full)
async function resolveSupply(roomId, supplyKey) {
    try {
        const response = await fetch(`/api/rooms/${roomId}/supply/${supplyKey}/resolve`, {
            method: 'POST'
        });

        if (response.ok) {
            loadRooms();
        } else {
            alert('Error resolving supply');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error resolving supply');
    }
}
