# Security Hardening & Test Coverage — 25 Iterations

> **Status**: Draft  
> **Author**: Brainstorm Agent  
> **Date**: 2026-03-30  
> **Versions**: v1.3.1 – v1.3.25  
> **Baseline**: 1,263 backend tests (65 files) + 741 frontend tests (79 files)  
> **Target**: ~1,650+ backend tests + ~800+ frontend tests  

---

## Executive Summary

25 incremental iterations that systematically harden SignalFlow AI's security posture and expand test coverage. Each iteration is self-contained, shippable, and adds ≥15 new tests. Iterations are grouped into five themes aligned with OWASP Top 10 categories.

### Current Security Posture (What Exists)

| Layer | Already Implemented |
|-------|-------------------|
| Auth | JWT (HS256) + API key + bcrypt passwords + token revocation + account lockout |
| Rate Limiting | slowapi on all mutating endpoints (per-IP) |
| Input Validation | Pydantic v2 schemas, password complexity, `sanitizer.py` for Claude prompts |
| Headers | CSP, X-Frame-Options DENY, X-Content-Type-Options, HSTS (prod), Referrer-Policy, Permissions-Policy |
| Request Size | 1MB body limit middleware |
| WebSocket | Connection limits (500 total, 5/IP), idle timeout, message rate limiting |
| Circuit Breaker | Redis-backed circuit breaker for external APIs |
| Data Integrity | OHLCV candle validation, Decimal for all financial values, FOR UPDATE SKIP LOCKED |
| Existing Tests | 5 security sprint files, 5 breaker test files, auth tests, password tests |

### Gaps Identified

| Gap | Risk | OWASP |
|-----|------|-------|
| No SSRF protection on user-supplied URLs (AI Q&A, news URLs) | High | A10 |
| No path traversal tests on SEO slug endpoint | Medium | A01 |
| No IDOR tests (accessing another user's trades/alerts by ID) | High | A01 |
| Symbol/slug inputs used in ILIKE without full sanitization | Medium | A03 |
| WebSocket auth ticket has no IP binding | Medium | A07 |
| No tests for JWT algorithm confusion (alg:none) attack | High | A07 |
| Admin endpoint auth is header-based only (no RBAC model) | Medium | A01 |
| Razorpay webhook signature bypass not tested | High | A08 |
| No enumeration protection on login (timing oracle) | Low | A07 |
| No tests for Celery task auth (internal API key) | Medium | A07 |
| Error responses may leak stack traces in edge cases | Medium | A05 |
| No tests for concurrent write operations (double-spend) | High | A04 |
| No frontend XSS regression tests | Medium | A03 |
| No test for token refresh race condition | Medium | A07 |
| Shared signal endpoint has no abuse limit | Low | A04 |

---

## Iteration Index

| Version | Theme | Title | New Tests |
|---------|-------|-------|-----------|
| v1.3.1 | Input Validation | SQL Injection Deep Sweep | 20 |
| v1.3.2 | Input Validation | XSS & HTML Injection Hardening | 18 |
| v1.3.3 | Input Validation | Command Injection & Code Execution | 16 |
| v1.3.4 | Input Validation | Path Traversal & File Inclusion | 16 |
| v1.3.5 | Input Validation | SSRF Prevention | 18 |
| v1.3.6 | Auth & Authz | Password Policy & Credential Stuffing | 18 |
| v1.3.7 | Auth & Authz | Session Management & Token Security | 20 |
| v1.3.8 | Auth & Authz | RBAC & Broken Access Control (IDOR) | 22 |
| v1.3.9 | Auth & Authz | Brute Force & Account Lockout | 16 |
| v1.3.10 | Auth & Authz | JWT Algorithm Attacks & Token Abuse | 18 |
| v1.3.11 | API Security | Endpoint-Level Rate Limiting Validation | 16 |
| v1.3.12 | API Security | Request Size & Payload Abuse | 16 |
| v1.3.13 | API Security | CORS Policy Validation | 15 |
| v1.3.14 | API Security | API Versioning & Deprecation Safety | 15 |
| v1.3.15 | API Security | Error Information Leakage | 18 |
| v1.3.16 | Data Protection | PII Handling & Data Minimization | 16 |
| v1.3.17 | Data Protection | Encryption & Secure Transport | 16 |
| v1.3.18 | Data Protection | Security Headers Comprehensive Validation | 18 |
| v1.3.19 | Data Protection | Cookie Security & Frontend State | 16 |
| v1.3.20 | Data Protection | Secrets Management & Config Hardening | 16 |
| v1.3.21 | Test Coverage | Edge Cases in Signal Pipeline | 20 |
| v1.3.22 | Test Coverage | Concurrency & Race Conditions | 18 |
| v1.3.23 | Test Coverage | Integration & End-to-End Security Flows | 20 |
| v1.3.24 | Test Coverage | Negative Testing & Boundary Values | 20 |
| v1.3.25 | Test Coverage | Chaos & Fault Injection | 18 |
| | | **Total New Tests** | **~450** |

---

## Theme 1: Input Validation & Injection Prevention (v1.3.1–v1.3.5)

---

### v1.3.1 — SQL Injection Deep Sweep

**OWASP**: A03:2021 – Injection  
**Scope**: Exhaustive SQLi testing across every endpoint that accepts text parameters. Verify SQLAlchemy ORM parameterization protects all queries, including raw `text()` calls and `ilike()` patterns.

**Risk Addressed**: Although SQLAlchemy ORM parameterizes queries, several endpoints use `ilike()` with user input (`symbol`, `slug`, `market`, `outcome`). The `news.py` endpoint uses `symbol.ilike(f"%{symbol}%")` directly. Portfolio `list_trades` does partial sanitization but only strips `%` and `_`.

#### Files to Modify

| File | Change |
|------|--------|
| `backend/app/api/portfolio.py` | Strengthen `safe_symbol` sanitization — add regex whitelist for symbol characters |
| `backend/app/api/news.py` | Add symbol sanitization before `ilike()` call |
| `backend/app/api/signals.py` | Add symbol/market_type enum validation |
| `backend/app/api/history.py` | Add outcome enum validation |

#### Test File: `backend/tests/test_sec_v1_sqli.py`

**Tests (20)**:

```
test_signals_second_order_sqli_via_symbol
test_signals_union_select_via_symbol
test_signals_stacked_query_injection
test_signals_time_based_blind_sqli
test_signals_boolean_blind_sqli
test_history_outcome_sqli_enum_bypass
test_history_market_sqli_with_comments
test_portfolio_symbol_sqli_with_hex_encoding
test_portfolio_trades_sqli_via_limit_param
test_news_symbol_sqli_via_ilike
test_news_market_sqli_via_parameter
test_price_alerts_symbol_sqli
test_alert_config_username_sqli
test_watchlist_symbol_sqli
test_seo_slug_sqli_with_path_separator
test_backtest_symbol_sqli
test_signal_feedback_notes_sqli
test_admin_endpoint_sqli_resistance
test_calendar_event_title_sqli
test_regression_sqli_payloads_from_v1_still_blocked
```

**Regression Guard**: `test_regression_sqli_payloads_from_v1_still_blocked` replays all SQL injection payloads from `test_breaker_security.py` to ensure existing protections survive.

---

### v1.3.2 — XSS & HTML Injection Hardening

**OWASP**: A03:2021 – Injection (Cross-Site Scripting)  
**Scope**: Ensure all user-supplied text stored in the database is safe for rendering. Verify that JSON API responses never contain executable HTML/JS. Test both stored XSS (via database persistence) and reflected XSS (via query parameters in error messages).

**Risk Addressed**: User-controlled fields (`notes` in feedback, `username` in alert config, `notes` in trades, AI Q&A `question`) are stored and potentially rendered by the frontend. The frontend renders `ai_reasoning` as HTML-like content in `AIReasoningPanel` component.

#### Files to Modify

| File | Change |
|------|--------|
| `backend/app/api/signal_feedback.py` | Add `bleach.clean()` or HTML-escape on `notes` field |
| `backend/app/api/alerts.py` | HTML-escape `username` before storage |
| `backend/app/api/portfolio.py` | HTML-escape trade `notes` |
| `frontend/src/components/signals/AIReasoningPanel.tsx` | Ensure `dangerouslySetInnerHTML` is never used; use text rendering |
| `frontend/src/lib/sanitize.ts` | Create client-side sanitization utility |

#### Test File: `backend/tests/test_sec_v2_xss.py`

**Tests (18)**:

```
test_feedback_notes_stored_xss_script_tag
test_feedback_notes_stored_xss_event_handler
test_feedback_notes_stored_xss_svg_onload
test_feedback_notes_polyglot_xss_payload
test_alert_config_username_stored_xss
test_trade_notes_stored_xss
test_trade_symbol_xss_via_output
test_ai_qa_question_reflected_xss
test_ai_qa_symbol_reflected_xss
test_error_response_no_reflected_input
test_signal_shared_view_no_xss_in_reasoning
test_seo_slug_reflected_xss
test_news_symbol_reflected_xss
test_watchlist_symbol_xss
test_calendar_event_title_xss
test_backtest_symbol_xss_in_response
test_html_entities_properly_escaped_in_all_text_fields
test_regression_xss_payloads_from_breaker_still_blocked
```

#### Frontend Test File: `frontend/src/__tests__/security-xss.test.ts`

Additional 5 frontend tests:

```
test_ai_reasoning_panel_no_dangerouslySetInnerHTML
test_signal_card_escapes_symbol_name
test_trade_notes_display_escapes_html
test_api_response_sanitization_utility
test_user_generated_content_rendering_safety
```

---

### v1.3.3 — Command Injection & Code Execution

**OWASP**: A03:2021 – Injection  
**Scope**: Verify no code path allows OS command execution via user input. Test the `sanitizer.py` prompt injection defenses. Verify Celery task parameters cannot trigger arbitrary code execution.

**Risk Addressed**: The `sanitizer.py` has injection pattern detection, but `detect_injection()` returns a boolean without blocking — callers must check the return value. AI Q&A sends user questions to Claude after sanitization, but a bypass could lead to prompt injection. Celery tasks receive symbol names and IDs as parameters — verify they're validated.

#### Files to Modify

| File | Change |
|------|--------|
| `backend/app/services/ai_engine/sanitizer.py` | Add more injection patterns (base64-encoded, unicode bypass, markdown injection) |
| `backend/app/api/ai_qa.py` | Enforce `detect_injection()` check — reject if True |
| `backend/app/tasks/backtest_tasks.py` | Validate symbol parameter format before processing |
| `backend/app/tasks/data_tasks.py` | Validate symbol format in task entry points |

#### Test File: `backend/tests/test_sec_v3_cmdinject.py`

**Tests (16)**:

```
test_sanitizer_blocks_basic_prompt_injection
test_sanitizer_blocks_system_prompt_reveal
test_sanitizer_blocks_jailbreak_attempts
test_sanitizer_blocks_base64_encoded_injection
test_sanitizer_blocks_unicode_bypass_injection
test_sanitizer_blocks_markdown_code_fence_injection
test_sanitizer_detect_injection_returns_true_for_all_patterns
test_sanitizer_truncation_prevents_overflow
test_sanitizer_control_char_removal
test_ai_qa_rejects_detected_injection_attempt
test_ai_qa_question_length_enforced
test_backtest_symbol_format_validated
test_celery_task_symbol_parameter_validation
test_no_subprocess_calls_in_codebase
test_no_eval_exec_in_codebase
test_sanitizer_regression_all_existing_patterns_still_detected
```

---

### v1.3.4 — Path Traversal & File Inclusion

**OWASP**: A01:2021 – Broken Access Control  
**Scope**: Test all endpoints accepting path-like parameters (SEO `slug`, wiki paths, signal IDs, backtest IDs) for path traversal attacks. Verify UUID parameters reject non-UUID formats.

**Risk Addressed**: The SEO endpoint accepts a `slug` parameter that could potentially contain `../` sequences. Signal and backtest endpoints use UUID parameters — FastAPI should validate these, but edge cases with URL-encoded values need testing.

#### Files to Modify

| File | Change |
|------|--------|
| `backend/app/api/seo.py` | Add slug format validation regex: `^[a-z0-9\-]+$` |
| `backend/app/services/seo.py` | Validate slug before database query |
| `backend/app/api/backtest.py` | Add symbol format validation |

#### Test File: `backend/tests/test_sec_v4_pathtraversal.py`

**Tests (16)**:

```
test_seo_slug_path_traversal_dot_dot_slash
test_seo_slug_path_traversal_encoded
test_seo_slug_path_traversal_double_encoded
test_seo_slug_null_byte_injection
test_seo_slug_only_allows_alphanumeric_hyphens
test_signal_id_rejects_non_uuid
test_signal_id_rejects_directory_traversal
test_backtest_id_rejects_non_uuid
test_share_id_rejects_non_uuid
test_config_id_rejects_non_uuid
test_signal_feedback_id_rejects_non_uuid
test_news_signal_id_rejects_non_uuid
test_event_id_rejects_non_uuid
test_url_encoded_path_separators_blocked
test_unicode_path_traversal_blocked
test_regression_uuid_validation_on_all_id_params
```

---

### v1.3.5 — SSRF Prevention

**OWASP**: A10:2021 – Server-Side Request Forgery  
**Scope**: Audit all outbound HTTP calls from the backend for SSRF vulnerabilities. The AI Q&A endpoint calls the Claude API; news fetcher calls external URLs; Razorpay webhooks process external payloads.

**Risk Addressed**: The `ai_qa.py` endpoint makes outbound calls to `api.anthropic.com` — this is hardcoded and safe. However, `news_fetcher.py` aggregates from external RSS/URL sources. If any user-controllable input influences the URLs fetched, SSRF is possible. The Razorpay webhook processes externally-supplied JSON containing URLs and IDs.

#### Files to Modify

| File | Change |
|------|--------|
| `backend/app/services/ai_engine/news_fetcher.py` | Add URL allowlist validation; reject private IP ranges (10.x, 172.16-31.x, 192.168.x, 127.x, 169.254.x) |
| `backend/app/api/payments.py` | Validate webhook payload structure, reject if subscription entity contains unexpected URLs |
| `backend/app/services/ai_engine/news_fetcher.py` | Add DNS rebinding protection (resolve hostname, check IP before fetch) |

#### Test File: `backend/tests/test_sec_v5_ssrf.py`

**Tests (18)**:

```
test_news_fetcher_blocks_private_ip_10x
test_news_fetcher_blocks_private_ip_172x
test_news_fetcher_blocks_private_ip_192x
test_news_fetcher_blocks_localhost_127001
test_news_fetcher_blocks_localhost_hostname
test_news_fetcher_blocks_ipv6_loopback
test_news_fetcher_blocks_link_local_169254
test_news_fetcher_blocks_metadata_endpoint_aws
test_news_fetcher_blocks_metadata_endpoint_gcp
test_news_fetcher_blocks_file_protocol
test_news_fetcher_blocks_gopher_protocol
test_news_fetcher_blocks_ftp_protocol
test_news_fetcher_allows_valid_https_urls
test_news_fetcher_dns_rebinding_protection
test_webhook_payload_structure_validation
test_webhook_rejects_malformed_subscription_entity
test_ai_qa_only_calls_anthropic_api
test_regression_no_user_controlled_outbound_urls
```

---

## Theme 2: Authentication & Authorization Hardening (v1.3.6–v1.3.10)

---

### v1.3.6 — Password Policy & Credential Stuffing

**OWASP**: A07:2021 – Identification and Authentication Failures  
**Scope**: Strengthen password validation, add breach-check stub, test edge cases in password complexity, and prevent credential stuffing via registration.

**Risk Addressed**: Password validation exists in Pydantic schema but edge cases (unicode passwords, zero-width chars, extremely long passwords, passwords matching email) are untested. Registration endpoint doesn't check for common/breached passwords.

#### Files to Modify

| File | Change |
|------|--------|
| `backend/app/schemas/auth.py` | Add checks: password cannot contain email, reject zero-width characters, add common password list check |
| `backend/app/api/auth_routes.py` | Add registration rate limiting per IP (already exists at 5/min — verify it works) |

#### Test File: `backend/tests/test_sec_v6_passwords.py`

**Tests (18)**:

```
test_password_min_length_enforced
test_password_max_length_enforced
test_password_requires_uppercase
test_password_requires_lowercase
test_password_requires_digit
test_password_requires_special_char
test_password_rejects_all_spaces
test_password_rejects_zero_width_chars
test_password_rejects_null_bytes
test_password_rejects_common_passwords_list
test_password_rejects_email_as_password
test_password_accepts_unicode_letters
test_password_edge_case_exactly_8_chars
test_password_edge_case_exactly_128_chars
test_registration_rate_limited_per_ip
test_bcrypt_hash_length_is_60
test_bcrypt_different_salts_per_hash
test_regression_password_validation_matches_schema
```

---

### v1.3.7 — Session Management & Token Security

**OWASP**: A07:2021 – Identification and Authentication Failures  
**Scope**: Test token lifecycle end-to-end: creation → refresh → rotation → revocation → expiry. Verify refresh token rotation invalidates old tokens. Test concurrent refresh race conditions.

**Risk Addressed**: Token refresh endpoint rotates tokens but doesn't test concurrent requests (two refreshes with the same token). The revocation check in `is_token_revoked()` fails open in dev/test — this is correct for testing but must fail closed in production.

#### Files to Modify

| File | Change |
|------|--------|
| `backend/app/auth.py` | Add jti uniqueness validation; add token binding (optional: bind to user-agent) |
| `backend/app/api/auth_routes.py` | Add audit logging for token operations; add max active sessions limit |

#### Test File: `backend/tests/test_sec_v7_sessions.py`

**Tests (20)**:

```
test_access_token_contains_required_claims
test_access_token_expires_at_configured_time
test_refresh_token_contains_required_claims
test_refresh_token_expires_at_configured_time
test_token_rotation_invalidates_old_refresh
test_revoked_refresh_token_cannot_be_reused
test_revoked_access_token_jti_rejected
test_bulk_revocation_invalidates_all_user_tokens
test_bulk_revocation_uses_iat_threshold
test_logout_revokes_refresh_token
test_logout_all_revokes_all_sessions
test_expired_access_token_returns_401
test_expired_refresh_token_returns_401
test_token_with_future_iat_rejected
test_token_with_missing_sub_rejected
test_token_with_missing_type_rejected
test_concurrent_refresh_only_one_succeeds
test_revocation_fails_closed_in_production
test_revocation_fails_open_in_development
test_regression_token_claims_structure_unchanged
```

---

### v1.3.8 — RBAC & Broken Access Control (IDOR)

**OWASP**: A01:2021 – Broken Access Control  
**Scope**: Test Insecure Direct Object Reference (IDOR) across all user-scoped endpoints. Verify User A cannot access User B's trades, alerts, price alerts, portfolio, or feedback.

**Risk Addressed**: User-scoped endpoints use `_user_trade_filter()`, `_user_config_filter()`, `_user_alert_filter()` which construct OR-based filters on `user_id` and `telegram_chat_id`. But `update_alert_config` takes a `config_id` path parameter — if the ownership check has a bypass, any user could modify another's config. The `delete_price_alert` endpoint needs IDOR testing. Admin endpoints only check for `internal_api_key` without role-based access.

#### Files to Modify

| File | Change |
|------|--------|
| `backend/app/api/alerts.py` | Strengthen ownership check — ensure 403 on non-owner access |
| `backend/app/api/price_alerts.py` | Add ownership check on DELETE endpoint |
| `backend/app/api/portfolio.py` | Add explicit IDOR guard on trade deletion (if added) |
| `backend/app/api/admin.py` | Add admin role to AuthContext; require "admin" role, not just API key |

#### Test File: `backend/tests/test_sec_v8_idor.py`

**Tests (22)**:

```
test_user_a_cannot_read_user_b_trades
test_user_a_cannot_read_user_b_alert_config
test_user_a_cannot_update_user_b_alert_config
test_user_a_cannot_delete_user_b_price_alert
test_user_a_cannot_read_user_b_price_alerts
test_user_a_cannot_read_user_b_portfolio_summary
test_user_a_cannot_read_user_b_signal_feedback
test_user_a_cannot_submit_feedback_as_user_b
test_user_a_cannot_share_signal_as_user_b
test_user_cannot_access_admin_revenue_without_key
test_user_cannot_access_admin_shadow_without_key
test_jwt_user_cannot_escalate_to_admin
test_free_tier_cannot_access_pro_ai_qa
test_free_tier_cannot_access_pro_backtest
test_pro_tier_can_access_pro_endpoints
test_config_id_guessing_returns_404_not_data
test_trade_id_guessing_returns_404_not_data
test_price_alert_id_guessing_returns_404_not_data
test_web_only_user_portfolio_access
test_web_only_user_watchlist_access
test_web_only_user_price_alerts_access
test_regression_idor_all_user_endpoints_tested
```

---

### v1.3.9 — Brute Force & Account Lockout

**OWASP**: A07:2021 – Identification and Authentication Failures  
**Scope**: Validate the account lockout mechanism works correctly. Test lockout bypass attempts, lockout timing, and recovery.

**Risk Addressed**: The `login` endpoint has lockout logic keyed by `{IP}:{email}`, but it depends on Redis. If Redis is down, lockout is bypassed entirely. The lockout key format could allow an attacker to learn valid emails by observing timing differences.

#### Files to Modify

| File | Change |
|------|--------|
| `backend/app/api/auth_routes.py` | Add constant-time response for invalid vs locked accounts; add lockout event logging |

#### Test File: `backend/tests/test_sec_v9_bruteforce.py`

**Tests (16)**:

```
test_lockout_after_max_failed_attempts
test_lockout_returns_429_with_retry_time
test_lockout_clears_on_successful_login
test_lockout_is_per_ip_per_email
test_different_ip_not_affected_by_lockout
test_lockout_duration_matches_config
test_failed_attempt_counter_expires
test_login_timing_constant_for_valid_vs_invalid_email
test_login_timing_constant_for_locked_vs_unlocked
test_lockout_survives_redis_reconnect
test_lockout_bypass_impossible_via_header_spoofing
test_concurrent_login_attempts_all_counted
test_lockout_key_no_email_enumeration
test_rate_limit_on_login_endpoint
test_rate_limit_on_register_endpoint
test_regression_lockout_constants_unchanged
```

---

### v1.3.10 — JWT Algorithm Attacks & Token Abuse

**OWASP**: A07:2021 – Identification and Authentication Failures  
**Scope**: Test JWT algorithm confusion (alg:none, RS256 with HS256 key), token forgery, claim tampering, and token replay attacks.

**Risk Addressed**: The `decode_jwt_token()` function specifies `algorithms=[settings.jwt_algorithm]`, which should prevent alg:none attacks. But this needs explicit testing. Token replay is partially mitigated by JTI revocation but needs testing. The WebSocket ticket system stores tickets with expiry but doesn't bind to IP.

#### Files to Modify

| File | Change |
|------|--------|
| `backend/app/auth.py` | Add explicit rejection of `alg: none`; add `require_iat` and `require_exp` to decode options |
| `backend/app/api/websocket.py` | Bind ticket to requesting IP; validate IP on WebSocket connect |

#### Test File: `backend/tests/test_sec_v10_jwtalgo.py`

**Tests (18)**:

```
test_alg_none_token_rejected
test_alg_none_uppercase_rejected
test_alg_none_mixed_case_rejected
test_alg_hs384_rejected_when_hs256_configured
test_alg_rs256_with_hs256_key_rejected
test_unsigned_token_rejected
test_token_with_tampered_sub_rejected
test_token_with_tampered_tier_rejected
test_token_with_tampered_exp_rejected
test_token_without_exp_rejected
test_token_without_iat_rejected
test_token_empty_string_rejected
test_token_malformed_base64_rejected
test_token_replay_with_revoked_jti
test_ws_ticket_bound_to_ip
test_ws_ticket_expired_rejected
test_ws_ticket_reuse_rejected
test_regression_jwt_algorithm_still_hs256
```

---

## Theme 3: API Security & Rate Limiting (v1.3.11–v1.3.15)

---

### v1.3.11 — Endpoint-Level Rate Limiting Validation

**OWASP**: A04:2021 – Insecure Design  
**Scope**: Verify every mutating endpoint has rate limiting. Map all endpoints to their rate limits and test that limits are enforced.

**Risk Addressed**: Rate limiting is disabled during tests (`TESTING=1`). This means no test ever validates that rate limits are configured correctly. Several read-only endpoints lack rate limits that could enable data scraping.

#### Files to Modify

| File | Change |
|------|--------|
| `backend/app/api/signals.py` | Add rate limit on list endpoint (60/min) |
| `backend/app/api/news.py` | Add rate limit on list endpoints |
| `backend/app/api/seo.py` | Add rate limit on public SEO endpoints |
| `backend/app/api/sharing.py` | Add rate limit on shared signal view (30/min) |

#### Test File: `backend/tests/test_sec_v11_ratelimit.py`

**Tests (16)**:

```
test_login_rate_limit_is_10_per_minute
test_register_rate_limit_is_5_per_minute
test_refresh_rate_limit_is_20_per_minute
test_ai_qa_rate_limit_is_5_per_minute
test_backtest_rate_limit_is_3_per_hour
test_trial_rate_limit_is_3_per_day
test_subscribe_rate_limit_is_5_per_hour
test_share_signal_rate_limit_is_10_per_minute
test_log_trade_rate_limit_is_30_per_minute
test_create_price_alert_rate_limit_is_10_per_minute
test_create_alert_config_rate_limit_is_10_per_minute
test_signals_list_rate_limited
test_news_list_rate_limited
test_seo_rate_limited
test_rate_limit_returns_429_not_500
test_regression_all_post_put_delete_endpoints_rate_limited
```

Note: Tests in this iteration must temporarily enable rate limiting by patching `limiter.enabled = True`.

---

### v1.3.12 — Request Size & Payload Abuse

**OWASP**: A04:2021 – Insecure Design  
**Scope**: Test request body size limits, deeply nested JSON, excessively large arrays, and parameter pollution.

**Risk Addressed**: The 1MB body limiter checks Content-Length header, but an attacker could send chunked transfer encoding without Content-Length. Deeply nested JSON could cause parsing delays.

#### Files to Modify

| File | Change |
|------|--------|
| `backend/app/main.py` | Add chunked body reading with size tracking; add JSON depth limit |
| `backend/app/api/portfolio.py` | Add max quantity/price bounds |
| `backend/app/api/alerts.py` | Add maximum watchlist size |

#### Test File: `backend/tests/test_sec_v12_payloads.py`

**Tests (16)**:

```
test_body_over_1mb_returns_413
test_body_exactly_1mb_accepted
test_body_content_length_header_checked
test_deeply_nested_json_100_levels_rejected
test_deeply_nested_json_10_levels_accepted
test_array_with_10000_items_rejected
test_parameter_pollution_duplicate_keys
test_null_byte_in_body_handled
test_unicode_bom_in_body_handled
test_non_json_content_type_with_json_body
test_empty_body_on_post_endpoint
test_trade_quantity_max_bound_enforced
test_trade_price_max_bound_enforced
test_watchlist_max_size_enforced
test_signal_types_array_max_size_enforced
test_regression_max_request_body_bytes_is_1mb
```

---

### v1.3.13 — CORS Policy Validation

**OWASP**: A05:2021 – Security Misconfiguration  
**Scope**: Validate CORS headers across all environments. Test that production CORS blocks unauthorized origins. Test preflight (OPTIONS) handling.

**Risk Addressed**: In development mode, CORS allows a regex matching local IPs and `.local` hostnames. This is fine for dev but must not leak to production. No test verifies that production CORS is strict.

#### Files to Modify

| File | Change |
|------|--------|
| `backend/app/main.py` | Add validation: ensure `_cors_origins_regex` is None in production |

#### Test File: `backend/tests/test_sec_v13_cors.py`

**Tests (15)**:

```
test_cors_allows_configured_frontend_url
test_cors_blocks_unknown_origin_in_production
test_cors_allows_localhost_3000_in_development
test_cors_development_regex_allows_local_network
test_cors_production_has_no_regex
test_cors_preflight_returns_correct_headers
test_cors_allows_required_methods_only
test_cors_allows_required_headers_only
test_cors_credentials_header_present
test_cors_no_wildcard_origin_in_production
test_cors_blocks_null_origin
test_cors_blocks_crafted_subdomain
test_cors_blocks_similar_looking_domain
test_cors_max_age_is_reasonable
test_regression_cors_origins_not_wildcard
```

---

### v1.3.14 — API Versioning & Deprecation Safety

**OWASP**: A05:2021 – Security Misconfiguration  
**Scope**: Verify API version prefix is enforced. Test that unversioned paths are rejected. Ensure no shadow/debug endpoints are exposed.

**Risk Addressed**: All API routes are under `/api/v1/`, but the `/health` and `/metrics` endpoints are at root level. The `/metrics` endpoint has access control but could leak system info. WebSocket endpoint is at `/ws/signals` — outside the versioned prefix.

#### Files to Modify

| File | Change |
|------|--------|
| `backend/app/main.py` | Add `X-API-Version` response header; add deprecation warning middleware for future v2 |

#### Test File: `backend/tests/test_sec_v14_versioning.py`

**Tests (15)**:

```
test_all_api_routes_under_v1_prefix
test_unversioned_api_path_returns_404
test_health_endpoint_no_sensitive_info
test_health_endpoint_db_error_no_leak
test_metrics_endpoint_requires_auth_or_local
test_metrics_endpoint_blocked_from_public_ip
test_no_debug_endpoints_exposed
test_no_swagger_ui_in_production
test_no_redoc_in_production
test_websocket_endpoint_exists
test_api_version_header_present
test_no_internal_routes_publicly_accessible
test_router_prefix_consistency
test_public_routes_are_only_auth_and_seo_and_shared
test_regression_endpoint_count_unchanged
```

---

### v1.3.15 — Error Information Leakage

**OWASP**: A05:2021 – Security Misconfiguration  
**Scope**: Ensure error responses never leak stack traces, internal paths, database schema names, or technology versions. Test the global exception handler.

**Risk Addressed**: The global exception handler returns `{"detail": "Internal server error"}` — this is correct. But Pydantic validation errors (422) return detailed field-level error messages that could reveal internal schema structure. The admin shadow-mode endpoint returns `str(e)` on error, which leaks exception details.

#### Files to Modify

| File | Change |
|------|--------|
| `backend/app/api/admin.py` | Stop returning `str(e)` in shadow-mode error response |
| `backend/app/main.py` | Add custom 422 handler that strips internal field names from validation errors |

#### Test File: `backend/tests/test_sec_v15_errorleak.py`

**Tests (18)**:

```
test_500_error_no_stack_trace
test_500_error_no_file_paths
test_500_error_no_module_names
test_422_validation_error_no_internal_schema
test_422_error_structure_is_safe
test_404_error_no_table_names
test_401_error_no_token_details
test_403_error_no_role_details
test_admin_shadow_error_no_exception_leak
test_database_error_no_sql_leak
test_redis_error_no_connection_string_leak
test_anthropic_api_error_no_key_leak
test_health_endpoint_no_version_leak_in_error
test_metrics_denied_no_detail_leak
test_unhandled_exception_returns_generic_500
test_server_header_no_version_info
test_pydantic_error_no_internal_field_names
test_regression_global_exception_handler_active
```

---

## Theme 4: Data Protection & Cryptography (v1.3.16–v1.3.20)

---

### v1.3.16 — PII Handling & Data Minimization

**OWASP**: A02:2021 – Cryptographic Failures  
**Scope**: Audit all PII storage and ensure data minimization. Email addresses, Telegram chat IDs, IP addresses in logs should be handled appropriately. Verify account deletion truly removes all PII.

**Risk Addressed**: The `delete_account` endpoint deletes user, tokens, configs, alerts, and trades, but does NOT delete `SignalFeedback` records or `SignalShare` records that reference the user. Structured logging may log email addresses or chat IDs.

#### Files to Modify

| File | Change |
|------|--------|
| `backend/app/api/auth_routes.py` | Add deletion of `SignalFeedback` and `SignalShare` records in account deletion |
| `backend/app/main.py` | Add PII redaction in structured log context (mask email, truncate IPs for GDPR) |
| `backend/app/api/auth_routes.py` | Mask email in login error logs |

#### Test File: `backend/tests/test_sec_v16_pii.py`

**Tests (16)**:

```
test_account_deletion_removes_user
test_account_deletion_removes_refresh_tokens
test_account_deletion_removes_alert_configs
test_account_deletion_removes_price_alerts
test_account_deletion_removes_trades
test_account_deletion_removes_signal_feedback
test_account_deletion_removes_signal_shares
test_account_deletion_is_complete_no_orphans
test_profile_response_no_password_hash
test_profile_response_no_internal_ids
test_shared_signal_no_creator_pii
test_login_error_log_no_raw_email
test_register_error_log_no_raw_password
test_api_responses_no_database_ids_as_integers
test_user_list_endpoint_does_not_exist
test_regression_pii_fields_not_in_logs
```

---

### v1.3.17 — Encryption & Secure Transport

**OWASP**: A02:2021 – Cryptographic Failures  
**Scope**: Verify all sensitive data at rest and in transit is properly encrypted. Test HSTS, TLS-only cookies, JWT signing strength.

**Risk Addressed**: HSTS is only added in production. JWT uses HS256 with a configurable secret — if the secret is too short, brute force is feasible. Refresh tokens are stored as SHA-256 hashes (no salt). The `api_secret_key` is compared with `hmac.compare_digest` (good) but there's no minimum length enforcement.

#### Files to Modify

| File | Change |
|------|--------|
| `backend/app/main.py` | Enforce minimum API_SECRET_KEY length (32 chars) in production |
| `backend/app/config.py` | Add validator for minimum secret lengths |

#### Test File: `backend/tests/test_sec_v17_crypto.py`

**Tests (16)**:

```
test_hsts_header_present_in_production
test_hsts_max_age_at_least_one_year
test_hsts_includes_subdomains
test_jwt_secret_min_length_enforced_in_production
test_jwt_algorithm_is_hs256
test_jwt_rejects_weak_secret_in_production
test_api_secret_key_min_length_enforced
test_bcrypt_cost_factor_is_adequate
test_refresh_token_stored_as_hash
test_refresh_token_hash_is_sha256
test_password_hash_not_reversible
test_api_key_comparison_is_constant_time
test_webhook_signature_comparison_is_constant_time
test_razorpay_webhook_uses_hmac_sha256
test_ws_ticket_uses_secure_random
test_regression_crypto_algorithms_unchanged
```

---

### v1.3.18 — Security Headers Comprehensive Validation

**OWASP**: A05:2021 – Security Misconfiguration  
**Scope**: Validate every security header is present and correctly configured across all response types (HTML, JSON, WebSocket upgrade, error responses).

**Risk Addressed**: Headers are set in middleware, but need to verify they appear on ALL responses including error responses (4xx, 5xx), redirect responses, and OPTIONS preflight responses.

#### Files to Modify

| File | Change |
|------|--------|
| `backend/app/main.py` | Ensure headers are added even on error responses; add `X-DNS-Prefetch-Control: off` |

#### Test File: `backend/tests/test_sec_v18_headers.py`

**Tests (18)**:

```
test_x_content_type_options_nosniff
test_x_frame_options_deny
test_referrer_policy_strict_origin
test_permissions_policy_restrictive
test_csp_default_src_self
test_csp_script_src_self
test_csp_frame_ancestors_none
test_csp_object_src_none
test_csp_base_uri_self
test_csp_connect_src_includes_frontend
test_security_headers_on_404_response
test_security_headers_on_422_response
test_security_headers_on_500_response
test_security_headers_on_health_endpoint
test_no_server_header_version_leak
test_x_robots_tag_on_shared_signals
test_x_dns_prefetch_control_off
test_regression_all_security_headers_present
```

---

### v1.3.19 — Cookie Security & Frontend State

**OWASP**: A07:2021 – Identification and Authentication Failures  
**Scope**: Verify the frontend stores tokens securely. Test that `sessionStorage` is used (not `localStorage`), tokens aren't leaked in URLs, and the NextAuth session is properly secured.

**Risk Addressed**: The frontend stores JWT tokens in `sessionStorage` (good — cleared on tab close). But NextAuth also maintains its own session with `strategy: 'jwt'`. Both token stores need to stay synchronized. If `NEXTAUTH_SECRET` is weak, session tokens can be forged.

#### Files to Modify

| File | Change |
|------|--------|
| `frontend/src/lib/api.ts` | Add token validation before use (check expiry client-side) |
| `frontend/src/lib/auth.ts` | Add minimum NEXTAUTH_SECRET length check |

#### Frontend Test File: `frontend/src/__tests__/security-cookies.test.ts`

**Tests (16)**:

```
test_tokens_stored_in_session_storage_not_local
test_tokens_not_in_url_params
test_tokens_not_in_url_hash
test_token_cleared_on_logout
test_token_cleared_on_401_response
test_refresh_token_not_sent_on_regular_requests
test_authorization_header_format_bearer
test_no_tokens_in_console_log
test_api_fetch_retries_on_401_once_only
test_concurrent_refresh_deduplicated
test_nextauth_session_strategy_is_jwt
test_nextauth_max_age_is_7_days
test_nextauth_secret_configured
test_session_sync_clears_on_signout
test_api_client_no_credentials_include_on_cross_origin
test_regression_token_storage_mechanism_unchanged
```

---

### v1.3.20 — Secrets Management & Config Hardening

**OWASP**: A05:2021 – Security Misconfiguration  
**Scope**: Verify all secrets are loaded from environment variables, never hardcoded. Test startup validation for required secrets. Ensure `.env.example` doesn't contain real values.

**Risk Addressed**: The `lifespan()` function validates `DATABASE_URL`, `JWT_SECRET_KEY`, and `API_SECRET_KEY` in production, but doesn't validate `ANTHROPIC_API_KEY`, `TELEGRAM_BOT_TOKEN`, or `RAZORPAY_WEBHOOK_SECRET`. Missing these causes runtime errors, not startup errors.

#### Files to Modify

| File | Change |
|------|--------|
| `backend/app/main.py` | Add startup warnings for missing optional secrets (non-blocking but logged) |
| `backend/app/config.py` | Add `@field_validator` for secret format validation |

#### Test File: `backend/tests/test_sec_v20_secrets.py`

**Tests (16)**:

```
test_no_hardcoded_secrets_in_source_code
test_no_api_keys_in_source_code
test_no_passwords_in_source_code
test_env_example_has_no_real_values
test_settings_loads_from_env_vars
test_production_requires_database_url
test_production_requires_jwt_secret
test_production_requires_api_secret
test_production_warns_missing_anthropic_key
test_production_warns_missing_telegram_token
test_jwt_secret_min_32_chars_in_production
test_default_values_are_safe
test_redis_url_has_safe_default
test_environment_default_is_development
test_sentry_dsn_not_required
test_regression_required_secrets_list_unchanged
```

---

## Theme 5: Test Coverage Expansion (v1.3.21–v1.3.25)

---

### v1.3.21 — Edge Cases in Signal Pipeline

**OWASP**: N/A (Quality & Correctness)  
**Scope**: Test edge cases in the signal generation pipeline: empty market data, all-NaN indicators, extreme price values, zero volume, boundary confidence scores, Decimal overflow.

**Risk Addressed**: The signal pipeline processes financial data where edge cases can cause silent data corruption. Decimal overflow, NaN propagation in technical indicators, and boundary confidence values (0, 100, 101) need explicit testing.

#### Files to Modify

| File | Change |
|------|--------|
| `backend/app/services/signal_gen/scorer.py` | Add bounds checking for final confidence (clamp 0-100) |
| `backend/app/services/signal_gen/targets.py` | Add guard for zero ATR value |
| `backend/app/services/analysis/indicators.py` | Add NaN propagation guards |

#### Test File: `backend/tests/test_sec_v21_pipeline_edge.py`

**Tests (20)**:

```
test_scorer_empty_technical_data
test_scorer_all_nan_indicators
test_scorer_confidence_clamped_at_0
test_scorer_confidence_clamped_at_100
test_scorer_boundary_65_is_buy
test_scorer_boundary_64_is_hold
test_scorer_boundary_80_is_strong_buy
test_scorer_boundary_35_is_hold
test_scorer_boundary_20_is_strong_sell
test_targets_zero_atr_no_crash
test_targets_negative_atr_rejected
test_targets_extreme_price_decimal_precision
test_targets_rr_ratio_always_gte_1_to_2
test_indicators_all_zero_volume
test_indicators_single_candle_no_crash
test_indicators_nan_close_prices
test_generator_no_market_data_skips_symbol
test_generator_stale_data_skips_symbol
test_signal_type_thresholds_match_spec
test_regression_scoring_weights_unchanged
```

---

### v1.3.22 — Concurrency & Race Conditions

**OWASP**: A04:2021 – Insecure Design  
**Scope**: Test concurrent operations that could cause data inconsistency: simultaneous signal resolution, double trade logging, concurrent token refresh, parallel price alert creation.

**Risk Addressed**: Signal resolution uses `FOR UPDATE SKIP LOCKED` but this hasn't been tested with actual concurrent database operations. Token refresh rotation could allow double-spend of a refresh token in a race condition. Price alert creation has a count-then-insert pattern vulnerable to TOCTOU.

#### Files to Modify

| File | Change |
|------|--------|
| `backend/app/api/price_alerts.py` | Use `SELECT ... FOR UPDATE` on count query to prevent TOCTOU race |
| `backend/app/api/auth_routes.py` | Use `SELECT ... FOR UPDATE` on refresh token to prevent double-use |

#### Test File: `backend/tests/test_sec_v22_concurrency.py`

**Tests (18)**:

```
test_concurrent_signal_resolution_no_duplicate_history
test_concurrent_trade_creation_all_succeed
test_concurrent_token_refresh_only_one_succeeds
test_concurrent_price_alert_creation_respects_limit
test_concurrent_alert_config_creation_no_duplicates
test_concurrent_watchlist_updates_consistent
test_concurrent_feedback_submission_no_duplicates
test_concurrent_account_deletion_no_error
test_concurrent_password_change_last_wins
test_concurrent_share_creation_all_unique
test_signal_for_update_skip_locked_present
test_cooldown_for_update_present
test_price_alert_atomic_trigger_present
test_refresh_token_rotation_atomic
test_subscription_creation_no_double_trial
test_concurrent_registration_same_email_only_one
test_database_connection_pool_under_load
test_regression_for_update_patterns_unchanged
```

---

### v1.3.23 — Integration & End-to-End Security Flows

**OWASP**: N/A (Integration Testing)  
**Scope**: Test complete security-relevant user flows: register → login → use API → refresh → logout. Test the full authentication chain without dependency overrides. Test WebSocket auth ticket flow end-to-end.

**Risk Addressed**: Most tests override `require_auth` / `get_current_user` with mocks, so the actual JWT verification path is never tested through the API layer. This iteration adds tests that exercise the real auth middleware.

#### Files to Modify

No code changes — only new integration tests.

#### Test File: `backend/tests/test_sec_v23_e2e.py`

**Tests (20)**:

```
test_e2e_register_login_access_protected_endpoint
test_e2e_register_login_refresh_access
test_e2e_register_login_logout_cannot_access
test_e2e_register_login_change_password_login_new
test_e2e_register_delete_account_cannot_login
test_e2e_register_duplicate_email_fails
test_e2e_login_wrong_password_fails
test_e2e_token_expires_gets_401
test_e2e_refresh_token_rotation_old_invalid
test_e2e_logout_all_invalidates_sessions
test_e2e_free_tier_blocked_from_pro_endpoint
test_e2e_api_key_access_to_signals
test_e2e_api_key_rejected_for_user_endpoints
test_e2e_ws_ticket_flow_auth_to_connect
test_e2e_webhook_invalid_signature_rejected
test_e2e_webhook_valid_signature_accepted
test_e2e_shared_signal_no_auth_required
test_e2e_seo_pages_no_auth_required
test_e2e_health_endpoint_no_auth
test_regression_e2e_auth_flow_unchanged
```

---

### v1.3.24 — Negative Testing & Boundary Values

**OWASP**: N/A (Quality & Robustness)  
**Scope**: Systematically test all API endpoints with invalid, missing, and boundary inputs. Verify proper error codes and messages for every failure mode.

**Risk Addressed**: Many endpoints are only tested with valid inputs. Invalid enum values, negative numbers, empty strings, extremely long strings, missing required fields, and wrong data types need systematic testing.

#### Test File: `backend/tests/test_sec_v24_negative.py`

**Tests (20)**:

```
test_signals_negative_confidence_rejected
test_signals_confidence_over_100_rejected
test_signals_limit_0_rejected
test_signals_limit_101_rejected
test_signals_offset_negative_rejected
test_signals_invalid_market_type_returns_empty
test_signals_invalid_signal_type_returns_empty
test_history_negative_limit
test_history_offset_negative
test_portfolio_trade_negative_quantity
test_portfolio_trade_zero_price
test_portfolio_trade_invalid_side
test_portfolio_trade_missing_required_fields
test_price_alert_invalid_condition
test_price_alert_negative_threshold
test_backtest_days_0_rejected
test_backtest_days_over_365_rejected
test_ai_qa_empty_symbol_rejected
test_ai_qa_empty_question_rejected
test_regression_all_endpoints_return_proper_error_codes
```

---

### v1.3.25 — Chaos & Fault Injection

**OWASP**: N/A (Resilience Testing)  
**Scope**: Test system behavior when external dependencies fail: database down, Redis down, Claude API down, Binance/Alpha Vantage down. Verify graceful degradation, proper error messages, and no data corruption.

**Risk Addressed**: The circuit breaker exists for external APIs, but behavior under cascading failures hasn't been tested. If the database connection pool is exhausted, what happens? If Redis is down during token revocation check, does production fail closed?

#### Files to Modify

| File | Change |
|------|--------|
| `backend/app/services/circuit_breaker.py` | Add test hooks for simulating failures |

#### Test File: `backend/tests/test_sec_v25_chaos.py`

**Tests (18)**:

```
test_database_connection_timeout_returns_500
test_database_pool_exhaustion_returns_503
test_redis_down_token_revocation_fails_closed_prod
test_redis_down_token_revocation_fails_open_dev
test_redis_down_circuit_breaker_bypasses_gracefully
test_redis_down_lockout_bypassed_but_login_works
test_redis_down_rate_limiting_still_works
test_claude_api_down_signal_gen_fallback
test_claude_api_budget_exhausted_fallback
test_claude_api_timeout_returns_fallback
test_binance_api_down_circuit_opens
test_alpha_vantage_down_circuit_opens
test_circuit_breaker_half_open_test_call
test_circuit_breaker_recovery_after_success
test_all_external_apis_down_health_degraded
test_partial_failure_other_markets_continue
test_celery_task_retry_on_transient_failure
test_regression_circuit_breaker_thresholds_unchanged
```

---

## Cumulative Test Count Projection

| Version | New Tests | Cumulative Backend | Cumulative Frontend |
|---------|-----------|-------------------|-------------------|
| Baseline | — | 1,263 | 741 |
| v1.3.1 | 20 | 1,283 | 741 |
| v1.3.2 | 18 + 5 FE | 1,301 | 746 |
| v1.3.3 | 16 | 1,317 | 746 |
| v1.3.4 | 16 | 1,333 | 746 |
| v1.3.5 | 18 | 1,351 | 746 |
| v1.3.6 | 18 | 1,369 | 746 |
| v1.3.7 | 20 | 1,389 | 746 |
| v1.3.8 | 22 | 1,411 | 746 |
| v1.3.9 | 16 | 1,427 | 746 |
| v1.3.10 | 18 | 1,445 | 746 |
| v1.3.11 | 16 | 1,461 | 746 |
| v1.3.12 | 16 | 1,477 | 746 |
| v1.3.13 | 15 | 1,492 | 746 |
| v1.3.14 | 15 | 1,507 | 746 |
| v1.3.15 | 18 | 1,525 | 746 |
| v1.3.16 | 16 | 1,541 | 746 |
| v1.3.17 | 16 | 1,557 | 746 |
| v1.3.18 | 18 | 1,575 | 746 |
| v1.3.19 | 0 + 16 FE | 1,575 | 762 |
| v1.3.20 | 16 | 1,591 | 762 |
| v1.3.21 | 20 | 1,611 | 762 |
| v1.3.22 | 18 | 1,629 | 762 |
| v1.3.23 | 20 | 1,649 | 762 |
| v1.3.24 | 20 | 1,669 | 762 |
| v1.3.25 | 18 | 1,687 | 762 |
| **Final** | **~445** | **~1,687** | **~762** |

---

## File Naming Convention

All new test files follow the pattern:

```
backend/tests/test_sec_v{N}_{topic}.py
```

Where `{N}` is 1–25 and `{topic}` is a short kebab-case descriptor:

| File | Iteration |
|------|-----------|
| `test_sec_v1_sqli.py` | v1.3.1 |
| `test_sec_v2_xss.py` | v1.3.2 |
| `test_sec_v3_cmdinject.py` | v1.3.3 |
| `test_sec_v4_pathtraversal.py` | v1.3.4 |
| `test_sec_v5_ssrf.py` | v1.3.5 |
| `test_sec_v6_passwords.py` | v1.3.6 |
| `test_sec_v7_sessions.py` | v1.3.7 |
| `test_sec_v8_idor.py` | v1.3.8 |
| `test_sec_v9_bruteforce.py` | v1.3.9 |
| `test_sec_v10_jwtalgo.py` | v1.3.10 |
| `test_sec_v11_ratelimit.py` | v1.3.11 |
| `test_sec_v12_payloads.py` | v1.3.12 |
| `test_sec_v13_cors.py` | v1.3.13 |
| `test_sec_v14_versioning.py` | v1.3.14 |
| `test_sec_v15_errorleak.py` | v1.3.15 |
| `test_sec_v16_pii.py` | v1.3.16 |
| `test_sec_v17_crypto.py` | v1.3.17 |
| `test_sec_v18_headers.py` | v1.3.18 |
| `test_sec_v19_cookies.py` | v1.3.19 (frontend) |
| `test_sec_v20_secrets.py` | v1.3.20 |
| `test_sec_v21_pipeline_edge.py` | v1.3.21 |
| `test_sec_v22_concurrency.py` | v1.3.22 |
| `test_sec_v23_e2e.py` | v1.3.23 |
| `test_sec_v24_negative.py` | v1.3.24 |
| `test_sec_v25_chaos.py` | v1.3.25 |

Frontend test files:

| File | Iteration |
|------|-----------|
| `frontend/src/__tests__/security-xss.test.ts` | v1.3.2 |
| `frontend/src/__tests__/security-cookies.test.ts` | v1.3.19 |

---

## Regression Guard Strategy

Every iteration includes at least one `test_regression_*` test that verifies the security fix from that iteration hasn't been reverted. These tests should:

1. **Check source code patterns** (e.g., `assert "with_for_update" in source`) for structural invariants
2. **Replay known-bad inputs** from earlier iterations to ensure protections persist
3. **Validate configuration values** haven't been weakened (e.g., secret lengths, rate limits)

All 25 regression tests should be runnable as a standalone suite:

```bash
pytest tests/ -k "test_regression" -v
```

---

## Priority & Risk Matrix

| Priority | Iterations | Why |
|----------|-----------|-----|
| P0 — Critical | v1.3.8 (IDOR), v1.3.10 (JWT alg), v1.3.5 (SSRF) | Direct access control bypass; exploitation = data breach |
| P1 — High | v1.3.1 (SQLi), v1.3.7 (Sessions), v1.3.15 (Error leak), v1.3.22 (Concurrency) | Exploitation = data exposure or corruption |
| P2 — Medium | v1.3.2 (XSS), v1.3.6 (Passwords), v1.3.9 (Brute force), v1.3.16 (PII), v1.3.17 (Crypto) | Exploitation = user harm, compliance risk |
| P3 — Low | v1.3.3, v1.3.4, v1.3.11–v1.3.14, v1.3.18–v1.3.20 | Defense-in-depth, best practices |
| P4 — Quality | v1.3.21, v1.3.23–v1.3.25 | Robustness & reliability |

**Recommended implementation order** (by risk, not version number):

1. v1.3.8 → v1.3.10 → v1.3.5 (P0 Critical)
2. v1.3.1 → v1.3.7 → v1.3.15 → v1.3.22 (P1 High)
3. v1.3.2 → v1.3.6 → v1.3.9 → v1.3.16 → v1.3.17 (P2 Medium)
4. Remaining iterations in version order

---

## Dependencies & Prerequisites

- **All iterations**: Require `pytest`, `pytest-asyncio`, `httpx` (already in `requirements.txt`)
- **v1.3.2 (XSS)**: May need `bleach` package for HTML sanitization
- **v1.3.5 (SSRF)**: May need `ipaddress` stdlib module for IP range validation
- **v1.3.11 (Rate limiting)**: Tests must temporarily enable rate limiting by patching `limiter.enabled`
- **v1.3.22 (Concurrency)**: Requires `asyncio.gather` for parallel test execution
- **v1.3.23 (E2E)**: Tests must NOT use dependency overrides — exercise real auth middleware

---

## Acceptance Criteria (Per Iteration)

Each iteration is complete when:

1. All new tests pass: `pytest tests/test_sec_v{N}_*.py -v`
2. All existing tests still pass: `pytest tests/ -v --override-ini="asyncio_mode=auto"`
3. No new lint warnings: `ruff check backend/`
4. Docker build succeeds: `docker compose build`
5. The regression test for that iteration passes independently
6. Code changes are committed with: `fix(security): v1.3.{N} — {title}`

---

*End of specification.*
