import coverage
import anybadge  # type: ignore
import os
import toml  # type: ignore


def generate_coverage_badge():
    badge_svg = './images/coverage_badge.svg'
    if os.path.exists(badge_svg):
        os.remove(badge_svg)

    cov = coverage.Coverage()
    cov.load()
    total_coverage = cov.report()

    badge = anybadge.Badge('coverage %', int(total_coverage), thresholds={50: 'red', 75: 'yellow', 90: 'green'})
    badge.write_badge(badge_svg)


def generate_version_badge():
    badge_svg = './images/version_badge.svg'
    if os.path.exists(badge_svg):
        os.remove(badge_svg)

    with open('pyproject.toml', 'r') as f:
        pyproject_data = toml.load(f)
        version = pyproject_data['project']['version']

    badge = anybadge.Badge('version', version, default_color='blue')
    badge.write_badge(badge_svg)


if __name__ == "__main__":
    generate_coverage_badge()
    generate_version_badge()
