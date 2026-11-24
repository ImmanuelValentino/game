<?php
require_once __DIR__ . '/common.php';

$savesDir = oakhaven_saves_dir();
$writable = is_dir($savesDir) && is_writable($savesDir);

oakhaven_send_json(200, array(
    'ok' => true,
    'service' => 'oakhaven-save-api',
    'php_version' => PHP_VERSION,
    'saves_writable' => $writable,
    'timestamp' => gmdate('c'),
));
