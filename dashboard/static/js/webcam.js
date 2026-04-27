let stream = null;
const capturedBlobs = [];

async function startCamera() {
  const video = document.getElementById('webcam');
  const placeholder = document.getElementById('cam-placeholder');
  const captureBtn = document.getElementById('capture-btn');
  const startBtn = document.getElementById('start-cam-btn');

  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
    video.srcObject = stream;
    placeholder.classList.add('hidden');
    captureBtn.disabled = false;
    startBtn.textContent = 'Camera On';
    startBtn.disabled = true;
  } catch (err) {
    alert('Cannot access camera: ' + err.message);
  }
}

async function capturePhotos() {
  const video = document.getElementById('webcam');
  const countdown = document.getElementById('countdown');
  const thumbs = document.getElementById('thumbnails');
  const captureBtn = document.getElementById('capture-btn');
  const status = document.getElementById('capture-status');
  const submitBtn = document.getElementById('submit-btn');

  if (!stream) { alert('Start the camera first.'); return; }

  captureBtn.disabled = true;
  capturedBlobs.length = 0;
  thumbs.innerHTML = '';

  for (let i = 0; i < 5; i++) {
    // Countdown 3…2…1
    for (let s = 3; s >= 1; s--) {
      countdown.textContent = s;
      countdown.classList.remove('hidden');
      await sleep(700);
    }
    countdown.classList.add('hidden');

    // Capture frame
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);

    const blob = await new Promise(res => canvas.toBlob(res, 'image/jpeg', 0.92));
    capturedBlobs.push(blob);

    // Preview thumbnail
    const img = document.createElement('img');
    img.src = URL.createObjectURL(blob);
    img.className = 'photo-thumb';
    img.title = `Photo ${i + 1}`;
    thumbs.appendChild(img);

    status.textContent = `Captured ${i + 1} / 5`;
    await sleep(800);
  }

  status.textContent = '5 photos captured ✓ — fill in the details and submit.';
  submitBtn.disabled = false;
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// Form submission — send as multipart
document.getElementById('register-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const form = e.target;
  const submitBtn = document.getElementById('submit-btn');
  const label = document.getElementById('submit-label');
  const errEl = document.getElementById('form-error');

  if (capturedBlobs.length < 5) {
    errEl.textContent = 'Please capture 5 photos first.';
    errEl.classList.remove('hidden');
    return;
  }

  const fd = new FormData(form);
  // Remove the file input placeholder if any; attach blobs as 'photos'
  fd.delete('photos');
  capturedBlobs.forEach((blob, i) => fd.append('photos', blob, `photo_${i + 1}.jpg`));

  submitBtn.disabled = true;
  label.innerHTML = '<span class="spinner"></span> Registering…';
  errEl.classList.add('hidden');

  try {
    const res = await fetch('/api/employees/register', { method: 'POST', body: fd });
    const data = await res.json();
    if (!res.ok) {
      errEl.textContent = data.detail || 'Registration failed.';
      errEl.classList.remove('hidden');
      submitBtn.disabled = false;
      label.textContent = 'Register Employee';
    } else {
      window.location.href = `/dashboard/employees/${data.employee_id}?registered=1`;
    }
  } catch (err) {
    errEl.textContent = 'Network error: ' + err.message;
    errEl.classList.remove('hidden');
    submitBtn.disabled = false;
    label.textContent = 'Register Employee';
  }
});
