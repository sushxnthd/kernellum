from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

import pytest


def _load_packager():
    path = Path(__file__).resolve().parents[1] / "scripts" / "package_krn_hw_001_kit.py"
    spec = importlib.util.spec_from_file_location("package_krn_hw_001_kit", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_verify_and_deterministic_zip(tmp_path: Path) -> None:
    packager = _load_packager()
    bitstream = tmp_path / "reference.bit"
    bitstream.write_bytes(b"deterministic-test-bitstream")
    expected_sha256 = hashlib.sha256(bitstream.read_bytes()).hexdigest()

    kit_a = tmp_path / "a" / "kit"
    kit_b = tmp_path / "b" / "kit"
    zip_a = tmp_path / "kit-a.zip"
    zip_b = tmp_path / "kit-b.zip"
    kwargs = {
        "bitstream": bitstream,
        "source_commit": "0123456789abcdef",
        "workflow_run": "test-run",
        "expected_sha256": expected_sha256,
    }
    packager.build_kit(out=kit_a, zip_path=zip_a, **kwargs)
    packager.build_kit(out=kit_b, zip_path=zip_b, **kwargs)

    manifest = packager.verify_kit(kit_a, expected_sha256=expected_sha256)
    assert manifest["source_commit"] == "0123456789abcdef"
    assert manifest["reference_bitstream_sha256"] == expected_sha256
    assert (kit_a / "tools/krn_hw_001.py").is_file()
    assert (kit_a / "tools/program_krn_hw_001_ulx3s.sh").is_file()
    assert (kit_a / "session/metadata.json").is_file()
    assert zip_a.read_bytes() == zip_b.read_bytes()


def test_verify_detects_tampering(tmp_path: Path) -> None:
    packager = _load_packager()
    bitstream = tmp_path / "reference.bit"
    bitstream.write_bytes(b"test-bitstream")
    expected_sha256 = hashlib.sha256(bitstream.read_bytes()).hexdigest()
    kit = tmp_path / "kit"
    packager.build_kit(
        bitstream,
        kit,
        source_commit="0123456789abcdef",
        workflow_run="test-run",
        expected_sha256=expected_sha256,
    )
    (kit / "README.md").write_text("tampered\n")

    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        packager.verify_kit(kit, expected_sha256=expected_sha256)
