import argparse
from .compiler import generate_demo_artifacts


def main():
    parser = argparse.ArgumentParser(description="Generate the Kernellum Compiler v0.1 demo accelerator")
    parser.add_argument("--out", default="artifacts/digits_int8", help="artifact output directory")
    args = parser.parse_args()
    build = generate_demo_artifacts(args.out)
    print(f"generated {args.out}")
    print(f"float accuracy: {build.float_accuracy*100:.2f}%")
    print(f"INT8 accuracy: {build.int_accuracy*100:.2f}%")
    print(f"cycle model: exact on {len(build.y_test)} samples")
    print(f"architecture: {build.lanes} lanes, {build.cycles} cycles")


if __name__ == "__main__":
    main()
