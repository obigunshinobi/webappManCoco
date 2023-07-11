let scanner = new Instascan.Scanner({
    video: document.getElementById('preview'),
    mirror: false,
    captureImage: false,
    backgroundScan: false,
    refractoryPeriod: 5000,
    scanPeriod: 1,
});

scanner.addListener('scan', function (content) {
    console.log('Full QR code content:', content);
    let parts = content.split('-');
    let stampId = parts[0];
    let userId = parts[1];
    console.log('Extracted stamp ID:', stampId);
    console.log('Extracted user ID:', userId);
    fetch('/validate_stamp/' + stampId + '/' + userId, { method: 'POST' })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.text();
        })
        .then(data => {
            console.log(data);
            if (data.trim() === "Stamp validated") {
                window.location.href = "/merchant";
            }
        })
        .catch((error) => {
            console.error('Error:', error);
        });
});

Instascan.Camera.getCameras().then(function (cameras) {
    if (cameras.length > 0) {
        scanner.start(cameras[0]);
    } else {
        console.error('No cameras found.');
    }
}).catch(function (e) {
    console.error(e);
});
