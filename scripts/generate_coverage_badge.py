import coverage
import anybadge  # type: ignore
import os


def generate_coverage_badge():
    badge_svg = 'coverage_badge.svg'
    # Delete existing badge if it exists
    if os.path.exists(badge_svg):
        os.remove(badge_svg)

    cov = coverage.Coverage()
    cov.load()
    total_coverage = cov.report()

    # Define badge parameters
    badge = anybadge.Badge('coverage %', int(total_coverage), thresholds={50: 'red', 75: 'yellow', 90: 'green'})

    # Save the badge to a file
    badge.write_badge(badge_svg)


if __name__ == "__main__":
    generate_coverage_badge()
