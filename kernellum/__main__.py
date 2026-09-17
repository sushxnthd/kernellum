import argparse
from pathlib import Path
from .compiler import generate_demo_artifacts


def _ensure_synthesizable_rtl(out_dir: str) -> None:
    """Apply a deterministic synthesis-safety fix to generated combinational RTL."""
    rtl_path = Path(out_dir) / "kernellum_mlp_accel.sv"
    text = rtl_path.read_text()
    needle = "    always_comb begin\n        mac_sum = 32'sd0;\n        case (state)"
    replacement = "    always_comb begin\n        mac_sum = 32'sd0;\n        lane = 0;\n        case (state)"
    if needle in text:
        rtl_path.write_text(text.replace(needle, replacement, 1))


def main():
    parser = argparse.ArgumentParser(description="Generate the Kernellum Compiler v0.1 demo accelerator")
    parser.add_argument("--out", default="artifacts/digits_int8", help="artifact output directory")
    args = parser.parse_args()
    build = generate_demo_artifacts(args.out)
    _ensure_synthesizable_rtl(args.out)
    print(f"generated {args.out}")
    print(f"float accuracy: {build.float_accuracy*100:.2f}%")
    print(f"INT8 accuracy: {build.int_accuracy*100:.2f}%")
    print(f"cycle model: exact on {len(build.y_test)} samples")
    print(f"architecture: {build.lanes} lanes, {build.cycles} cycles")


if __name__ == "__main__":
    main()
