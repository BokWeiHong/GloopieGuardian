let map;
let cy;
let apMarkers = [];
let currentLocationMarker = null;

let allAPsData = [];
let currentLat = null;
let currentLon = null;
let maxRadarRange = 10; 
let hoveredAP = null;    
let renderedPoints = []; 

const canvas = document.getElementById('radarCanvas');
const ctx = canvas.getContext('2d');
const size = 450;
canvas.width = size;
canvas.height = size;
const centerX = size / 2;
const centerY = size / 2;
const radius = size / 2 - 20;

function getDistanceMeters(lat1, lon1, lat2, lon2) {
    const R = 6371e3; 
    const φ1 = lat1 * Math.PI / 180;
    const φ2 = lat2 * Math.PI / 180;
    const Δφ = (lat2 - lat1) * Math.PI / 180;
    const Δλ = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
              Math.cos(φ1) * Math.cos(φ2) *
              Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

function getBearing(startLat, startLon, destLat, destLon) {
    const startLatRad = startLat * Math.PI / 180;
    const startLonRad = startLon * Math.PI / 180;
    const destLatRad = destLat * Math.PI / 180;
    const destLonRad = destLon * Math.PI / 180;
    const y = Math.sin(destLonRad - startLonRad) * Math.cos(destLatRad);
    const x = Math.cos(startLatRad) * Math.sin(destLatRad) -
             Math.sin(startLatRad) * Math.cos(destLatRad) * Math.cos(destLonRad - startLonRad);
    return Math.atan2(y, x);
}

function drawRadarScope() {
    ctx.clearRect(0, 0, size, size);
    ctx.fillStyle = '#ffffff'; 
    ctx.fillRect(0, 0, size, size);
    renderedPoints = [];

    ctx.strokeStyle = 'rgba(0, 0, 0, 0.4)'; 
    ctx.lineWidth = 1.5;
    
    for (let i = 1; i <= 5; i++) {
        ctx.beginPath();
        ctx.arc(centerX, centerY, (radius / 5) * i, 0, Math.PI * 2);
        ctx.stroke();

        ctx.fillStyle = '#666';
        ctx.font = '10px monospace';
        const distLabel = Math.round((maxRadarRange / 5) * i) + "m";
        ctx.fillText(distLabel, centerX + 5, centerY - (radius / 5) * i + 10);
    }

    ctx.beginPath();
    ctx.moveTo(centerX, centerY - radius); ctx.lineTo(centerX, centerY + radius);
    ctx.moveTo(centerX - radius, centerY); ctx.lineTo(centerX + radius, centerY);
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(centerX, centerY, 6, 0, Math.PI * 2);
    ctx.fillStyle = '#0000ff'; 
    ctx.fill();

    if (currentLat !== null && currentLon !== null) {
        allAPsData.forEach(ap => {
            const dist = getDistanceMeters(currentLat, currentLon, ap.lat, ap.lon);
            const angle = getBearing(currentLat, currentLon, ap.lat, ap.lon);
            if (dist > maxRadarRange) return;
            const pixelDist = (dist / maxRadarRange) * radius;
            const x = centerX + Math.sin(angle) * pixelDist;
            const y = centerY - Math.cos(angle) * pixelDist;
            renderedPoints.push({ x, y, data: ap });
            ctx.beginPath();
            ctx.arc(x, y, 5, 0, Math.PI * 2);
            ctx.fillStyle = (hoveredAP && hoveredAP === ap) ? '#ff9900' : '#ff0000'; 
            ctx.fill();
            
        });
    }
    if (hoveredAP) {
        drawTooltip(hoveredAP);
    }
}

function drawTooltip(ap) {
    const point = renderedPoints.find(p => p.data === ap);
    if (!point) return;

    const x = point.x;
    const y = point.y;

    const truncate = (str, len) => str.length > len ? str.substring(0, len) + "..." : str;

    const text1 = truncate(ap.ssid || "Hidden SSID", 20);
    const text2 = (ap.strongest_signal || "?") + " dBm";
    const text3 = ap.devmac || "UNKNOWN MAC";

    ctx.font = "10px 'Press Start 2P', monospace"; 

    const width = Math.max(
        ctx.measureText(text1).width, 
        ctx.measureText(text2 + " " + text3).width
    ) + 20; 
    
    const lineHeight = 14;
    const height = (lineHeight * 3) + 15;
    const padding = 10;

    let tx = x + 15;
    let ty = y + 15;

    if (tx + width > size) {
        tx = x - width - 15;
    }

    if (tx < 5) {
        tx = 5;
    }

    if (tx + width > size) {
        tx = size - width - 5;
    }

    if (ty + height > size) {
        ty = y - height - 15;
    }

    if (ty < 5) {
        ty = 5;
    }

    ctx.save();

    ctx.shadowColor = "rgba(0, 0, 0, 0.3)";
    ctx.shadowBlur = 0;
    ctx.shadowOffsetX = 4;
    ctx.shadowOffsetY = 4;

    ctx.fillStyle = "#ffffff";
    ctx.fillRect(tx, ty, width, height);

    ctx.shadowColor = "transparent";
    ctx.strokeStyle = "#000000";
    ctx.lineWidth = 3;
    ctx.strokeRect(tx, ty, width, height);

    ctx.fillStyle = "#000000";
    ctx.textBaseline = "top";
    
    ctx.fillText(text1, tx + padding, ty + padding);
    
    ctx.fillStyle = "#009900"; 
    ctx.fillText(text2, tx + padding, ty + padding + lineHeight);

    ctx.fillStyle = "#666666"; 
    ctx.fillText(text3, tx + padding, ty + padding + (lineHeight * 2));

    ctx.restore();
}

document.getElementById('rangeSelector').addEventListener('change', (e) => {
    maxRadarRange = parseInt(e.target.value);
    drawRadarScope();
    updateRadarTable();
});

canvas.addEventListener('mousemove', (e) => {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const mouseX = (e.clientX - rect.left) * scaleX;
    const mouseY = (e.clientY - rect.top) * scaleY;
    let found = null;

    for (const p of renderedPoints) {
        const dx = mouseX - p.x;
        const dy = mouseY - p.y;
        const distance = Math.sqrt(dx*dx + dy*dy);
        
        if (distance < 8) {
            found = p.data;
            break;
        }
    }

    if (found !== hoveredAP) {
        hoveredAP = found;
        canvas.style.cursor = found ? 'pointer' : 'default';
        drawRadarScope();

        if (cy && found) {
            cy.elements().unselect();
            cy.nodes(`[mac = "${found.devmac}"]`).select();
        }
    }
});

function updateRadarTable() {
    const tbody = document.querySelector('#radarTable tbody');
    tbody.innerHTML = '';

    if (!currentLat || !currentLon) return;

    const sortedAPs = allAPsData.map(ap => {
        const dist = getDistanceMeters(currentLat, currentLon, ap.lat, ap.lon);
        return { ...ap, distance: dist };
    }).sort((a, b) => a.distance - b.distance);

    sortedAPs.forEach(ap => {
        if (ap.distance > maxRadarRange) return;

        const tr = document.createElement('tr');

        const sig = parseInt(ap.strongest_signal);
        let sigClass = 'sig-low';
        if (sig > -60) sigClass = 'sig-high';
        else if (sig > -80) sigClass = 'sig-med';

        tr.innerHTML = `
            <td>
                ${ap.ssid || '<span style="color:#999">HIDDEN</span>'}
            </td>
            <td>${ap.devmac || '-'}</td>
            <td class="${sigClass}">${ap.strongest_signal}</td>
            <td><strong>${ap.distance.toFixed(1)}m</strong></td>
        `;

        tr.addEventListener('click', () => {
            if (cy) {
                const node = cy.nodes(`[mac = "${ap.devmac}"]`);
                if (node.length) {
                    cy.animate({
                        center: {success: node},
                        zoom: 2,
                        duration: 500
                    });
                }
            }
        });

        tr.addEventListener('mouseenter', () => {
            hoveredAP = ap;
            drawRadarScope();
        });
        tr.addEventListener('mouseleave', () => {
            hoveredAP = null;
            drawRadarScope();
        });

        tbody.appendChild(tr);
    });
}

async function loadScanOptions() {
    try {
        const res = await fetch('/api/scans/');
        const scans = await res.json();
        console.log("Fetched scans:", scans);
        const selector = document.getElementById('scanSelector');
        selector.innerHTML = '';
        scans.forEach(scan => {
            const option = document.createElement('option');
            option.value = scan.id;
            option.textContent = `#${scan.id} ${scan.name}`;
            selector.appendChild(option);
        });
        updateSelectedText();
    } catch (err) {
        console.error("Failed to load scans:", err);
    }
}

function updateSelectedText() {
    const selector = document.getElementById('scanSelector');
    const selected = Array.from(selector.selectedOptions).map(opt => opt.value);
    const textInput = document.getElementById('selectedScans');
    textInput.value = selected.length
        ? `Selected: [${selected.join(', ')}]`
        : 'No scans selected...';
}

document.getElementById('scanSelector').addEventListener('change', updateSelectedText);
document.getElementById('selectAll').addEventListener('change', function () {
    const selector = document.getElementById('scanSelector');
    const allOptions = Array.from(selector.options);
    allOptions.forEach(opt => opt.selected = this.checked);
    updateSelectedText();
});

document.getElementById('applyFilters').addEventListener('click', () => {
    const selected = Array.from(document.getElementById('scanSelector').selectedOptions)
        .map(opt => opt.value);
    console.log("Selected scan IDs:", selected);
    refreshDashboard(selected);
});

async function refreshDashboard(scanIds = []) {
    await Promise.all([
        loadAPs(scanIds),
        drawClientGraph(scanIds),
    ]);
}

async function initializeMap() {
    let initialLat = 3.1390;
    let initialLon = 101.6869;
    let hasFix = false;
    try {
        const res = await fetch('/map/api/monitoring-path/');
        const data = await res.json();
        if (data.success && data.lat && data.lon) {
            initialLat = data.lat;
            initialLon = data.lon;
            
            // UPDATE GLOBALS FOR RADAR
            currentLat = initialLat;
            currentLon = initialLon;
            hasFix = true;
            console.log(`Initializing map at GPS location: ${initialLat}, ${initialLon}`);
        } else {
            console.warn("No GPS fix, using default location");
        }
    } catch (err) {
        console.error("Error fetching GPS location, using default:", err);
    }
    map = L.map('map').setView([initialLat, initialLon], 17);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxNativeZoom: 19,
        maxZoom: 25,
        zoomSnap: 0.1,
        attribution: '© OpenStreetMap'
    }).addTo(map);
    if (hasFix) {
        addCurrentLocationMarker(initialLat, initialLon);
    } else {
        updateGPSDisplay(null, null, false);
    }

    drawRadarScope();
}

function addCurrentLocationMarker(lat, lon, data = {}) {
    if (!map) return;
    if (currentLocationMarker) map.removeLayer(currentLocationMarker);
    const locationIcon = L.divIcon({
        className: 'current-location-marker',
        html: `<div style="width:16px; height:16px; background:blue; border:2px solid white; border-radius:50%; box-shadow:0 0 5px rgba(0,0,0,0.5);"></div>`,
        iconSize: [20, 20],
        iconAnchor: [10, 10]
    });
    currentLocationMarker = L.marker([lat, lon], { icon: locationIcon }).addTo(map);
    currentLocationMarker.bindPopup(`
        <b>Your Current Location</b><br><br>
        Lat: ${lat.toFixed(6)}<br>
        Lon: ${lon.toFixed(6)}
        ${data.alt ? `<br>Alt: ${data.alt.toFixed(1)}m` : ''}
        ${data.satellites ? `<br>Sats: ${data.satellites}` : ''}
    `).openPopup();
    updateGPSDisplay(lat, lon, true);

    currentLat = lat;
    currentLon = lon;
    drawRadarScope();
}

function updateGPSDisplay(lat, lon, hasFix = true) {
    const latEl = document.getElementById('gpsLat');
    const lonEl = document.getElementById('gpsLon');
    if (!latEl || !lonEl) return;
    if (hasFix) {
        latEl.textContent = `Lat: ${lat.toFixed(6)}`;
        latEl.style.color = '#28a745';
        lonEl.textContent = `Lon: ${lon.toFixed(6)}`;
        lonEl.style.color = '#28a745';
    } else {
        latEl.textContent = 'Lat: No fix';
        latEl.style.color = '#dc3545';
        lonEl.textContent = 'Lon: No fix';
        lonEl.style.color = '#dc3545';
    }
}

function clearMapMarkers() {
    apMarkers.forEach(marker => map.removeLayer(marker));
    apMarkers = [];
}

async function loadAPs(scanIds = []) {
    try {
        clearMapMarkers();
        let url = 'api/aps/';
        if (scanIds.length > 0) url += '?scan_id=' + scanIds.join(',');
        const res = await fetch(url);
        const aps = await res.json();

        allAPsData = aps;

        aps.forEach(ap => {
            const icon = L.divIcon({
                className: 'custom-marker',
                html: `<div style="width:10px; height:10px; background:red; border:1px solid black; border-radius:50%;"></div>`,
                iconSize: [12, 12]
            });
            const marker = L.marker([ap.lat, ap.lon], { icon }).addTo(map);
            marker.bindPopup(`
                <b>${ap.ssid || '(No SSID)'}</b><br><br>
                MAC: ${ap.devmac || '-'}<br>
                Signal: ${ap.strongest_signal || '-'} dBm<br>
                Lat: ${ap.lat || '-'}<br>
                Lon: ${ap.lon || '-'}
            `);
            apMarkers.push(marker);
        });

        drawRadarScope();
        updateRadarTable();

        // Auto-select first AP in radar and highlight it
        if (aps.length > 0) {
            hoveredAP = aps[0];
            drawRadarScope();
        }
    } catch (err) {
        console.error("Error loading APs:", err);
    }
}

let allGraphData = {
    nodes: [],
    edges: [],
    aps: []
};

function populateAPSelector(aps) {
    const selector = document.getElementById('apSelector');
    selector.innerHTML = '<option value="">-- Select an AP --</option>';
    
    aps.forEach((ap, index) => {
        const option = document.createElement('option');
        option.value = ap.data.id;
        option.textContent = ap.data.label || ap.data.mac;
        selector.appendChild(option);
    });

    // Set first AP as default
    if (aps.length > 0) {
        selector.value = aps[0].data.id;
        renderAPGraph(aps[0].data.id);
    }
}

function populateAssociationTable(selectedAPId = null) {
    const tableBody = document.getElementById('associationTable').querySelector('tbody');
    tableBody.innerHTML = '';

    if (!selectedAPId) {
        // Show all associations
        allGraphData.edges.forEach(edge => {
            const apNode = allGraphData.aps.find(n => n.data.id === edge.data.target);
            const clientNode = allGraphData.nodes.find(n => n.data.id === edge.data.source && n.data.type === 'CLIENT');
            
            if (apNode && clientNode) {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${apNode.data.label || apNode.data.mac}</td>
                    <td>${clientNode.data.label || clientNode.data.mac}</td>
                    <td>${edge.data.type}</td>
                `;
                tableBody.appendChild(tr);
            }
        });
    } else {
        // Show only for selected AP
        const connectedEdges = allGraphData.edges.filter(edge => edge.data.target === selectedAPId);
        const apNode = allGraphData.aps.find(n => n.data.id === selectedAPId);
        
        connectedEdges.forEach(edge => {
            const clientNode = allGraphData.nodes.find(n => n.data.id === edge.data.source && n.data.type === 'CLIENT');
            
            if (clientNode) {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${apNode.data.label || apNode.data.mac}</td>
                    <td>${clientNode.data.label || clientNode.data.mac}</td>
                    <td>${edge.data.type}</td>
                `;
                tableBody.appendChild(tr);
            }
        });
    }
}

function renderAPGraph(selectedAPId = null) {
    const cyContainer = document.getElementById('cy');
    
    if (!cyContainer || !cyContainer.cytoscapeInstance) {
        console.error("Cytoscape instance not found!");
        return;
    }

    const cy = cyContainer.cytoscapeInstance;
    cy.elements().remove();

    const containerWidth = 600;
    const containerHeight = 600;
    const centerX = containerWidth / 2;
    const centerY = containerHeight / 2;

    let nodesToRender = [];
    let edgesToRender = [];

    if (selectedAPId) {
        const ap = allGraphData.aps.find(node => node.data.id === selectedAPId);
        if (!ap) return;

        nodesToRender.push(ap);

        const connectedEdges = allGraphData.edges.filter(edge => edge.data.target === selectedAPId);
        edgesToRender = connectedEdges;

        connectedEdges.forEach(edge => {
            const client = allGraphData.nodes.find(node => node.data.id === edge.data.source);
            if (client) {
                nodesToRender.push(client);
            }
        });
    } else {
        nodesToRender = allGraphData.nodes;
        edgesToRender = allGraphData.edges;
    }

    const positionedNodes = [];
    const nodeMap = new Map();

    nodesToRender.forEach(node => {
        nodeMap.set(node.data.id, node);
    });

    if (selectedAPId) {

        const ap = nodesToRender.find(n => n.data.type === "AP");
        if (ap) {
            positionedNodes.push({ ...ap, position: { x: centerX, y: centerY } });
        }

        const clients = nodesToRender.filter(n => n.data.type === "CLIENT");
        const radius = 150;
        clients.forEach((client, index) => {
            const angle = (index / Math.max(clients.length, 1)) * 2 * Math.PI;
            const x = centerX + radius * Math.cos(angle);
            const y = centerY + radius * Math.sin(angle);
            positionedNodes.push({ ...client, position: { x, y } });
        });
    } else {

        const aps = nodesToRender.filter(n => n.data.type === "AP");
        const cols = Math.ceil(Math.sqrt(aps.length));
        const spacing = 400;

        aps.forEach((ap, index) => {
            const row = Math.floor(index / cols);
            const col = index % cols;
            const x = centerX - (cols - 1) * spacing / 2 + col * spacing;
            const y = centerY - (Math.ceil(aps.length / cols) - 1) * spacing / 2 + row * spacing;
            positionedNodes.push({ ...ap, position: { x, y } });

            const apClients = nodesToRender.filter(n => 
                n.data.type === "CLIENT" && 
                edgesToRender.some(e => e.data.target === ap.data.id && e.data.source === n.data.id)
            );

            const clientRadius = 100;
            apClients.forEach((client, clientIndex) => {
                const angle = (clientIndex / Math.max(apClients.length, 1)) * 2 * Math.PI;
                const cx = x + clientRadius * Math.cos(angle);
                const cy = y + clientRadius * Math.sin(angle);
                positionedNodes.push({ ...client, position: { x: cx, y: cy } });
            });
        });
    }

    cy.add(positionedNodes);
    cy.add(edgesToRender);

    console.log(`Rendered ${positionedNodes.length} nodes and ${edgesToRender.length} edges`);

    cy.center();
    cy.zoom(1.5);

    // Update association table
    populateAssociationTable(selectedAPId);
}

async function drawClientGraph(scan_ids) {
    const cyContainer = document.getElementById('cy');
    
    if (!cyContainer) {
        console.error("Cytoscape container #cy not found!");
        return;
    }

    if (cyContainer.cytoscapeInstance) {
        cyContainer.cytoscapeInstance.destroy();
    }

    if (typeof cytoscape === 'undefined') {
        console.error("Cytoscape library not loaded!");
        return;
    }

    const cy = cytoscape({
        container: cyContainer,
        elements: [],
        style: [
            {
                selector: 'node[type="AP"]',
                style: {
                    'background-color': '#007bff',
                    'label': 'data(label)',
                    'color': '#000',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'width': 40,
                    'height': 40,
                    'font-size': 10
                }
            },
            {
                selector: 'node[type="CLIENT"]',
                style: {
                    'background-color': '#ff4d4d',
                    'shape': 'ellipse',
                    'label': 'data(label)',
                    'color': '#000',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'width': 30,
                    'height': 30,
                    'font-size': 9
                }
            },
            {
                selector: 'edge[type="Associated"]',
                style: {
                    'line-color': '#28a745',
                    'width': 3,
                    'curve-style': 'bezier',
                    'target-arrow-shape': 'triangle',
                    'target-arrow-color': '#28a745',
                }
            },
            {
                selector: 'edge[type="Observed"]',
                style: {
                    'line-color': '#ffc107',
                    'width': 1,
                    'line-style': 'dashed',
                    'curve-style': 'bezier',
                    'target-arrow-shape': 'triangle',
                    'target-arrow-color': '#ffc107',
                }
            }
        ],
        layout: { name: 'preset' }
    });

    console.log("Cytoscape instance created successfully");

    cyContainer.cytoscapeInstance = cy;

    try {
        const url = scan_ids.length > 0 
            ? `/map/api/client-graph/?scan_id=${scan_ids.join(',')}` 
            : `/map/api/client-graph/`;
        
        console.log("Fetching client graph from:", url);
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const jsonData = await response.json();

        if (!jsonData || jsonData.length === 0) {
            console.warn("No client data returned from API");
            populateAPSelector([]);
            return;
        }

        allGraphData.nodes = jsonData.filter(item => !item.data.source);
        allGraphData.edges = jsonData.filter(item => item.data.source);
        allGraphData.aps = allGraphData.nodes.filter(node => node.data.type === "AP");

        console.log(`Loaded ${allGraphData.aps.length} APs and ${allGraphData.nodes.length} total nodes`);

        populateAPSelector(allGraphData.aps);

    } catch (err) {
        console.error("Failed to load client graph:", err);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const apSelector = document.getElementById('apSelector');
    if (apSelector) {
        apSelector.addEventListener('change', (e) => {
            const selectedAPId = e.target.value;
            renderAPGraph(selectedAPId || null);
        });
    }
});

loadScanOptions();
initializeMap().then(() => {
    loadAPs();
    drawClientGraph([]);
});