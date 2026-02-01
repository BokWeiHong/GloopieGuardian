const chartColors = [
  "#3366CC", // blue
  "#DC3912", // red
  "#FF9900", // orange
  "#109618", // green
  "#990099", // purple
  "#3B3EAC", // indigo
  "#0099C6", // teal
  "#DD4477", // pink
  "#66AA00", // lime
  "#B82E2E", // dark red
  "#316395", // steel blue
  "#994499", // violet
  "#22AA99", // turquoise
  "#AAAA11", // olive
  "#6633CC"  // deep purple
];

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
loadScanOptions();

document.getElementById('applyFilters').addEventListener('click', () => {
    const selected = Array.from(document.getElementById('scanSelector').selectedOptions)
        .map(opt => opt.value);
    console.log("Selected scan IDs:", selected);
    refreshDashboard(selected);
});

async function refreshDashboard(scanIds = []) {
    await Promise.all([
        loadStats(scanIds),
        loadAvgSignalByManufacturer(10, scanIds),
        loadDeviceTypePie(scanIds),
        loadEncryptionPie(scanIds),
        loadChannelUsageChart(scanIds),
        loadSignalDistribution(scanIds),
        loadSignalStrengthCharts(scanIds),
        loadGeolocationMap(scanIds),
        loadTopManufacturersChart(scanIds)
    ]);
}


async function loadStats(scanIds = []) {
    try {
        const res = await fetch(`/api/devices/stats/?scan_id=${scanIds.join(',')}`);
        const data = await res.json();
        document.getElementById("total-scans").textContent = data.total_scans;
        document.getElementById("access-points").textContent = data.access_points;
        document.getElementById("connected-clients").textContent = data.connected_clients;
        document.getElementById("avg-signal").innerHTML = data.avg_signal + "<span>dBm</span>";
    } catch (err) {
        console.error("Failed to load stats:", err);
    }
}
loadStats();

async function loadAvgSignalByManufacturer(top = 10, scanIds = []) {
    try {
        const res = await fetch(`/api/devices/avg-signal-manufacturer/?top=${top}&scan_id=${scanIds.join(',')}`);
        const json = await res.json();
        const labels = json.map(item => item.manufacturer || "Unknown");
        const data = json.map(item => Math.round(item.avg_signal));
        const colors = labels.map((_, i) => chartColors[i % chartColors.length]);
        const ctx = document.getElementById('avgSignalManufacturerChart').getContext('2d');
        
        if (window.avgSignalChart) {
            window.avgSignalChart.destroy();
        }

        window.avgSignalChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Average Signal (dBm)',
                    data: data,
                    backgroundColor: colors,
                    borderColor: '#111',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false,
                        reverse: true,
                        title: {
                            display: true,
                            text: 'Signal Strength (dBm)',
                            font: {
                                family: '"Press Start 2P", system-ui, sans-serif',
                                size: 10
                            }
                        }
                    },
                    x: {
                        ticks: {
                            display: false,
                        }

                    }
                },
                plugins: {
                    legend: { 
                        display: false 
                    },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y} dBm`
                        },
                        backgroundColor: '#222',
                        borderColor: '#000',
                        borderWidth: 1,
                        titleFont: {
                            family: '"Press Start 2P", system-ui, sans-serif',
                            size: 10
                        },
                        bodyFont: {
                            family: '"Press Start 2P", system-ui, sans-serif',
                            size: 8
                        },
                        padding: 8
                    }
                }
            }
        });

        // ---- Fill Table ----
        const tbody = document.querySelector('#avgSignalManufacturerTable tbody');
        if (tbody) {
            tbody.innerHTML = "";
            json.forEach((entry) => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${entry.manufacturer || 'Unknown'}</td>
                    <td>${entry.ssid || 'N/A'}</td>
                    <td>${entry.avg_signal ? entry.avg_signal.toFixed(2) + ' dBm' : '—'}</td>
                `;
                tbody.appendChild(row);
            });
        }

    } catch (err) {
        console.error("Failed to load average signal by manufacturer:", err);
    }
}
loadAvgSignalByManufacturer(10);

async function loadDeviceTypePie(scanIds = []) {
    try {
        const res = await fetch(`/api/devices/by-type/?scan_id=${scanIds.join(',')}`);
        const json = await res.json();
        const labels = json.map(item => item.type || "Unknown");
        const data = json.map(item => item.count);

        const ctx = document.getElementById('deviceTypePieChart').getContext('2d');
        new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: data.map((_, i) => chartColors[i % chartColors.length]),
                    borderColor: '#000',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Devices by Type (APs vs Clients)',
                        color: 'black',
                        font: {
                            family: '"Press Start 2P", system-ui, -apple-system, sans-serif',
                            size: 12
                        }
                    },
                    legend: { 
                        display: true,
                        position: 'bottom',
                        labels: {
                            font: {
                                family: '"Press Start 2P", system-ui, -apple-system, sans-serif',
                                size: 8
                            }
                        }
                    },
                    tooltip: {
                        enabled: true,
                        borderColor: '#222',
                        borderWidth: 1,
                        titleFont: {
                            family: '"Press Start 2P", system-ui, -apple-system, sans-serif',
                            size: 10
                        },
                        bodyFont: {
                            family: '"Press Start 2P", system-ui, -apple-system, sans-serif',
                            size: 8
                        },
                        padding: 8
                    }
                }
            }
        });
    } catch (err) {
        console.error("Failed to load device type pie chart:", err);
    }
}
loadDeviceTypePie();


async function loadEncryptionPie(scanIds = []) {
    const res = await fetch(`/api/devices/encryption-types/?scan_id=${scanIds.join(',')}`);
    const json = await res.json();

    // Extract labels and data
    const labels = json.map(item => item.encryption || 'Unknown');
    const data = json.map(item => item.count);

    const ctx = document.getElementById('encryptionPieChart').getContext('2d');
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: data.map((_, i) => chartColors[i % chartColors.length]),
                borderColor: '#000',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Encryption Type Distribution',
                    color: 'black',
                    font: {
                        family: '"Press Start 2P", system-ui, -apple-system, sans-serif',
                        size: 12
                    }
                },
                legend: { 
                    display: true,
                    position: 'bottom',
                    labels: {
                        font: {
                            family: '"Press Start 2P", system-ui, -apple-system, sans-serif',
                            size: 8
                        }
                    }
                },
                tooltip: {
                    enabled: true,
                    borderColor: '#222',
                    borderWidth: 1,
                    titleFont: {
                        family: '"Press Start 2P", system-ui, -apple-system, sans-serif',
                        size: 10
                    },
                    bodyFont: {
                        family: '"Press Start 2P", system-ui, -apple-system, sans-serif',
                        size: 8
                    },
                    padding: 8
                }
            }
        }
    });
}
loadEncryptionPie();

async function loadChannelUsageChart(scanIds = []) {
    const res = await fetch(`/api/devices/channel-usage/?scan_id=${scanIds.join(',')}`);
    const json = await res.json();

    const labels = json.map(item => `CH ${item.channel}`);
    const data = json.map(item => item.count);

    const ctx = document.getElementById('channelUsageChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Devices',
                data: data,
                backgroundColor: data.map((_, i) => chartColors[i % chartColors.length]),
                borderColor: '#000',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Wi-Fi Channel',
                        color: 'black',
                        font: {
                            family: '"Press Start 2P", system-ui, -apple-system, sans-serif',
                            size: 10
                        }
                    },
                    ticks: {
                        color: 'black',
                        font: {
                            size: 8,
                            family: '"Press Start 2P", system-ui, -apple-system, sans-serif'
                        }
                    },
                    grid: {
                        color: '#eee'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Number of Devices',
                        color: 'black',
                        font: {
                            family: '"Press Start 2P", system-ui, -apple-system, sans-serif',
                            size: 10
                        }
                    },
                    ticks: {
                        color: 'black',
                        font: {
                            size: 8,
                            family: '"Press Start 2P", system-ui, -apple-system, sans-serif'
                        }
                    },
                    beginAtZero: true,
                    grid: {
                        color: '#eee'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Channel Usage Distribution',
                    color: 'black',
                    font: {
                        family: '"Press Start 2P", system-ui, -apple-system, sans-serif',
                        size: 12
                    }
                },
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: true,
                    borderColor: '#222',
                    borderWidth: 1,
                    titleFont: {
                        family: '"Press Start 2P", system-ui, -apple-system, sans-serif',
                        size: 10
                    },
                    bodyFont: {
                        family: '"Press Start 2P", system-ui, -apple-system, sans-serif',
                        size: 8
                    },
                    padding: 8
                }
            }
        }
    });
}
loadChannelUsageChart();

async function loadSignalDistribution(scanIds = []) {
    const res = await fetch(`/api/devices/signal-distribution/?scan_id=${scanIds.join(',')}`);
    const json = await res.json();
    const bins = json.map(d => d.bin);
    const counts = json.map(d => d.count);

    const ctx = document.getElementById('signalDistributionChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: bins.map(b => `${b} dBm`),
            datasets: [{
                label: 'Device Count',
                data: counts,
                backgroundColor: json.map((_, i) => chartColors[i % chartColors.length]),
                borderColor: '#000',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    color: 'black',
                    text: 'Signal Strength Distribution (5 dBm bins)',
                    font: {
                        family: '"Press Start 2P", system-ui, sans-serif',
                        size: 12
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        font: {
                            family: '"Press Start 2P", system-ui, sans-serif',
                            size: 8
                        },
                        maxRotation: 45,
                        minRotation: 0
                    },
                    title: {
                        display: true,
                        text: 'Signal Strength (dBm)',
                        font: {
                            family: '"Press Start 2P", system-ui, sans-serif',
                            size: 10
                        }
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Devices',
                        font: {
                            family: '"Press Start 2P", system-ui, sans-serif',
                            size: 10
                        }
                    },
                    ticks: {
                        font: {
                            family: '"Press Start 2P", system-ui, sans-serif',
                            size: 8
                        }
                    }
                }
            }
        }
    });
}
loadSignalDistribution();

async function loadSignalStrengthCharts(scanIds = []) {
    const res = await fetch(`/api/devices/signal-strength-distribution/?scan_id=${scanIds.join(',')}`);
    const json = await res.json();
    const labels = json.map(d => d.category);
    const values = json.map(d => d.count);

    const pieCtx = document.getElementById('signalPieChart').getContext('2d');
    new Chart(pieCtx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: json.map((_, i) => chartColors[i % chartColors.length]),
                borderColor: '#000',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        font: {
                            family: '"Press Start 2P", system-ui, sans-serif',
                            size: 8
                        }
                    }
                },
                title: {
                    display: true,
                    text: 'Signal Strength Distribution (Pie)',
                    color: 'black',
                    font: {
                        family: '"Press Start 2P", system-ui, sans-serif',
                        size: 12
                    }
                },
                tooltip: {
                    enabled: true,
                    borderColor: '#222',
                    borderWidth: 1,
                    titleFont: {
                        family: '"Press Start 2P", system-ui, -apple-system, sans-serif',
                        size: 10
                    },
                    bodyFont: {
                        family: '"Press Start 2P", system-ui, -apple-system, sans-serif',
                        size: 8
                    },
                    padding: 8
                }
            }
        }
    });
}
loadSignalStrengthCharts();

async function loadGeolocationMap(scanIds = []) {
    const res = await fetch(`/api/devices/geolocation/?scan_id=${scanIds.join(',')}`);
    const json = await res.json();
    const dataPoints = json.map(item => ({
        x: parseFloat(item.avg_lon),
        y: parseFloat(item.avg_lat),
        signal: item.strongest_signal,
        devkey: item.devkey
    }));

    const ctx = document.getElementById('geolocationChart').getContext('2d');
    new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Device Positions',
                data: dataPoints,
                backgroundColor: dataPoints.map(p => {
                    const s = p.signal;
                    if (s >= -40) return 'rgba(0, 200, 0, 0.8)';   
                    if (s >= -60) return 'rgba(255, 206, 86, 0.8)';
                    if (s >= -80) return 'rgba(255, 99, 132, 0.8)';
                    return 'rgba(150, 150, 150, 0.5)';             
                }),
                borderWidth: 1,
                borderColor: '#222',
                pointRadius: 6,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: 'Device Geolocation Map (Lat vs Lon)',
                    color: 'black',
                    font: {
                        family: '"Press Start 2P", system-ui, sans-serif',
                        size: 12
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0,0,0,0.7)',
                    titleFont: {
                        family: '"Press Start 2P", system-ui, sans-serif',
                        size: 10
                    },
                    bodyFont: {
                        family: '"Press Start 2P", system-ui, sans-serif',
                        size: 8
                    },
                    callbacks: {
                        title: () => null,
                        label: (ctx) => {
                            const d = ctx.raw;
                            return [
                                `DevKey: ${d.devkey}`,
                                `Lat: ${d.y.toFixed(5)}`,
                                `Lon: ${d.x.toFixed(5)}`,
                                `Signal: ${d.signal} dBm`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Longitude',
                        color: 'black',
                        font: {
                            family: '"Press Start 2P", system-ui, sans-serif',
                            size: 10
                        }
                    },
                    ticks: {
                        color: 'black',
                        font: {
                            size: 8,
                            family: '"Press Start 2P", system-ui, sans-serif'
                        }
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Latitude',
                        color: 'black',
                        font: {
                            family: '"Press Start 2P", system-ui, sans-serif',
                            size: 10
                        }
                    },
                    ticks: {
                        color: 'black',
                        font: {
                            size: 8,
                            family: '"Press Start 2P", system-ui, sans-serif'
                        }
                    }
                }
            }
        }
    });
}
loadGeolocationMap();

async function loadTopManufacturersChart(scanIds = []) {
    const res = await fetch(`/api/devices/top-manufacturers/?scan_id=${scanIds.join(',')}`);
    const json = await res.json();
    const ctx = document.getElementById('topManufacturersChart').getContext('2d');

    const datasets = json.map((item, i) => ({
        label: item.manufacturer || "Unknown",
        data: [item.count],
        backgroundColor: chartColors[i % chartColors.length],
        borderColor: '#000',
        borderWidth: 2
    }));

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Manufacturers'],
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Manufacturer',
                        color: 'black',
                        font: {
                            family: '"Press Start 2P", system-ui, -apple-system, sans-serif',
                            size: 10
                        }
                    },
                    ticks: {
                        display: false
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Devices',
                        color: 'black',
                        font: {
                            family: '"Press Start 2P", system-ui, -apple-system, sans-serif',
                            size: 10
                        }
                    },
                    ticks: {
                        display: true,
                        color: 'black',
                        font: {
                            size: 8,
                            family: '"Press Start 2P", system-ui, -apple-system, sans-serif'
                        }
                    },
                    grid: {
                        color: '#eee'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Top 10 Manufacturers by Device Count',
                    color: 'black',
                    font: {
                        family: '"Press Start 2P", system-ui, -apple-system, sans-serif',
                        size: 12
                    }
                },
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        font: {
                            family: '"Press Start 2P", system-ui, -apple-system, sans-serif',
                            size: 8
                        }
                    }
                },
                tooltip: {
                    enabled: true,
                    borderColor: '#222',
                    borderWidth: 1,
                    titleFont: {
                        family: '"Press Start 2P", system-ui, -apple-system, sans-serif',
                        size: 10
                    },
                    bodyFont: {
                        family: '"Press Start 2P", system-ui, -apple-system, sans-serif',
                        size: 8
                    },
                    padding: 8,
                    callbacks: {
                        title: () => null,
                        label: (ctx) => `${ctx.dataset.label}: ${ctx.formattedValue} devices`
                    }
                }
            }
        }
    });
}
loadTopManufacturersChart();

async function loadNewVsReturning(scanIds = []) {
    const res = await fetch(`/api/devices/new-vs-returning-devices/?scan_id=${scanIds.join(',')}`);
    const json = await res.json();

    const ctx = document.getElementById('newVsReturningChart').getContext('2d');
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['New Devices', 'Returning Devices'],
            datasets: [{
                data: [json.new, json.returning],
                backgroundColor: chartColors,
                borderColor: '#000',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { 
                title: { 
                    display: true, 
                    text: 'New vs Returning Devices', 
                    font: {
                        family: '"Press Start 2P", system-ui, -apple-system, sans-serif',
                        size: 12
                    } 
                },
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        font: {
                            family: '"Press Start 2P", system-ui, -apple-system, sans-serif',
                            size: 8
                        }
                    }
                },
                tooltip: {
                    enabled: true,
                    borderColor: '#222',
                    borderWidth: 1,
                    titleFont: {
                        family: '"Press Start 2P", system-ui, -apple-system, sans-serif',
                        size: 10
                    },
                    bodyFont: {
                        family: '"Press Start 2P", system-ui, -apple-system, sans-serif',
                        size: 8
                    },
                    padding: 8
                }
            }
        }
    });
}
loadNewVsReturning();
