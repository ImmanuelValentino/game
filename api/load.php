<?php
require_once __DIR__ . '/common.php';

if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    oakhaven_send_json(405, array('ok' => false, 'error' => 'Method not allowed'));
}

$rawId = isset($_GET['player_id']) ? $_GET['player_id'] : '';
$playerId = oakhaven_sanitize_player_id($rawId);
if ($playerId === null) {
    oakhaven_send_json(400, array('ok' => false, 'error' => 'Invalid player_id'));
}

$path = oakhaven_save_path($playerId);
if (!is_file($path)) {
    oakhaven_send_json(200, array('ok' => true, 'found' => false, 'data' => null));
}

$content = @file_get_contents($path);
if ($content === false) {
    oakhaven_send_json(500, array('ok' => false, 'error' => 'Unable to read save file'));
}

$decoded = json_decode($content, true);
if (json_last_error() !== JSON_ERROR_NONE || !is_array($decoded) || !isset($decoded['data'])) {
    oakhaven_send_json(200, array('ok' => true, 'found' => false, 'data' => null));
}

oakhaven_send_json(200, array(
    'ok' => true,
    'found' => true,
    'updated_at' => isset($decoded['updated_at']) ? $decoded['updated_at'] : null,
    'data' => $decoded['data'],
));
