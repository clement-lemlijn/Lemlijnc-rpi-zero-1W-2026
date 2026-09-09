import io
import logging
import socketserver
from http import server
from threading import Condition

from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput

PAGE = """\
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pi Zero Cam — Clément Lemlijn</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    --pi-red: #c51a4a;
    --pi-red-light: #fdf0f4;
    --bg: #f8f9fb;
    --card: #ffffff;
    --text: #1a1a1a;
    --text-muted: #5c5c6a;
    --border: #e8e8ee;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    line-height: 1.6;
  }

  .container {
    max-width: 920px;
    margin: 0 auto;
    padding: 2rem 1.5rem 3rem;
  }

  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.25rem 0 2.5rem;
    flex-wrap: wrap;
    gap: 0.75rem;
  }

  .logo-text {
    font-weight: 600;
    font-size: 1.15rem;
    letter-spacing: -0.02em;
  }

  .badge {
    background: var(--pi-red-light);
    color: var(--pi-red);
    font-size: 0.8rem;
    font-weight: 600;
    padding: 0.4rem 0.9rem;
    border-radius: 999px;
    border: 1px solid rgba(197, 26, 74, 0.2);
    white-space: nowrap;
  }

  .badge::before {
    content: "● ";
  }

  .hero {
    text-align: center;
    margin-bottom: 3rem;
  }

  h1 {
    font-size: clamp(1.8rem, 5vw, 2.6rem);
    font-weight: 700;
    letter-spacing: -0.03em;
    margin-bottom: 0.6rem;
  }

  h1 span { color: var(--pi-red); }

  .subtitle {
    font-size: 1.05rem;
    color: var(--text-muted);
    max-width: 460px;
    margin: 0 auto 2.25rem;
  }

  /* Flux vidéo responsive */
  .stream-wrapper {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 0.75rem;
    box-shadow: 0 20px 40px -15px rgba(197, 26, 74, 0.18);
    max-width: 720px;
    margin: 0 auto;
  }

  .stream-frame {
    width: 100%;
    aspect-ratio: 4 / 3;
    border-radius: 12px;
    overflow: hidden;
    background: #111;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .stream-frame img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }

  .cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.25rem;
    margin: 2.5rem 0 3rem;
  }

  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.4rem;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
  }

  .card-icon {
    width: 40px;
    height: 40px;
    background: var(--pi-red-light);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 0.9rem;
    font-size: 1.2rem;
  }

  .card h3 {
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 0.35rem;
  }

  .card p {
    font-size: 0.88rem;
    color: var(--text-muted);
  }

  footer {
    text-align: center;
    padding-top: 2rem;
    border-top: 1px solid var(--border);
    color: var(--text-muted);
    font-size: 0.85rem;
  }

  .highlight { color: var(--pi-red); font-weight: 500; }

  @media (max-width: 480px) {
    .container { padding: 1.5rem 1rem 2rem; }
    .cards { grid-template-columns: 1fr; }
  }
</style>
</head>
<body>
  <div class="container">

    <header>
      <div class="logo-text">Pi Zero Cam</div>
      <div class="badge">En direct</div>
    </header>

    <section class="hero">
      <h1>Flux <span>caméra</span></h1>
      <p class="subtitle">Diffusion en direct depuis mon Raspberry Pi Zero W.</p>

      <div class="stream-wrapper">
        <div class="stream-frame">
          <img src="stream.mjpg" alt="Flux caméra en direct">
        </div>
      </div>
    </section>

    <div class="cards">
      <div class="card">
        <div class="card-icon">📷</div>
        <h3>Picamera2</h3>
        <p>Encodage MJPEG en direct via le module caméra du Pi Zero.</p>
      </div>

      <div class="card">
        <div class="card-icon">📡</div>
        <h3>Streaming HTTP</h3>
        <p>Serveur Python léger, diffusion multipart/x-mixed-replace.</p>
      </div>

      <div class="card">
        <div class="card-icon">⚡</div>
        <h3>Raspberry Pi Zero W</h3>
        <p>Faible consommation, toujours prêt à filmer.</p>
      </div>
    </div>

    <footer>
      <p>Propulsé par un <span class="highlight">Raspberry Pi Zero W</span> • Picamera2</p>
      <p>Clément Lemlijn — 2026</p>
    </footer>

  </div>
</body>
</html>
"""

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning('Client déconnecté %s: %s', self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

picam2 = Picamera2()
# Résolution basse recommandée sur Zero W (tu peux monter à 800x600 si ça tient)
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
output = StreamingOutput()
picam2.start_recording(JpegEncoder(), FileOutput(output))

try:
    address = ('', 8080)          # Port 8080
    server = StreamingServer(address, StreamingHandler)
    print("Serveur démarré → http://IP-DU-PI:8080")
    server.serve_forever()
finally:
    picam2.stop_recording()
