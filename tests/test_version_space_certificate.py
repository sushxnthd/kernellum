import hashlib
import json

from kernellum.discovery.version_space_certificate import issue_envelope_certificate, verify_provenance


def provenance():
    raw = json.dumps({
        "schema": "kernellum.hypothesis-class-provenance.v1",
        "hypothesis_class": "bounded-demo-class",
        "request_scope": "demo-request",
    }, sort_keys=True).encode()
    return verify_provenance(raw, hashlib.sha256(raw).hexdigest(), lambda payload: True)


def test_missing_provenance_refuses():
    result = issue_envelope_certificate([[0.0, 1.0], [1.0, 2.0]], [0.5, 1.5], scale=1, tolerance=1, provenance=None)
    assert result == {"schema": "kernellum.envelope-decision.v1", "decision": "refuse", "reason": "missing_verified_hypothesis_class_provenance"}


def test_conditional_bound_and_wide_refusal():
    verified = provenance()
    passed = issue_envelope_certificate([[0.0, 1.0], [1.0, 3.0]], [0.5, 2.0], scale=2, tolerance=0.6, provenance=verified)
    assert passed["decision"] == "certify_conditional"
    assert passed["normalized_rmse_upper_bound"] <= 0.6
    failed = issue_envelope_certificate([[0.0, 1.0], [1.0, 3.0]], [0.5, 2.0], scale=2, tolerance=0.39, provenance=verified)
    assert failed["reason"] == "conditional_bound_exceeds_tolerance"


def test_provenance_integrity_and_external_gate():
    raw = b'{"schema":"kernellum.hypothesis-class-provenance.v1","hypothesis_class":"h","request_scope":"q"}'
    digest = hashlib.sha256(raw).hexdigest()
    try:
        verify_provenance(raw, "0" * 64, lambda payload: True)
        assert False
    except ValueError as error:
        assert "digest" in str(error)
    try:
        verify_provenance(raw, digest, lambda payload: False)
        assert False
    except ValueError as error:
        assert "rejected" in str(error)

