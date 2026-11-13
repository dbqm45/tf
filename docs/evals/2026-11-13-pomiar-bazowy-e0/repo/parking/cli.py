"""Command line: python3 -m parking.cli <minutes>"""
import sys

from parking.fees import fee


def main(argv: list[str]) -> int:
    if len(argv) != 2 or not argv[1].isdigit():
        print("usage: python3 -m parking.cli <minutes>")
        return 2
    grosze = fee(int(argv[1]))
    print(f"{grosze // 100},{grosze % 100:02d} zł")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
