<?php
require_once __DIR__ . '/common.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    oakhaven_send_json(405, array('ok' => false, 'error' => 'Method not allowed'));
}

$raw = file_get_contents('php://input', false, null, 0, 262144);
if ($raw === false || strlen($raw) === 0) {
    oakhaven_send_json(400, array('ok' => false, 'error' => 'Empty request body'));
}

$body = json_decode($raw, true);
if (json_last_error() !== JSON_ERROR_NONE || !is_array($body)) {
    oakhaven_send_json(400, array('ok' => false, 'error' => 'Invalid JSON payload'));
}

$playerId = oakhaven_sanitize_player_id(isset($body['player_id']) ? $body['player_id'] : '');
if ($playerId === null) {
    oakhaven_send_json(400, array('ok' => false, 'error' => 'Invalid player_id format'));
}

if (!isset($body['data']) || !is_array($body['data'])) {
    oakhaven_send_json(400, array('ok' => false, 'error' => 'Missing save data object'));
}

$saveRecord = array(
    'player_id' => $playerId,
    'updated_at' => gmdate('c'),
    'data' => $body['data'],
);

$encoded = json_encode($saveRecord, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
if ($encoded === false) {
    oakhaven_send_json(500, array('ok' => false, 'error' => 'Failed to encode save data'));
}

$targetPath = oakhaven_save_path($playerId);
$bytes = @file_put_contents($targetPath, $encoded, LOCK_EX);
if ($bytes === false) {
    oakhaven_send_json(500, array('ok' => false, 'error' => 'Failed to write save file'));
}

oakhaven_send_json(200, array(
    'ok' => true,
    'player_id' => $playerId,
    'bytes' => $bytes,
    'updated_at' => $saveRecord['updated_at'],
));
