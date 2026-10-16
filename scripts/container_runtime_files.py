#!/usr/bin/env python3
"""Add original local-runtime files to an isolated PHP workshop copy.

This does not repair application authorization, transactions or cloud IaC.
Existing files are refused; review the printed paths and diff before committing.
"""
import argparse
from pathlib import Path

FILES = {
    '.dockerignore': '.git\nservices\nreports\n*.log\n.env\n.env.*\ninfrastructure\nk8s\n',
    'health-live.php': '<?php\nheader("Content-Type: application/json");\necho json_encode(["status" => "alive"]);\n',
    'health-ready.php': '''<?php
header("Content-Type: application/json");
mysqli_report(MYSQLI_REPORT_ERROR | MYSQLI_REPORT_STRICT);
try {
    $db = mysqli_init();
    $db->options(MYSQLI_OPT_CONNECT_TIMEOUT, 2);
    $db->real_connect(getenv('DB_HOST') ?: 'localhost', getenv('DB_USER'), getenv('DB_PASS'), getenv('DB_NAME'));
    $db->query('SELECT 1');
    $db->close();
    echo json_encode(['status' => 'ready']);
} catch (Throwable $error) {
    http_response_code(503);
    echo json_encode(['status' => 'not_ready']);
}
''',
    'apache-workshop.conf': '''<Directory /var/www/html>
    Options -Indexes
    AllowOverride None
    Require all granted
    FallbackResource /index.php
</Directory>
<LocationMatch "(^|/)\\.">
    Require all denied
</LocationMatch>
''',
    'php-workshop.ini': 'display_errors=Off\nlog_errors=On\nerror_reporting=E_ALL\n',
    'Dockerfile.runtime': '''# Original runtime harness; no cloud deployment is performed.
FROM php:8.2-apache
RUN docker-php-ext-install mysqli
COPY apache-workshop.conf /etc/apache2/conf-enabled/workshop.conf
COPY php-workshop.ini /usr/local/etc/php/conf.d/workshop.ini
COPY index.php health-live.php health-ready.php /var/www/html/
EXPOSE 80
HEALTHCHECK --interval=5s --timeout=3s --start-period=5s --retries=3 CMD curl -fsS http://localhost/health-live.php || exit 1
''',
}


def install(destination):
    destination = Path(destination).resolve()
    if not (destination / 'index.php').is_file():
        raise ValueError('Expected an isolated PHP application with index.php')
    conflicts = [name for name in FILES if (destination / name).exists() or (destination / name).is_symlink()]
    if conflicts:
        raise ValueError('Refusing to overwrite: ' + ', '.join(conflicts))
    for name, content in FILES.items():
        (destination / name).write_text(content)
    return list(FILES)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    try:
        for name in install(args.destination):
            print(name)
    except (ValueError, OSError) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()
