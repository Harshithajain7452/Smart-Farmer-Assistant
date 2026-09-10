/* Nearby mandi finder — browser Geolocation API + Leaflet/OpenStreetMap. */
(function () {
  const mapEl = document.getElementById('nearby-map');
  if (!mapEl || typeof L === 'undefined') return;

  const listEl = document.getElementById('marketList');
  const statusEl = document.getElementById('geoStatus');
  const map = L.map('nearby-map').setView([22.9734, 78.6569], 5);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18, attribution: '© OpenStreetMap contributors'
  }).addTo(map);

  let markers = [];
  function clearMarkers() { markers.forEach(function (m) { map.removeLayer(m); }); markers = []; }

  function render(list, lat, lon) {
    clearMarkers();
    listEl.innerHTML = '';
    if (!list.length) {
      listEl.innerHTML = '<div class="text-muted-2 p-3">No markets found within this radius. ' +
        'Increase the search radius and try again.</div>';
      return;
    }
    const you = L.marker([lat, lon]).addTo(map).bindPopup('<strong>Your location</strong>');
    markers.push(you);

    list.forEach(function (m, i) {
      const marker = L.marker([m.lat, m.lon]).addTo(map).bindPopup(
        '<strong>' + m.name + '</strong><br>' + m.district + ', ' + m.state +
        '<br>' + m.distance_km + ' km away<br>' + m.commodities +
        '<br><a href="' + m.directions + '" target="_blank" rel="noopener">Get directions</a>');
      markers.push(marker);

      const card = document.createElement('div');
      card.className = 'card-soft p-3 mb-2 card-hover fade-up';
      card.innerHTML =
        '<div class="d-flex justify-content-between align-items-start gap-2">' +
        '<div><div class="fw-bold">' + m.name + '</div>' +
        '<div class="small text-muted-2">' + m.district + ', ' + m.state + '</div>' +
        '<div class="small mt-1"><i class="bi bi-basket me-1"></i>' + m.commodities + '</div>' +
        '<div class="small"><i class="bi bi-telephone me-1"></i>' + m.phone + '</div></div>' +
        '<span class="pill">' + m.distance_km + ' km</span></div>' +
        '<div class="mt-2 d-flex gap-2"><a class="btn btn-brand btn-sm" target="_blank" rel="noopener" href="' +
        m.directions + '"><i class="bi bi-signpost-2 me-1"></i>Directions</a>' +
        '<a class="btn btn-ghost btn-sm" href="tel:' + m.phone.replace(/\s/g, '') + '">Call</a></div>';
      card.addEventListener('click', function () { map.setView([m.lat, m.lon], 11); marker.openPopup(); });
      listEl.appendChild(card);
    });

    map.fitBounds(L.featureGroup(markers).getBounds().pad(0.25));
  }

  function locate() {
    if (!navigator.geolocation) {
      statusEl.textContent = 'Geolocation is not supported by this browser.';
      return;
    }
    statusEl.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Detecting your location…';
    listEl.innerHTML = '<div class="skeleton mb-2" style="height:86px"></div>'.repeat(3);

    navigator.geolocation.getCurrentPosition(function (pos) {
      const lat = pos.coords.latitude, lon = pos.coords.longitude;
      const radius = document.getElementById('radiusSelect').value;
      statusEl.textContent = 'Showing markets near ' + lat.toFixed(3) + ', ' + lon.toFixed(3);
      fetch('/api/nearby-markets?lat=' + lat + '&lon=' + lon + '&radius=' + radius)
        .then(function (r) { return r.json(); })
        .then(function (data) { render(data.markets || [], lat, lon); })
        .catch(function () { statusEl.textContent = 'Could not load markets. Please retry.'; });
    }, function (err) {
      statusEl.textContent = 'Location permission denied (' + err.message +
        '). Showing all listed markets instead.';
      listEl.innerHTML = '';
      (window.ALL_MARKETS || []).forEach(function (m) {
        const marker = L.marker([m.lat, m.lon]).addTo(map)
          .bindPopup('<strong>' + m.name + '</strong><br>' + m.district + ', ' + m.state);
        markers.push(marker);
      });
    }, { enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 });
  }

  document.getElementById('locateBtn').addEventListener('click', locate);
  document.getElementById('radiusSelect').addEventListener('change', locate);
  locate();
})();
