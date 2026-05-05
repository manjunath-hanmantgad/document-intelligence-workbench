# Graph Report - mj-projects-new  (2026-05-04)

## Corpus Check
- 53 files · ~42,421 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 229 nodes · 372 edges · 15 communities detected
- Extraction: 70% EXTRACTED · 30% INFERRED · 0% AMBIGUOUS · INFERRED: 110 edges (avg confidence: 0.76)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]

## God Nodes (most connected - your core abstractions)
1. `Base` - 15 edges
2. `seed_demo_workspace()` - 13 edges
3. `get_settings()` - 11 edges
4. `write_audit_log()` - 9 edges
5. `register()` - 7 edges
6. `get_connection()` - 7 edges
7. `evaluate_log()` - 7 edges
8. `Project` - 6 edges
9. `AlertRule` - 6 edges
10. `evaluate_alert_rules()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `AlertRule` --calls--> `alert_rules_view()`  [INFERRED]
  observatory/models.py → dashboard/app.py
- `Project` --calls--> `projects_view()`  [INFERRED]
  observatory/models.py → dashboard/app.py
- `make_engine()` --calls--> `get_settings()`  [INFERRED]
  observatory/database.py → shared/config.py
- `init_platform_db()` --calls--> `main()`  [INFERRED]
  observatory/database.py → workers/alert_worker.py
- `create_access_token()` --calls--> `get_settings()`  [INFERRED]
  observatory/security.py → shared/config.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.11
Nodes (29): BaseModel, ChatMessage, ChatRequest, AlertRuleCreate, AlertRuleRead, ApiKeyCreate, ApiKeyCreateResponse, ApiKeyRead (+21 more)

### Community 1 - "Community 1"
Cohesion: 0.21
Nodes (20): Base, DeclarativeBase, Base, _seed_alerts(), _seed_calls(), seed_demo_workspace(), AlertRule, ApiKey (+12 more)

### Community 2 - "Community 2"
Cohesion: 0.12
Nodes (17): auth_screen(), set_auth(), write_audit_log(), TokenResponse, create_access_token(), generate_api_key(), hash_api_key(), hash_password() (+9 more)

### Community 3 - "Community 3"
Cohesion: 0.16
Nodes (11): build_alerts(), send_alerts(), validate_optional_bearer_token(), get_settings(), require_provider_credentials(), Settings, estimate_tokens(), get_llm_client() (+3 more)

### Community 4 - "Community 4"
Cohesion: 0.2
Nodes (15): seed(), clamp(), evaluate_log(), EvaluationResult, extract_question(), heuristic_evaluate(), persist_evaluation(), run() (+7 more)

### Community 5 - "Community 5"
Cohesion: 0.2
Nodes (14): alert_rules_view(), api_keys_view(), calls_dataframe(), current_context(), evaluations_dataframe(), evaluations_view(), org_endpoints(), org_projects() (+6 more)

### Community 6 - "Community 6"
Cohesion: 0.14
Nodes (8): calculate_cost(), chat(), stats_summary(), ChatResponse, setup_logger(), track_event(), test_known_model_cost(), test_mock_model_is_free()

### Community 7 - "Community 7"
Cohesion: 0.22
Nodes (7): _connect_args(), init_platform_db(), make_engine(), stamp_initial_revision_if_needed(), reset_demo_workspace(), test_seed_demo_workspace_creates_customer_demo_data(), main()

### Community 8 - "Community 8"
Cohesion: 0.22
Nodes (6): evaluate_alert_rules(), has_recent_open_incident(), metric_value(), create_alert_rule(), evaluate_rules_now(), main()

### Community 9 - "Community 9"
Cohesion: 0.24
Nodes (8): get_api_key_context(), get_current_user(), require_engineer(), require_owner_or_admin(), ensure_role(), Role, decode_access_token(), StrEnum

### Community 10 - "Community 10"
Cohesion: 0.27
Nodes (6): create_evaluation_job(), run_evaluation_job(), run_queued_jobs(), score_call(), queue_evaluation_job(), run_job_now()

### Community 11 - "Community 11"
Cohesion: 0.33
Nodes (3): register_user(), test_register_create_project_api_key_ingest_and_metrics(), test_llm_calls_and_trace_detail_endpoints()

### Community 12 - "Community 12"
Cohesion: 0.83
Nodes (3): database_url(), run_migrations_offline(), run_migrations_online()

### Community 13 - "Community 13"
Cohesion: 0.5
Nodes (1): enterprise foundation  Revision ID: 0001_enterprise_foundation Revises: Create D

### Community 14 - "Community 14"
Cohesion: 0.83
Nodes (3): test_alert_rule_creates_incident_and_suppresses_duplicate(), test_evaluation_job_scores_ingested_calls(), _workspace()

## Knowledge Gaps
- **1 isolated node(s):** `enterprise foundation  Revision ID: 0001_enterprise_foundation Revises: Create D`
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 13`** (4 nodes): `0001_enterprise_foundation.py`, `downgrade()`, `enterprise foundation  Revision ID: 0001_enterprise_foundation Revises: Create D`, `upgrade()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_settings()` connect `Community 3` to `Community 9`, `Community 2`, `Community 6`, `Community 7`?**
  _High betweenness centrality (0.168) - this node is a cross-community bridge._
- **Why does `chat()` connect `Community 6` to `Community 3`, `Community 4`?**
  _High betweenness centrality (0.127) - this node is a cross-community bridge._
- **Why does `seed_demo_workspace()` connect `Community 1` to `Community 2`, `Community 7`?**
  _High betweenness centrality (0.117) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `Base` (e.g. with `Organization` and `User`) actually correct?**
  _`Base` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `seed_demo_workspace()` (e.g. with `Organization` and `User`) actually correct?**
  _`seed_demo_workspace()` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `get_settings()` (e.g. with `make_engine()` and `create_access_token()`) actually correct?**
  _`get_settings()` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `enterprise foundation  Revision ID: 0001_enterprise_foundation Revises: Create D` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._