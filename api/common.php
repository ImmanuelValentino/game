<?php
/**
 * Shared helpers for Ashes of Oakhaven Save API (Strict PHP 7.2 compatible).
 */

function oakhaven_send_json($status, $payload) {
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0');
    echo json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function oakhaven_sanitize_player_id($raw) {
    if (!is_string($raw)) {
        return null;
    }
    $trimmed = trim($raw);
    if (!preg_match('/^[A-Za-z0-9_-]{8,48}$/', $trimmed)) {
        return null;
    }
    return $trimmed;
}

function oakhaven_saves_dir() {
    $dir = dirname(__DIR__) . DIRECTORY_SEPARATOR . 'saves';
    if (!is_dir($dir)) {
        @mkdir($dir, 0755, true);
    }
    return $dir;
}

function oakhaven_save_path($playerId) {
    return oakhaven_saves_dir() . DIRECTORY_SEPARATOR . $playerId . '.json';
}
