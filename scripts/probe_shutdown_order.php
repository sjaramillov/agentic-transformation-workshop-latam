<?php
// Original regression probe for the workshop. Run with php -n, never as an endpoint.
// A fake mysqli isolates callback/connection ordering. It does not test SQL or a DB.
if (extension_loaded('mysqli') || $argc !== 2 || !is_file($argv[1])) {
    fwrite(STDERR, "Usage: php -n probe_shutdown_order.php /path/to/index.php\n");
    exit(2);
}
class mysqli {
    public $connect_error = null;
    public $affected_rows = 1;
    private $closed = false;
    public function __construct(...$args) {}
    public function query($sql) { return true; }
    public function prepare($sql) {
        if ($this->closed) { throw new Error('PROBE: response persistence attempted after connection close'); }
        return new ProbeStatement($sql);
    }
    public function close() { $this->closed = true; }
}
class ProbeStatement {
    public function __construct(private $sql) {}
    public function bind_param($types, &...$values) {}
    public function execute() {
        if (str_contains($this->sql, 'UPDATE idempotency_keys')) {
            fwrite(STDERR, "PROBE_RESPONSE_PERSISTENCE_REACHED\n");
        }
        return true;
    }
    public function close() {}
}
$_SERVER['REQUEST_METHOD'] = 'DELETE';
$_SERVER['REQUEST_URI'] = '/api/bookings/1';
$_SERVER['HTTP_IDEMPOTENCY_KEY'] = 'synthetic-regression-key';
$_SERVER['REMOTE_ADDR'] = '127.0.0.1';
http_response_code(200);
require $argv[1];
