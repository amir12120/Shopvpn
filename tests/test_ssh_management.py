# -*- coding: utf-8 -*-
"""Regression tests for the SSH/quota work merged from upstream.

Kept dependency-free so the same tests run in the lean CI job.
"""
import base64
from urllib.parse import urlsplit, unquote

import pytest

import dedicated_sub as ds
import ssh_service
from database import Database
from ssh_uri import build_ssh_uri


def _db(tmp_path) -> Database:
    db = Database(str(tmp_path / "bot.db"))
    db.init_db(owner_id=1)
    return db


def _combo_service(db, user_id: int = 100):
    db.add_or_update_user(user_id, "user", "User")
    server_id = db.add_panel_server("Panel", "pasarguard", "https://panel.example.com", "u", "p")
    config_id = db.add_custom_config(
        user_id, server_id, "combo", 10, 30, "https://sub.example.com/x",
        source="direct_product",
    )
    pool_id = db.create_quota_pool(user_id, 10, None, "test pool")
    assert db.attach_custom_config_to_quota_pool(pool_id, config_id)
    node_id = db.create_ssh_node("Germany-SSH-1", "linux", "ssh.example.com")
    account_row = db.register_ssh_account(
        node_id, user_id, "acc-1", "combo_ssh", "ssh.example.com", 22, pool_id,
        None, "encrypted",
    )
    return config_id, pool_id, node_id, account_row


def test_ssh_uri_round_trip():
    uri = build_ssh_uri("root", "ZP9QUTS47qAg#l4U", "31.56.196.63", 24720, "Fff")
    assert uri == "ssh://cm9vdDpaUDlRVVRTNDdxQWcjbDRV@31.56.196.63:24720#Fff"
    parsed = urlsplit(uri)
    assert parsed.hostname == "31.56.196.63"
    assert parsed.port == 24720
    assert base64.b64decode(parsed.username).decode() == "root:ZP9QUTS47qAg#l4U"
    assert unquote(parsed.fragment) == "Fff"


def test_ssh_uri_brackets_ipv6_and_rejects_missing_password():
    parsed = urlsplit(build_ssh_uri("user", "password1234567890", "2001:db8::1", 2200, "v6"))
    assert parsed.hostname == "2001:db8::1"
    assert parsed.port == 2200
    with pytest.raises(ValueError):
        build_ssh_uri("user", "", "127.0.0.1", 22, "x")


def test_plain_and_base64_subscriptions_recognize_ssh_uri():
    uri = "ssh://alice:secret@ssh.example.com:22#Germany-SSH"
    for raw in (uri.encode(), base64.b64encode(uri.encode())):
        body = ds.parse_body(raw)
        assert body.kind == "uris"
        assert body.uris == [uri]
    assert ds.uri_protocol(uri) == "SSH"
    assert ds.uri_remark(uri) == "Germany-SSH"


def test_ssh_account_is_linked_to_vpn_config_and_pool(tmp_path):
    db = _db(tmp_path)
    config_id, pool_id, node_id, _ = _combo_service(db)
    assert db.link_ssh_account_to_config("acc-1", config_id)
    rows = db.ssh_accounts_for_config(config_id)
    assert len(rows) == 1
    assert rows[0]["username"] == "combo_ssh"
    assert rows[0]["node_name"] == "Germany-SSH-1"
    pool = db.quota_pool_for_custom_config(config_id)
    assert pool and int(pool["id"]) == pool_id
    assert db.update_ssh_node_name(node_id, "Germany-2")
    overview = ssh_service.overview(db)
    assert overview["nodes"][0]["name"] == "Germany-2"
    assert overview["accounts"][0]["account_id"] == "acc-1"
    assert overview["pools"][0]["members"]


def test_ssh_accounts_require_an_existing_config(tmp_path):
    db = _db(tmp_path)
    _, _, _, _ = _combo_service(db)
    assert db.link_ssh_account_to_config("missing-account", 1) is False
    assert db.ssh_accounts_for_config(1) == []


def test_shared_pool_quota_is_authoritative_for_subscription(tmp_path):
    db = _db(tmp_path)
    config_id, pool_id, _, _ = _combo_service(db)
    db.record_usage_snapshot("vpn", f"custom_config:{config_id}", 120 * 1024 ** 2,
                             source="test")
    db.record_usage_snapshot("ssh", "acc-1", 80 * 1024 ** 2, source="test")
    info = ds.quota_info_for_config(db, config_id)
    assert info["total"] == 10 * 1024 ** 3
    assert info["upload"] == 200 * 1024 ** 2
    assert info["download"] == 0

