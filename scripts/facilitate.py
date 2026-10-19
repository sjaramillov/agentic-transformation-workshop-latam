#!/usr/bin/env python3
"""Open the guided workshop locally; Python standard library, no cloud calls."""
import argparse
from contextlib import contextmanager
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import secrets
import shlex
import sys
import webbrowser

try:
    from .discovery import Lesson, ROOT, Session
except ImportError:
    from discovery import Lesson, ROOT, Session


@contextmanager
def session_lock(directory):
    # Supported teaching environments are Linux, macOS and WSL. The OS releases
    # this lock even after a killed process, so the session can always resume.
    import fcntl
    directory.mkdir(parents=True, exist_ok=True)
    with (directory/'.lock').open('a') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('Esta sesión ya está abierta en otra terminal') from None
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def make_server(session, port=0):
    token = secrets.token_urlsafe(32)
    static = ROOT/'workshop/coach'
    try:
        session_path = session.directory.resolve().relative_to(ROOT)
    except ValueError:
        session_path = session.directory.resolve()

    def view():
        return {**session.lesson.view(session.state), 'token': token,
                'prepare_command': 'python3 scripts/workshop.py prepare --discovery ' +
                shlex.quote(str(session_path)) + ' --output .local/workshop-01'}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def reply(self, status, body, content_type='application/json; charset=utf-8'):
            raw = json.dumps(body, ensure_ascii=False).encode() if isinstance(body, dict) else body
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(raw)))
            self.send_header('Cache-Control', 'no-store')
            if self.path == '/tablero.html':
                self.send_header('Content-Disposition', 'attachment; filename="tablero.html"')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
            self.end_headers()
            self.wfile.write(raw)

        def allowed_host(self):
            return self.headers.get('Host') == f'127.0.0.1:{self.server.server_port}'

        def do_GET(self):
            self.connection.settimeout(5)
            if not self.allowed_host():
                return self.reply(403, {'error': 'Abre la URL 127.0.0.1 que aparece en la terminal'})
            if self.path == '/api/session':
                return self.reply(200, view())
            if self.path == '/favicon.ico':
                return self.reply(204, b'', 'image/x-icon')
            routes = {'/': ('index.html', 'text/html; charset=utf-8'),
                      '/boards.js': ('boards.js', 'text/javascript; charset=utf-8'),
                      '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
                      '/style.css': ('style.css', 'text/css; charset=utf-8')}
            if self.path in routes:
                name, mime = routes[self.path]
                return self.reply(200, (static/name).read_bytes(), mime)
            downloads = {'/tablero.html': ('tablero.html', 'text/html; charset=utf-8'),
                         '/resumen.md': ('resumen.md', 'text/plain; charset=utf-8'),
                         '/session.json': ('session.json', 'application/json; charset=utf-8'),
                         '/contexts/ara.txt': ('contexts/ara.txt', 'text/plain; charset=utf-8'),
                         '/contexts/moda.txt': ('contexts/moda.txt', 'text/plain; charset=utf-8')}
            if self.path in downloads:
                name, mime = downloads[self.path]
                file = session.directory/name
                if file.is_file():
                    return self.reply(200, file.read_bytes(), mime)
            return self.reply(404, {'error': 'Recurso no disponible'})

        def do_POST(self):
            self.connection.settimeout(5)
            origin = f'http://127.0.0.1:{self.server.server_port}'
            if (not self.allowed_host() or self.headers.get('Origin') not in (None, origin)
                    or not secrets.compare_digest(self.headers.get('X-Workshop-Token', ''), token)):
                return self.reply(403, {'error': 'Abre el ejercicio desde la URL de la terminal'})
            if self.path not in ('/api/answer', '/api/next'):
                return self.reply(404, {'error': 'Acción no disponible'})
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 2048 or self.headers.get('Content-Type') != 'application/json':
                    raise ValueError('Solicitud no válida')
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError('Solicitud no válida')
                if self.path == '/api/answer':
                    session.answer(data.get('cursor'), data.get('choice'))
                else:
                    session.advance(data.get('count'))
            except (ValueError, TypeError, KeyError) as error:
                return self.reply(409, {'error': str(error)})
            except OSError:
                return self.reply(500, {'error': 'No se pudo guardar. Comprueba el espacio disponible y vuelve a abrir la sesión.'})
            return self.reply(200, view())

    server = HTTPServer(('127.0.0.1', port), Handler)
    server.timeout = 1
    return server


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'.local/discovery-01', help='Carpeta de la sesión; se retoma si ya existe')
    parser.add_argument('--port', type=int, default=0, help='0 elige un puerto libre')
    parser.add_argument('--no-browser', action='store_true', help='Mostrar la URL sin abrir el navegador')
    args = parser.parse_args(argv)
    if not 0 <= args.port <= 65535:
        parser.error('El puerto debe estar entre 0 y 65535')
    try:
        lesson = Lesson.local()
        with session_lock(args.output):
            session = Session(args.output, lesson)
            with make_server(session, args.port) as server:
                url = f'http://127.0.0.1:{server.server_port}'
                print(f'WORKSHOP_READY {url}', flush=True)
                print(f'Sesión: {args.output.resolve()}\nCtrl+C para pausar. El mismo comando retoma tu avance.', flush=True)
                if not args.no_browser:
                    try:
                        webbrowser.open(url)
                    except webbrowser.Error:
                        print('Abre la URL en tu navegador.', flush=True)
                server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        print('\nSesión guardada. Puedes retomarla con el mismo comando.')
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
